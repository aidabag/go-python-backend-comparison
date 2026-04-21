from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# Определение строгих DTO (Data Transfer Objects) структур данных
# для передачи информации между слоями handler, service и storage.
# Обеспечение статической типизации за счет использования dataclasses.

@dataclass
class Product:
    """Модель товара магазина."""
    id: int
    name: str
    price: int
    stock: int

@dataclass
class OrderItem:
    """Модель позиции внутри заказа."""
    product_id: int
    quantity: int
    price_at_order: int

@dataclass
class Order:
    """Модель заказа.
    Включение массива позиций items при наличии соответствующего флага запроса."""
    id: int
    status: str
    created_at: datetime
    items: List[OrderItem]

@dataclass
class OrderSummary:
    """Структура детализированного отчета по заказу."""
    order_id: int
    status: str
    created_at: datetime
    items: List[OrderItem]
    total: int
    total_items: int
    total_positions: int

@dataclass
class OrderItemRequest:
    """Структура входящего запроса на добавление позиции в заказ."""
    product_id: int
    quantity: int

@dataclass
class CreateOrderRequest:
    """Структура входящего запроса на создание нового заказа."""
    items: List[OrderItemRequest]

@dataclass
class TopProduct:
    """Структура результатов аналитической выборки популярных товаров."""
    product_id: int
    total_quantity: int
