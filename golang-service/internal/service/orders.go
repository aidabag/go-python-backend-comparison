package service

import (
	"fmt"
	"golang-service/internal/storage"
	"time"
)

// Структура сервиса управления заказами
type OrderService struct {
	orderStorage   *storage.OrderStorage
	productStorage *storage.ProductStorage
	storage        *storage.Storage
	maxRetries     int
}

// Структура запроса на создание заказа
type CreateOrderRequest struct {
	Items []OrderItemRequest `json:"items"`
}

// Структура позиции в запросе создания заказа
type OrderItemRequest struct {
	ProductID int `json:"product_id"`
	Quantity  int `json:"quantity"`
}

// Инициализация сервисного слоя заказов
func NewOrderService(
	orderStorage *storage.OrderStorage,
	productStorage *storage.ProductStorage,
	storage *storage.Storage,
	maxRetries int,
) *OrderService {
	return &OrderService{
		orderStorage:   orderStorage,
		productStorage: productStorage,
		storage:        storage,
		maxRetries:     maxRetries,
	}
}

// Регистрация нового заказа с резервированием товаров
func (s *OrderService) CreateOrder(req *CreateOrderRequest) (*storage.Order, error) {
	// Валидация входного массива позиций
	if len(req.Items) == 0 {
		return nil, fmt.Errorf("order must have at least one item")
	}

	var order *storage.Order
	var err error

	// Исполнение операции в рамках общей транзакции с механизмом перезапуска
	err = storage.RetryTransaction(s.storage, s.maxRetries, func(tx *storage.Transaction) error {
		// Создание записи о заказе в базе данных
		order, err = tx.CreateOrder()
		if err != nil {
			return err
		}

		// Обработка каждой заявленной позиции заказа
		for _, item := range req.Items {
			// Проверка положительного количества товара
			if item.Quantity <= 0 {
				return fmt.Errorf("quantity must be positive")
			}

			// Наложение блокировки записи и извлечение текущих данных товара
			price, stock, err := tx.LockProduct(item.ProductID)
			if err != nil {
				return fmt.Errorf("product %d: %w", item.ProductID, err)
			}

			// Проверка достаточности складских остатков
			if stock < item.Quantity {
				return fmt.Errorf("insufficient stock for product %d: available %d, requested %d", 
					item.ProductID, stock, item.Quantity)
			}

			// Списание зарезервированного товара со склада
			if err := tx.UpdateStock(item.ProductID, -item.Quantity); err != nil {
				return err
			}

			// Сохранение связи товара и заказа
			if err := tx.AddOrderItem(order.ID, item.ProductID, item.Quantity, price); err != nil {
				return err
			}
		}

		return nil
	})

	if err != nil {
		return nil, err
	}

	// Выгрузка собранного заказа вместе с итоговыми позициями
	fullOrder, err := s.orderStorage.GetByID(order.ID, true)
	if err != nil {
		return nil, err
	}

	return fullOrder, nil
}

// Извлечение информации о заказе
func (s *OrderService) GetOrder(id int, includeItems bool) (*storage.Order, error) {
	return s.orderStorage.GetByID(id, includeItems)
}

// Формирование списка заказов с фильтрацией
func (s *OrderService) ListOrders(limit, offset int, status string, includeItems bool) ([]*storage.Order, error) {
	// Настройка нижней границы выборки
	if limit <= 0 {
		limit = 100
	}
	// Установка жесткого лимита выборки
	if limit > 1000 {
		limit = 1000
	}
	// Валидация смещения
	if offset < 0 {
		offset = 0
	}

	// Проверка корректности статуса
	if status != "" && status != "new" && status != "completed" {
		return nil, fmt.Errorf("invalid status: %s", status)
	}

	return s.orderStorage.List(limit, offset, status, includeItems)
}

