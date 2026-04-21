import dataclasses
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from internal.service.products import ProductService
from internal.handlers.helpers import write_error

# Структура обработчика маршрутов для товаров.

class ProductHandler:
    """Обертка контроллера для товаров."""

    @staticmethod
    async def create_product(request: Request) -> JSONResponse:
        """Обработка запроса на создание нового товара."""
        try:
            # Декодирование тела запроса
            body = await request.json()
        except Exception:
            return write_error(400, "validation_failed", "Invalid request body")

        name = body.get("name", "")
        price = body.get("price", 0)
        stock = body.get("stock", 0)

        try:
            # Делегирование создания товара слою сервиса
            product = await ProductService.create_product(name, price, stock)
        except Exception as e:
            err_msg = str(e)
            # Обработка конфликтов уникальности сущности
            if "duplicate" in err_msg or "unique" in err_msg:
                return write_error(409, "validation_failed", err_msg)
            return write_error(400, "validation_failed", err_msg)

        # Отправка ответа об успешной регистрации
        return JSONResponse(dataclasses.asdict(product), status_code=201)

    @staticmethod
    async def get_product(request: Request) -> JSONResponse:
        """Обработка запроса на получение данных товара."""
        try:
            # Извлечение идентификатора из пути запроса
            product_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid product ID")

        try:
            # Получение данных через слой бизнес-логики
            product = await ProductService.get_product(product_id)
        except Exception as e:
            err_msg = str(e)
            # Отработка случая отсутствия данных
            if "not found" in err_msg:
                return write_error(404, "not_found", "Product not found")
            return write_error(500, "internal_error", err_msg)

        # Сериализация и отправка результата клиенту
        return JSONResponse(dataclasses.asdict(product))

    @staticmethod
    async def list_products(request: Request) -> JSONResponse:
        """Извлечение списка товаров с учетом параметров URL."""
        limit = 100
        offset = 0

        # Чтение параметра лимита из GET-запроса
        limit_str = request.query_params.get("limit")
        if limit_str and limit_str.isdigit():
            limit = int(limit_str)

        # Чтение параметра смещения из GET-запроса
        offset_str = request.query_params.get("offset")
        if offset_str and offset_str.isdigit():
            offset = int(offset_str)

        # Чтение параметра сортировки
        sort = request.query_params.get("sort", "")

        try:
            # Запрос списка товаров к сервису
            products = await ProductService.list_products(limit, offset, sort)
        except Exception as e:
            return write_error(500, "internal_error", str(e))

        # Отправка сериализованного списка массивного ответа
        products_dict = [dataclasses.asdict(p) for p in products]
        return JSONResponse(products_dict)

    @staticmethod
    async def update_product(request: Request) -> JSONResponse:
        """Обработка запроса на частичное обновление данных товара (PATCH)."""
        try:
            # Извлечение целевого идентификатора товара из URL
            product_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid product ID")

        try:
            # Декодирование тела запроса JSON
            updates = await request.json()
        except Exception:
            return write_error(400, "validation_failed", "Invalid request body")

        try:
            # Делегирование процесса обновления слою сервисов
            await ProductService.update_product(product_id, updates)
        except Exception as e:
            err_msg = str(e)
            # Отработка ошибки отсутствующего товара
            if "not found" in err_msg:
                return write_error(404, "not_found", "Product not found")
            return write_error(400, "validation_failed", err_msg)

        try:
            # Получение актуального состояния модифицированного товара
            product = await ProductService.get_product(product_id)
        except Exception as e:
            return write_error(500, "internal_error", str(e))

        # Формирование и отправка успешного ответа
        return JSONResponse(dataclasses.asdict(product))

    @staticmethod
    async def delete_product(request: Request) -> Response:
        """Обработка директивы на удаление товара."""
        try:
            # Парсинг идентификатора из URL
            product_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid product ID")

        try:
            # Отправка команды удаления
            await ProductService.delete_product(product_id)
        except Exception as e:
            err_msg = str(e)
            # Валидация попытки удаления несуществующего товара
            if "not found" in err_msg:
                return write_error(404, "not_found", "Product not found")
            # Перехват запрета на удаление по внешнему ключу заказов
            if "used in orders" in err_msg:
                return write_error(409, "validation_failed", err_msg)
            return write_error(500, "internal_error", err_msg)

        # Отправка статуса 204 без тела сообщения
        return Response(status_code=204)
