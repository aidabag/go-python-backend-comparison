import asyncio
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from internal.config.config import AppConfig
import internal.storage.storage as storage
from internal.storage.storage import init_db, close_db
from internal.handlers.products import ProductHandler
from internal.handlers.orders import OrderHandler

from internal.metrics.metrics import registry, update_memory_metrics, MetricsMiddleware
from internal.middleware.middleware import LoggingMiddleware

# Настройка консольного журналирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def health_handler(request: Request) -> Response:
    """ Настройка конечных точек состояния с проверкой готовности БД. """
    if storage.DB_POOL is None:
        return JSONResponse({"status": "error", "message": "database pool not initialized"}, status_code=503)
    return JSONResponse({"status": "ok"})

async def metrics_handler(request: Request) -> Response:
    """Возврат HTTP обработчика модуля Prometheus."""
    data = generate_latest(registry)
    return Response(data, media_type=CONTENT_TYPE_LATEST)

async def lifespan(app: Starlette):
    """Обертка управления жизненным циклом приложения."""
    
    # Структурирование строки подключения к базе данных
    dsn = f"postgresql://{AppConfig.db_user}:{AppConfig.db_pass}@{AppConfig.db_host}:{AppConfig.db_port}/{AppConfig.db_name}"
    
    # Инициализация слоя подключения к базе данных
    await init_db(dsn, AppConfig.db_pool_max_conn)
    
    # Исполнение миграций схемы базы данных (создание таблиц)
    from internal.storage.storage import apply_migrations
    await apply_migrations()
    
    # Запуск фоновой корутины профилирования потребления памяти
    memory_task = asyncio.create_task(update_memory_metrics())
    
    yield
    
    # Отложенное закрытие пула соединений
    memory_task.cancel()
    await close_db()


# Настройка корневого маршрутизатора
routes = [
    Route("/health", health_handler, methods=["GET"]),
    Route(AppConfig.metrics_path, metrics_handler, methods=["GET"]),

    # Привязка маршрутов товаров
    Route("/products", ProductHandler.list_products, methods=["GET"]),
    Route("/products", ProductHandler.create_product, methods=["POST"]),
    Route("/products/{id:int}", ProductHandler.get_product, methods=["GET"]),
    Route("/products/{id:int}", ProductHandler.update_product, methods=["PUT", "PATCH"]),
    Route("/products/{id:int}", ProductHandler.delete_product, methods=["DELETE"]),

    # Привязка маршрутов заказов
    Route("/orders", OrderHandler.create_order, methods=["POST"]),
    Route("/orders", OrderHandler.list_orders, methods=["GET"]),
    Route("/orders/{id:int}", OrderHandler.get_order, methods=["GET"]),
    Route("/orders/{id:int}/items", OrderHandler.add_order_item, methods=["POST"]),
    Route("/orders/{id:int}/items/{product_id:int}", OrderHandler.delete_order_item, methods=["DELETE"]),
    Route("/orders/{id:int}/total", OrderHandler.get_order_total, methods=["GET"]),
    Route("/orders/{id:int}/summary", OrderHandler.get_order_summary, methods=["GET"]),

    # Интеграция аналитических эндпоинтов
    Route("/analytics/orders/average", OrderHandler.get_average_order_value, methods=["GET"]),
    Route("/analytics/products/top", OrderHandler.get_top_products, methods=["GET"]),
]

# Точка входа в приложение веб-сервера
app = Starlette(debug=False, routes=routes, lifespan=lifespan)

# Оборачивание обработчиков в промежуточное ПО (Middleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

# Запуск сетевого прослушивателя сервера
if __name__ == "__main__":
    addr = f":{AppConfig.service_port}"
    print(f"Server starting on {addr}")
    
    # Настройка Uvicorn как ASGI сервера
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(AppConfig.service_port), 
        workers=4,
        log_level="warning",
        access_log=False
    )
