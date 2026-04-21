import datetime
from typing import List, Dict, Any, Optional
import asyncpg

from internal.models.models import Order, OrderItem, TopProduct, OrderSummary
from internal.storage.orders import OrderStorage
from internal.storage.products import ProductStorage
from internal.storage.transaction import with_retry_transaction


# Реализация модуля бизнес-логики заказов.

class OrderService:
    """Обертка сервисного слоя для координации заказов и складских запасов."""

    @staticmethod
    async def create_order(items: List[Dict[str, int]]) -> Order:
        """Регистрация нового заказа с резервированием товаров."""
        # Валидация входного массива позиций
        if not items:
            raise ValueError("order must have at least one item")

        @with_retry_transaction
        async def _tx_create_order(conn: asyncpg.Connection) -> Order:
            # Создание записи о заказе в базе данных
            order = await OrderStorage.create(conn)
            
            # Обработка каждой заявленной позиции заказа
            for item in items:
                product_id = item.get("product_id", 0)
                quantity = item.get("quantity", 0)
                
                # Проверка положительного количества товара
                if quantity <= 0:
                    raise ValueError("quantity must be positive")
                    
                # Наложение блокировки записи и извлечение текущих данных товара
                price, stock = await ProductStorage.lock_product(conn, product_id)
                
                # Проверка достаточности складских остатков
                if stock < quantity:
                    raise ValueError(f"insufficient stock for product {product_id}: available {stock}, requested {quantity}")
                    
                # Списание зарезервированного товара со склада
                await ProductStorage.update_stock(conn, product_id, -quantity)
                
                # Сохранение связи товара и заказа
                await OrderStorage.add_item(conn, order.id, product_id, quantity, price)
                
            return order

        # Исполнение операции в рамках общей транзакции с механизмом перезапуска
        order = await _tx_create_order()
        
        # Выгрузка собранного заказа вместе с итоговыми позициями
        return await OrderStorage.get_by_id(order.id, True)

    @staticmethod
    async def get_order(order_id: int, include_items: bool) -> Order:
        """Извлечение информации о заказе."""
        return await OrderStorage.get_by_id(order_id, include_items)

    @staticmethod
    async def list_orders(limit: int, offset: int, status: str, include_items: bool) -> List[Order]:
        """Формирование списка заказов с фильтрацией."""
        # Настройка нижней границы выборки
        if limit <= 0:
            limit = 100
        # Установка жесткого лимита выборки
        if limit > 1000:
            limit = 1000
        # Валидация смещения
        if offset < 0:
            offset = 0

        # Проверка корректности статуса
        if status and status not in ("new", "completed"):
            raise ValueError(f"invalid status: {status}")

        return await OrderStorage.list_orders(limit, offset, status, include_items)

    @staticmethod
    async def add_order_item(order_id: int, product_id: int, quantity: int) -> None:
        """Добавление новой позиции в существующий заказ."""
        # Проверка количества добавляемого товара
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        # Загрузка заказа для проверки статуса
        order = await OrderStorage.get_by_id(order_id, False)
        # Блокировка модификации закрытых заказов
        if order.status != "new":
            raise ValueError("can only modify orders with status 'new'")

        @with_retry_transaction
        async def _tx_add_item(conn: asyncpg.Connection) -> None:
            # Блокировка товарной позиции и чтение остатков
            price, stock = await ProductStorage.lock_product(conn, product_id)

            # Проверка доступности необходимого объема товара
            if stock < quantity:
                raise ValueError(f"insufficient stock for product {product_id}: available {stock}, requested {quantity}")

            # Списание товара со склада
            await ProductStorage.update_stock(conn, product_id, -quantity)
            
            # Фиксация позиции в заказе
            await OrderStorage.add_item(conn, order_id, product_id, quantity, price)

        # Инициализация транзакции обновления заказа
        await _tx_add_item()

    @staticmethod
    async def delete_order_item(order_id: int, product_id: int) -> None:
        """Исключение позиции из состава заказа."""
        # Загрузка заказа для валидации статуса
        order = await OrderStorage.get_by_id(order_id, False)
        # Ограничение модификации закрытых заказов
        if order.status != "new":
            raise ValueError("can only modify orders with status 'new'")

        @with_retry_transaction
        async def _tx_delete_item(conn: asyncpg.Connection) -> None:
            # Удаление связи и освобождение зарезервированного количества
            quantity = await OrderStorage.delete_item(conn, order_id, product_id)

            # Возврат позиции на склад
            await ProductStorage.update_stock(conn, product_id, quantity)

        # Инициализация транзакции удаления позиции
        await _tx_delete_item()

    @staticmethod
    async def get_order_total(order_id: int) -> int:
        """Расчет суммарной стоимости заказа."""
        return await OrderStorage.get_total(order_id)

    @staticmethod
    async def get_order_summary(order_id: int) -> OrderSummary:
        """Формирование детализированного отчета по заказу."""
        # Делегирование загрузки структуры заказа
        order = await OrderStorage.get_by_id(order_id, True)

        # Вычисление итоговой суммы слоя хранения
        total = await OrderStorage.get_total(order_id)

        total_items = 0
        # Подсчет общего количества физических единиц товара
        for item in order.items:
            total_items += item.quantity

        # Возврат агрегированной сводки
        return OrderSummary(
            order_id=order_id,
            status=order.status,
            created_at=order.created_at,
            items=order.items,
            total=total,
            total_items=total_items,
            total_positions=len(order.items)
        )

    @staticmethod
    async def get_average_order_value(since: Optional[datetime.datetime], until: Optional[datetime.datetime]) -> float:
        """Делегирование расчета среднего чека."""
        return await OrderStorage.get_average_order_value(since, until)

    @staticmethod
    async def get_top_products(limit: int, since: Optional[datetime.datetime], until: Optional[datetime.datetime]) -> List[TopProduct]:
        """Извлечение рейтинга наиболее популярных товаров."""
        # Валидация нижней границы списка
        if limit <= 0:
            limit = 10
        # Ограничение верхнего предела списка
        if limit > 100:
            limit = 100

        return await OrderStorage.get_top_products(limit, since, until)