// Добавление новой позиции в существующий заказ
func (s *OrderService) AddOrderItem(orderID, productID, quantity int) error {
	// Проверка количества добавляемого товара
	if quantity <= 0 {
		return fmt.Errorf("quantity must be positive")
	}

	// Загрузка заказа для проверки статуса
	order, err := s.orderStorage.GetByID(orderID, false)
	if err != nil {
		return err
	}
	// Блокировка модификации закрытых заказов
	if order.Status != "new" {
		return fmt.Errorf("can only modify orders with status 'new'")
	}

	// Инициализация транзакции обновления заказа
	err = storage.RetryTransaction(s.storage, s.maxRetries, func(tx *storage.Transaction) error {
		// Блокировка товарной позиции и чтение остатков
		price, stock, err := tx.LockProduct(productID)
		if err != nil {
			return fmt.Errorf("product %d: %w", productID, err)
		}

		// Проверка доступности необходимого объема товара
		if stock < quantity {
			return fmt.Errorf("insufficient stock for product %d: available %d, requested %d", 
				productID, stock, quantity)
		}

		// Списание товара со склада
		if err := tx.UpdateStock(productID, -quantity); err != nil {
			return err
		}

		// Фиксация позиции в заказе
		if err := tx.AddOrderItem(orderID, productID, quantity, price); err != nil {
			return err
		}

		return nil
	})

	return err
}

// Исключение позиции из состава заказа
func (s *OrderService) DeleteOrderItem(orderID, productID int) error {
	// Загрузка заказа для валидации статуса
	order, err := s.orderStorage.GetByID(orderID, false)
	if err != nil {
		return err
	}
	// Ограничение модификации закрытых заказов
	if order.Status != "new" {
		return fmt.Errorf("can only modify orders with status 'new'")
	}

	// Инициализация транзакции удаления позиции
	err = storage.RetryTransaction(s.storage, s.maxRetries, func(tx *storage.Transaction) error {
		// Удаление связи и освобождение зарезервированного количества
		quantity, err := tx.DeleteOrderItem(orderID, productID)
		if err != nil {
			return err
		}

		// Возврат позиции на склад
		if err := tx.UpdateStock(productID, quantity); err != nil {
			return err
		}

		return nil
	})

	return err
}

// Расчет суммарной стоимости заказа
func (s *OrderService) GetOrderTotal(orderID int) (int, error) {
	return s.orderStorage.GetTotal(orderID)
}

// Формирование детализированного отчета по заказу
func (s *OrderService) GetOrderSummary(orderID int) (*OrderSummary, error) {
	// Делегирование загрузки структуры заказа
	order, err := s.orderStorage.GetByID(orderID, true)
	if err != nil {
		return nil, err
	}

	// Вычисление итоговой суммы слоя хранения
	total, err := s.orderStorage.GetTotal(orderID)
	if err != nil {
		return nil, err
	}

	totalItems := 0
	// Подсчет общего количества физических единиц товара
	for _, item := range order.Items {
		totalItems += item.Quantity
	}

	// Возврат агрегированной сводки
	return &OrderSummary{
		OrderID:        orderID,
		Status:         order.Status,
		CreatedAt:      order.CreatedAt,
		Items:          order.Items,
		Total:          total,
		TotalItems:     totalItems,
		TotalPositions: len(order.Items),
	}, nil
}

// Структура сводного отчета по заказу
type OrderSummary struct {
	OrderID        int                 `json:"order_id"`
	Status         string              `json:"status"`
	CreatedAt      time.Time           `json:"created_at"`
	Items          []storage.OrderItem `json:"items"`
	Total          int                 `json:"total"`
	TotalItems     int                 `json:"total_items"`
	TotalPositions int                 `json:"total_positions"`
}

// Делегирование расчета среднего чека
func (s *OrderService) GetAverageOrderValue(since, until *time.Time) (float64, error) {
	return s.orderStorage.GetAverageOrderValue(since, until)
}

// Извлечение рейтинга наиболее популярных товаров
func (s *OrderService) GetTopProducts(limit int, since, until *time.Time) ([]storage.TopProduct, error) {
	// Валидация нижней границы списка
	if limit <= 0 {
		limit = 10
	}
	// Ограничение верхнего предела списка
	if limit > 100 {
		limit = 100
	}

	return s.orderStorage.GetTopProducts(limit, since, until)
}
