import asyncpg
from typing import List, Dict, Any, Tuple
from internal.models.models import Product
import internal.storage.storage as storage
from internal.storage.storage import load_sql_file

# Инициализация слоя хранения для сущности товаров

class ProductStorage:
    """Обертка асинхронного подключения к базе данных для управления товарами."""

    @staticmethod
    async def create(product: Product) -> None:
        """Запись нового товара в базу данных."""
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        # Подготовка текста SQL-запроса вставки
        query = "INSERT INTO products (name, price, stock) VALUES ($1, $2, $3) RETURNING id"
        async with storage.DB_POOL.acquire() as conn:
            try:
                # Выполнение инструкции и сканирование сгенерированного идентификатора
                product.id = await conn.fetchval(query, product.name, product.price, product.stock)
            except Exception as e:
                raise Exception(f"failed to create product: {e}")

    @staticmethod
    async def get_by_id(product_id: int) -> Product:
        """Извлечение данных товара по уникальному идентификатору."""
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        # Инициализация текста запроса поиска
        query = "SELECT id, name, price, stock FROM products WHERE id = $1"
        async with storage.DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса и извлечение полей
                row = await conn.fetchrow(query, product_id)
            except Exception as e:
                raise Exception(f"failed to get product: {e}")
                
            if row is None:
                raise Exception("product not found")
                
            return Product(
                id=row["id"],
                name=row["name"],
                price=row["price"],
                stock=row["stock"]
            )

    @staticmethod
    async def list_products(limit: int, offset: int, sort: str) -> List[Product]:
        """Получение списка товаров с применением пагинации и сортировки."""
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        # Установка сортировки по умолчанию (новые записи в начале)
        order_by = "id DESC"
        
        # Безопасное сопоставление строкового параметра с SQL-выражением ORDER BY
        if sort in ("", "id_desc"):
            order_by = "id DESC"
        elif sort in ("id", "id_asc"):
            order_by = "id ASC"
        elif sort == "name":
            order_by = "name ASC"
        elif sort == "price":
            order_by = "price ASC"
        else:
            # Выбор значения по умолчанию при получении неизвестного параметра сортировки
            order_by = "id DESC"
            
        # Формирование итогового SQL-запроса
        query = f"SELECT id, name, price, stock FROM products ORDER BY {order_by} LIMIT $1 OFFSET $2"
        products = []
        
        async with storage.DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса выборки
                rows = await conn.fetch(query, limit, offset)
            except Exception as e:
                raise Exception(f"failed to list products: {e}")
                
            # Построчное чтение результатов выборки
            for row in rows:
                products.append(Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"],
                    stock=row["stock"]
                ))
                
        return products

    @staticmethod
    async def update(product_id: int, updates: Dict[str, Any]) -> None:
        """Частичное обновление данных товара (PATCH операция)."""
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        # Проверка наличия полей для обновления
        if not updates:
            return
            
        set_parts = []
        args = []
        arg_num = 1
        
        # Формирование пар ключ-значение для SQL-инструкции SET
        for key, value in updates.items():
            set_parts.append(f"{key} = ${arg_num}")
            args.append(value)
            arg_num += 1
            
        # Добавление идентификатора товара в конец списка аргументов
        args.append(product_id)
        
        # Динамическая склейка SQL-запроса изменения
        query = f"UPDATE products SET {', '.join(set_parts)} WHERE id = ${arg_num}"
        
        async with storage.DB_POOL.acquire() as conn:
            try:
                # Исполнение инструкции обновления
                await conn.execute(query, *args)
            except Exception as e:
                raise Exception(f"failed to update product: {e}")

    @staticmethod
    async def delete(product_id: int) -> None:
        """Удаление товара из базы данных."""
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        # Проверка использования товара в оформленных заказах
        check_query = "SELECT COUNT(*) FROM order_items WHERE product_id = $1"
        
        async with storage.DB_POOL.acquire() as conn:
            try:
                # Исполнение запроса подсчета связанных записей
                count = await conn.fetchval(check_query, product_id)
            except Exception as e:
                raise Exception(f"failed to check product usage: {e}")
                
            if count > 0:
                raise Exception("product is used in orders and cannot be deleted")
                
            # Подготовка SQL-команды удаления
            delete_query = "DELETE FROM products WHERE id = $1"
            try:
                # Исполнение инструкции
                await conn.execute(delete_query, product_id)
            except Exception as e:
                raise Exception(f"failed to delete product: {e}")

    @staticmethod
    async def lock_product(conn: asyncpg.Connection, product_id: int) -> Tuple[int, int]:
        """Наложение блокировки строк на товар для предотвращения состояний гонки."""
        # Чтение SQL-запроса из файловой системы монорепозитория
        try:
            query = load_sql_file("lock_product.sql")
        except Exception as e:
            raise Exception(f"failed to load lock_product.sql: {e}")
            
        try:
            # Выполнение запроса и извлечение данных
            row = await conn.fetchrow(query, product_id)
        except Exception as e:
            raise Exception(f"failed to lock product: {e}")
            
        if row is None:
            raise Exception("product not found")
            
        return row["price"], row["stock"]

    @staticmethod
    async def update_stock(conn: asyncpg.Connection, product_id: int, delta: int) -> None:
        """Обновление складских остатков товара."""
        # Подготовка команды обновления запасов
        query = "UPDATE products SET stock = stock + $1 WHERE id = $2"
        
        try:
            # Исполнение команды
            await conn.execute(query, delta, product_id)
        except Exception as e:
            raise Exception(f"failed to update stock: {e}")
