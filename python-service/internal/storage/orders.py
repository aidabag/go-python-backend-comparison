import datetime
from typing import List, Optional
import asyncpg

from internal.models.models import Order, OrderItem, TopProduct
from internal.storage.storage import DB_POOL, load_sql_file

# Инициализация слоя хранения для сущности заказов

class OrderStorage:
    """Обертка подключения к базе данных для управления заказами."""

    @staticmethod
    async def create(conn: asyncpg.Connection) -> Order:
        """Создание новой записи о заказе."""
        try:
            query = load_sql_file("insert_order.sql")
        except Exception as e:
            raise Exception(f"failed to load insert_order.sql: {e}")

        try:
            # Исполнение SQL-команды генерации заказа
            row = await conn.fetchrow(query)
            if not row:
                raise Exception("no data returned from insert_order.sql")
                
            return Order(
                id=row["id"],
                status=row["status"],
                created_at=row["created_at"],
                items=[]
            )
        except Exception as e:
            raise Exception(f"failed to create order: {e}")

    @staticmethod
    async def get_by_id(order_id: int, include_items: bool) -> Order:
        """Извлечение информации о заказе по уникальному идентификатору."""
        if DB_POOL is None:
            raise RuntimeError("database pool not initialized")

        query = "SELECT id, status, created_at FROM orders WHERE id = $1"
        
        async with DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса и чтение данных
                row = await conn.fetchrow(query, order_id)
            except Exception as e:
                raise Exception(f"failed to get order: {e}")

            if row is None:
                raise Exception("order not found")

            order = Order(
                id=row["id"],
                status=row["status"],
                created_at=row["created_at"],
                items=[]
            )

            # Подгрузка связанных позиций заказа
            if include_items:
                order.items = await OrderStorage._get_order_items(conn, order_id)

            return order

    @staticmethod
    async def list_orders(limit: int, offset: int, status: str, include_items: bool) -> List[Order]:
        """Выгрузка списка заказов с учетом пагинации и фильтрации."""
        if DB_POOL is None:
            raise RuntimeError("database pool not initialized")

        query = "SELECT id, status, created_at FROM orders"
        args = []
        arg_num = 1

        # Динамическое добавление условия фильтрации по статусу
        if status:
            query += f" WHERE status = ${arg_num}"
            args.append(status)
            arg_num += 1

        # Применение сортировки и лимитов
        query += f" ORDER BY id DESC LIMIT ${arg_num} OFFSET ${arg_num + 1}"
        args.extend([limit, offset])

        orders = []

        async with DB_POOL.acquire() as conn:
            try:
                # Выполнение сформированного запроса
                rows = await conn.fetch(query, *args)
            except Exception as e:
                raise Exception(f"failed to list orders: {e}")

            # Построчное сканирование результатов выборки
            for row in rows:
                order = Order(
                    id=row["id"],
                    status=row["status"],
                    created_at=row["created_at"],
                    items=[]
                )

                # Догрузка позиций заказа при наличии флага
                if include_items:
                    order.items = await OrderStorage._get_order_items(conn, order.id)

                orders.append(order)

        return orders

    @staticmethod
    async def _get_order_items(conn: asyncpg.Connection, order_id: int) -> List[OrderItem]:
        """Извлечение товарных позиций для отдельного заказа."""
        query = "SELECT product_id, quantity, price_at_order FROM order_items WHERE order_id = $1"
        
        try:
            # Исполнение запроса
            rows = await conn.fetch(query, order_id)
        except Exception as e:
            raise Exception(f"failed to get order items: {e}")

        items = []
        # Итеративное чтение строк результата
        for row in rows:
            items.append(OrderItem(
                product_id=row["product_id"],
                quantity=row["quantity"],
                price_at_order=row["price_at_order"]
            ))

        return items

    @staticmethod
    async def add_item(conn: asyncpg.Connection, order_id: int, product_id: int, quantity: int, price_at_order: int) -> None:
        """Запись новой позиции в заказ."""
        try:
            # Чтение SQL-файла с диска
            query = load_sql_file("insert_order_item.sql")
        except Exception as e:
            raise Exception(f"failed to load insert_order_item.sql: {e}")

        try:
            # Исполнение команды добавления
            await conn.execute(query, order_id, product_id, quantity, price_at_order)
        except Exception as e:
            raise Exception(f"failed to add order item: {e}")

    @staticmethod
    async def delete_item(conn: asyncpg.Connection, order_id: int, product_id: int) -> int:
        """Удаление позиции из заказа."""
        try:
            # Чтение команды удаления из файла
            query = load_sql_file("delete_order_item.sql")
        except Exception as e:
            raise Exception(f"failed to load delete_order_item.sql: {e}")

        try:
            # Выполнение запроса и извлечение количества возвращаемого товара
            row = await conn.fetchrow(query, order_id, product_id)
        except Exception as e:
            raise Exception(f"failed to delete order item: {e}")

        if not row:
            raise Exception("order item not found")

        return row["quantity"]

    @staticmethod
    async def get_total(order_id: int) -> int:
        """Подсчет общей стоимости заказа."""
        if DB_POOL is None:
            raise RuntimeError("database pool not initialized")

        query = "SELECT COALESCE(SUM(quantity * price_at_order), 0) FROM order_items WHERE order_id = $1"
        
        async with DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса агрегации
                total_val = await conn.fetchval(query, order_id)
                return int(total_val) if total_val is not None else 0
            except Exception as e:
                raise Exception(f"failed to get order total: {e}")

    @staticmethod
    async def get_average_order_value(since: Optional[datetime.datetime], until: Optional[datetime.datetime]) -> float:
        """Вычисление средней стоимости заказа за промежуток времени."""
        if DB_POOL is None:
            raise RuntimeError("database pool not initialized")

        query = '''
            SELECT COALESCE(AVG(total), 0) FROM (
                SELECT order_id, SUM(quantity * price_at_order) as total
                FROM order_items
                WHERE order_id IN (SELECT id FROM orders WHERE created_at >= $1 AND created_at <= $2)
                GROUP BY order_id
            ) subquery
        '''

        # Установка начального времени расчетного периода
        start_time = since if since is not None else datetime.datetime.min
        # Установка конечного времени расчетного периода
        end_time = until if until is not None else datetime.datetime.now()

        async with DB_POOL.acquire() as conn:
            try:
                # Совершение выборки среднего значения
                avg = await conn.fetchval(query, start_time, end_time)
                return float(avg) if avg is not None else 0.0
            except Exception as e:
                raise Exception(f"failed to get average order value: {e}")

    @staticmethod
    async def get_top_products(limit: int, since: Optional[datetime.datetime], until: Optional[datetime.datetime]) -> List[TopProduct]:
        """Составление списка самых продаваемых товаров."""
        if DB_POOL is None:
            raise RuntimeError("database pool not initialized")

        query = '''
            SELECT product_id, SUM(quantity) as total_quantity
            FROM order_items
            WHERE order_id IN (
                SELECT id FROM orders 
                WHERE created_at >= $1 AND created_at <= $2
            )
            GROUP BY product_id
            ORDER BY total_quantity DESC
            LIMIT $3
        '''

        start_time = since if since is not None else datetime.datetime.min
        end_time = until if until is not None else datetime.datetime.now()

        async with DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса топ-списка
                rows = await conn.fetch(query, start_time, end_time, limit)
            except Exception as e:
                raise Exception(f"failed to get top products: {e}")

            top_products = []
            # Построчное сканирование результатов статистики
            for row in rows:
                top_products.append(TopProduct(
                    product_id=row["product_id"],
                    total_quantity=row["total_quantity"]
                ))
            
            return top_products
