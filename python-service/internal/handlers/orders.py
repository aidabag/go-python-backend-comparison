import datetime
import dataclasses
from typing import Any
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from internal.service.orders import OrderService
from internal.handlers.helpers import write_error

# Подготовка структуры ответа с поддержкой форматирования дат.
def _serialize_response(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _serialize_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_response(v) for v in data]
    elif isinstance(data, datetime.datetime):
        # Преобразование метки времени в формат RFC3339
        return data.isoformat().replace("+00:00", "Z")
    elif isinstance(data, float) and data.is_integer():
        return int(data)
    elif dataclasses.is_dataclass(data):
        return _serialize_response(dataclasses.asdict(data))
    return data

# Структура обработчика маршрутов для заказов.

class OrderHandler:
    """Обертка контроллера для работы с заказами."""

    @staticmethod
    async def create_order(request: Request) -> JSONResponse:
        """Обработка запроса на формирование нового заказа."""
        try:
            # Декодирование JSON-структуры запроса
            body = await request.json()
        except Exception:
            return write_error(400, "validation_failed", "Invalid request body")

        items = body.get("items", [])

        try:
            # Делегирование процессинга создания
            order = await OrderService.create_order(items)
        except Exception as e:
            err_msg = str(e)
            # Идентификация ошибки нехватки товаров
            if "insufficient stock" in err_msg:
                return write_error(409, "insufficient_stock", err_msg)
            return write_error(400, "validation_failed", err_msg)

        # Отправка кода успешного создания и тела документа
        return JSONResponse(_serialize_response(order), status_code=201)

    @staticmethod
    async def get_order(request: Request) -> JSONResponse:
        """Обработка запроса на извлечение сведений о заказе."""
        try:
            # Парсинг идентификатора из URL-пути
            order_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid order ID")

        try:
            # Делегирование операции чтения заказа
            order = await OrderService.get_order(order_id, True)
        except Exception as e:
            err_msg = str(e)
            # Отработка ошибки отсутствующей сущности
            if "not found" in err_msg:
                return write_error(404, "not_found", "Order not found")
            return write_error(500, "internal_error", err_msg)

        # Сериализация и отправка результата клиенту
        return JSONResponse(_serialize_response(order))

    @staticmethod
    async def list_orders(request: Request) -> JSONResponse:
        """Обработка директивы на получение списка заказов."""
        limit = 100
        offset = 0

        # Извлечение параметров фильтрации
        status = request.query_params.get("status", "")
        include_items = request.query_params.get("include_items") == "true"

        limit_str = request.query_params.get("limit")
        if limit_str and limit_str.isdigit():
            limit = int(limit_str)

        offset_str = request.query_params.get("offset")
        if offset_str and offset_str.isdigit():
            offset = int(offset_str)

        try:
            # Запрос агрегированной коллекции у сервиса
            orders = await OrderService.list_orders(limit, offset, status, include_items)
        except Exception as e:
            return write_error(400, "validation_failed", str(e))

        # Выгрузка массива клиенту
        return JSONResponse(_serialize_response(orders))

    @staticmethod
    async def add_order_item(request: Request) -> JSONResponse:
        """Управление интеграцией дополнительной позиции в спецификацию заказа."""
        try:
            order_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid order ID")

        try:
            # Декодирование тела запроса
            body = await request.json()
        except Exception:
            return write_error(400, "validation_failed", "Invalid request body")

        product_id = body.get("product_id", 0)
        quantity = body.get("quantity", 0)

        try:
            # Инициализация процедуры добавления позиции
            await OrderService.add_order_item(order_id, product_id, quantity)
        except Exception as e:
            err_msg = str(e)
            # Анализ возможных путей возникновения ошибок бизнес-логики
            if "not found" in err_msg:
                return write_error(404, "not_found", err_msg)
            if "insufficient stock" in err_msg:
                return write_error(409, "insufficient_stock", err_msg)
            if "can only modify" in err_msg:
                return write_error(409, "validation_failed", err_msg)
            return write_error(400, "validation_failed", err_msg)

        try:
            # Загрузка обновленного состояния заказа
            order = await OrderService.get_order(order_id, True)
        except Exception as e:
            return write_error(500, "internal_error", str(e))

        # Отправка сериализованного представления
        return JSONResponse(_serialize_response(order))

    @staticmethod
    async def delete_order_item(request: Request) -> Response:
        """Контроль процесса удаления позиции из закрытого заказа."""
        try:
            order_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid order ID")

        try:
            product_id = int(request.path_params["product_id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid product ID")

        try:
            # Делегирование запуска функции удаления
            await OrderService.delete_order_item(order_id, product_id)
        except Exception as e:
            err_msg = str(e)
            if "not found" in err_msg:
                return write_error(404, "not_found", err_msg)
            if "can only modify" in err_msg:
                return write_error(409, "validation_failed", err_msg)
            return write_error(400, "validation_failed", err_msg)

        # Отправка ответа об успешном удалении
        return Response(status_code=204)

    @staticmethod
    async def get_order_total(request: Request) -> JSONResponse:
        """Запрос суммарной стоимости заказа."""
        try:
            order_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid order ID")

        try:
            # Передача вычислений сервисному слою
            total = await OrderService.get_order_total(order_id)
        except Exception as e:
            err_msg = str(e)
            if "not found" in err_msg:
                return write_error(404, "not_found", "Order not found")
            return write_error(500, "internal_error", err_msg)

        response = {
            "order_id": order_id,
            "total": total
        }

        return JSONResponse(response)

    @staticmethod
    async def get_order_summary(request: Request) -> JSONResponse:
        """Обработка вызова агрегированной статистики по заказу."""
        try:
            order_id = int(request.path_params["id"])
        except (KeyError, ValueError):
            return write_error(400, "validation_failed", "Invalid order ID")

        try:
            # Извлечение агрегированного итога
            summary = await OrderService.get_order_summary(order_id)
        except Exception as e:
            err_msg = str(e)
            if "not found" in err_msg:
                return write_error(404, "not_found", "Order not found")
            return write_error(500, "internal_error", err_msg)

        return JSONResponse(_serialize_response(summary))

    @staticmethod
    async def get_average_order_value(request: Request) -> JSONResponse:
        """Аналитический запрос показателей среднего чека."""
        since_str = request.query_params.get("since")
        until_str = request.query_params.get("until")

        since = None
        until = None

        # Разбор параметров временного интервала
        try:
            if since_str:
                since = datetime.datetime.fromisoformat(since_str.replace("Z", "+00:00"))
            if until_str:
                until = datetime.datetime.fromisoformat(until_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        try:
            # Делегирование аналитического расчета
            avg = await OrderService.get_average_order_value(since, until)
        except Exception as e:
            return write_error(500, "internal_error", str(e))

        response = {"average": avg}

        return JSONResponse(response)

    @staticmethod
    async def get_top_products(request: Request) -> JSONResponse:
        """Аналитический запрос рейтинга популярных товаров."""
        limit = 10
        limit_str = request.query_params.get("limit")
        if limit_str and limit_str.isdigit():
            limit = int(limit_str)

        since_str = request.query_params.get("since")
        until_str = request.query_params.get("until")

        since = None
        until = None

        try:
            if since_str:
                since = datetime.datetime.fromisoformat(since_str.replace("Z", "+00:00"))
            if until_str:
                until = datetime.datetime.fromisoformat(until_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        try:
            # Делегирование математической группировки
            top_products = await OrderService.get_top_products(limit, since, until)
        except Exception as e:
            return write_error(500, "internal_error", str(e))

        return JSONResponse(_serialize_response(top_products))
