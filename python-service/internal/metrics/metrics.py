import os
import psutil
import asyncio
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Нативная реестровая запись для Prometheus
registry = CollectorRegistry()

# Объявление метрик HTTP запросов
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    registry=registry
)

# Объявление метрик аппаратных ресурсов
app_memory_bytes = Gauge(
    "app_memory_bytes",
    "Application memory usage in bytes",
    registry=registry
)

app_cpu_seconds_total = Counter(
    "app_cpu_seconds_total",
    "Total CPU time used by the application (placeholder)",
    registry=registry
)

# Метрики ожидания транзакций
db_lock_wait_seconds_total = Counter(
    "db_lock_wait_seconds_total",
    "Total time spent waiting for database locks",
    registry=registry
)

def record_db_lock_wait(duration_seconds: float) -> None:
    """Регистрация времени ожидания блокировок СУБД."""
    db_lock_wait_seconds_total.inc(duration_seconds)

async def update_memory_metrics() -> None:
    """Забор статистики потребления оперативной памяти."""
    process = psutil.Process(os.getpid())
    while True:
        try:
            # Чтение состояния распределения памяти
            app_memory_bytes.set(process.memory_info().rss)
        except Exception:
            pass
        await asyncio.sleep(5)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Интеграция промежуточного слоя сбора HTTP-статистики."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        endpoint = request.url.path

        try:
            # Делегирование запроса слоям бизнес-логики
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            
            # Увеличение счетчика входящих запросов
            http_requests_total.labels(
                method=request.method, 
                endpoint=endpoint, 
                status=str(status_code)
            ).inc()
            
            # Наблюдение за задержками времени ответа
            http_request_duration.labels(endpoint=endpoint).observe(duration)
            
        return response
