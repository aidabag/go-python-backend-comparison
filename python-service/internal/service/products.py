from typing import List, Dict, Any
from internal.models.models import Product
from internal.storage.products import ProductStorage

# Реализация модуля бизнес-логики товаров.

class ProductService:
    """Обертка сервисного слоя для обработки бизнес-правил товаров."""

    @staticmethod
    async def create_product(name: str, price: int, stock: int) -> Product:
        """Регистрация нового товара с проверкой входных параметров."""
        if not name:
            raise ValueError("name is required")
        if price < 0:
            raise ValueError("price must be non-negative")
        if stock < 0:
            raise ValueError("stock must be non-negative")

        product = Product(
            id=0,
            name=name,
            price=price,
            stock=stock
        )

        # Передача записи в слой хранения
        await ProductStorage.create(product)
        return product

    @staticmethod
    async def get_product(product_id: int) -> Product:
        """Извлечение данных товара по уникальному идентификатору."""
        # Делегирование запроса слою базы данных
        return await ProductStorage.get_by_id(product_id)

    @staticmethod
    async def list_products(limit: int, offset: int, sort: str) -> List[Product]:
        """Составление списка товаров с применением границ пагинации."""
        # Валидация нижней границы размера выборки
        if limit <= 0:
            limit = 100
        # Валидация верхней границы размера выборки
        if limit > 1000:
            limit = 1000
        # Валидация смещения
        if offset < 0:
            offset = 0

        # Исполнение запроса выборки
        return await ProductStorage.list_products(limit, offset, sort)

    @staticmethod
    async def update_product(product_id: int, updates: Dict[str, Any]) -> None:
        """Безопасное обновление значений полей товара."""
        # Инициализация фильтра разрешенных ключей
        allowed_fields = {"name", "price", "stock"}
        validated_updates = {}

        # Цикл валидации входящих параметров
        for key, value in updates.items():
            # Игнорирование недопустимых полей
            if key not in allowed_fields:
                continue

            # Приведение типов и логическая проверка значений
            if key == "price":
                if isinstance(value, (int, float)):
                    price_val = int(value)
                    if price_val < 0:
                        raise ValueError("price must be non-negative")
                    validated_updates[key] = price_val
            elif key == "stock":
                if isinstance(value, (int, float)):
                    stock_val = int(value)
                    if stock_val < 0:
                        raise ValueError("stock must be non-negative")
                    validated_updates[key] = stock_val
            elif key == "name":
                if isinstance(value, str):
                    validated_updates[key] = value

        # Прерывание операции при отсутствии корректных данных
        if not validated_updates:
            return

        # Делегирование операции слою хранения
        await ProductStorage.update(product_id, validated_updates)

    @staticmethod
    async def delete_product(product_id: int) -> None:
        """Удаление товара из каталога базы данных."""
        # Отправка команды физического удаления
        await ProductStorage.delete(product_id)
