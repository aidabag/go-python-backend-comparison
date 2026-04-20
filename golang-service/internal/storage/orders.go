package storage

import (
	"database/sql"
	"fmt"
	"time"
)

// Структура данных заказа
type Order struct {
	ID        int         `json:"id"`
	Status    string      `json:"status"`
	CreatedAt time.Time   `json:"created_at"`
	Items     []OrderItem `json:"items,omitempty"`
}

// Структура позиции заказа
type OrderItem struct {
	ProductID    int `json:"product_id"`
	Quantity     int `json:"quantity"`
	PriceAtOrder int `json:"price_at_order"`
}

// Обертка подключения к базе данных для управления заказами
type OrderStorage struct {
	db *sql.DB
}

// Инициализация слоя хранения для сущности заказов
func NewOrderStorage(db *sql.DB) *OrderStorage {
	return &OrderStorage{db: db}
}

// Создание новой записи о заказе
func (s *OrderStorage) Create() (*Order, error) {
	// Загрузка пути к SQL-файлу
	query, err := LoadSQLFile("insert_order.sql")
	if err != nil {
		return nil, fmt.Errorf("failed to load insert_order.sql: %w", err)
	}

	order := &Order{}
	// Исполнение SQL-команды генерации заказа
	err = s.db.QueryRow(query).Scan(&order.ID, &order.Status, &order.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to create order: %w", err)
	}
	return order, nil
}

// Извлечение информации о заказе по уникальному идентификатору
func (s *OrderStorage) GetByID(id int, includeItems bool) (*Order, error) {
	order := &Order{}
	// Подготовка SQL-запроса поиска
	query := `SELECT id, status, created_at FROM orders WHERE id = $1`
	// Исполнение запроса и чтение данных
	err := s.db.QueryRow(query, id).Scan(&order.ID, &order.Status, &order.CreatedAt)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("order not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get order: %w", err)
	}

	// Подгрузка связанных позиций заказа
	if includeItems {
		items, err := s.getOrderItems(id)
		if err != nil {
			return nil, err
		}
		order.Items = items
	}

	return order, nil
}

// Выгрузка списка заказов с учетом пагинации и фильтрации
func (s *OrderStorage) List(limit, offset int, status string, includeItems bool) ([]*Order, error) {
	// Подготовка базового SQL-запроса
	query := `SELECT id, status, created_at FROM orders`
	args := []interface{}{}
	argNum := 1

	// Динамическое добавление условия фильтрации по статусу
	if status != "" {
		query += fmt.Sprintf(" WHERE status = $%d", argNum)
		args = append(args, status)
		argNum++
	}

	// Применение сортировки и лимитов
	query += fmt.Sprintf(" ORDER BY id DESC LIMIT $%d OFFSET $%d", argNum, argNum+1)
	args = append(args, limit, offset)

	// Выполнение сформированного запроса
	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list orders: %w", err)
	}
	// Делегирование закрытия курсора
	defer rows.Close()

	var orders []*Order
	// Построчное сканирование результатов выборки
	for rows.Next() {
		order := &Order{}
		if err := rows.Scan(&order.ID, &order.Status, &order.CreatedAt); err != nil {
			return nil, fmt.Errorf("failed to scan order: %w", err)
		}

		// Догрузка позиций заказа при наличии флага
		if includeItems {
			items, err := s.getOrderItems(order.ID)
			if err != nil {
				return nil, err
			}
			order.Items = items
		}

		orders = append(orders, order)
	}

	return orders, nil
}

// Извлечение товарных позиций для отдельного заказа
func (s *OrderStorage) getOrderItems(orderID int) ([]OrderItem, error) {
	// Подготовка текста запроса списка позиций
	query := `SELECT product_id, quantity, price_at_order FROM order_items WHERE order_id = $1`
	// Исполнение запроса
	rows, err := s.db.Query(query, orderID)
	if err != nil {
		return nil, fmt.Errorf("failed to get order items: %w", err)
	}
	// Завершение работы курсора
	defer rows.Close()

	var items []OrderItem
	// Итеративное чтение строк результата
	for rows.Next() {
		item := OrderItem{}
		if err := rows.Scan(&item.ProductID, &item.Quantity, &item.PriceAtOrder); err != nil {
			return nil, fmt.Errorf("failed to scan order item: %w", err)
		}
		items = append(items, item)
	}

	return items, nil
}

// Запись новой позиции в заказ
func (s *OrderStorage) AddItem(orderID, productID, quantity, priceAtOrder int) error {
	// Чтение SQL-файла с диска
	query, err := LoadSQLFile("insert_order_item.sql")
	if err != nil {
		return fmt.Errorf("failed to load insert_order_item.sql: %w", err)
	}

	// Исполнение команды добавления
	_, err = s.db.Exec(query, orderID, productID, quantity, priceAtOrder)
	if err != nil {
		return fmt.Errorf("failed to add order item: %w", err)
	}
	return nil
}

// Удаление позиции из заказа
func (s *OrderStorage) DeleteItem(orderID, productID int) (int, error) {
	// Чтение команды удаления из файла
	query, err := LoadSQLFile("delete_order_item.sql")
	if err != nil {
		return 0, fmt.Errorf("failed to load delete_order_item.sql: %w", err)
	}

	var quantity int
	// Выполнение запроса и извлечение количества возвращаемого товара
	err = s.db.QueryRow(query, orderID, productID).Scan(&quantity)
	if err == sql.ErrNoRows {
		return 0, fmt.Errorf("order item not found")
	}
	if err != nil {
		return 0, fmt.Errorf("failed to delete order item: %w", err)
	}

	return quantity, nil
}

// Подсчет общей стоимости заказа
func (s *OrderStorage) GetTotal(orderID int) (int, error) {
	// Конструирование агрегационного SQL-запроса
	query := `SELECT COALESCE(SUM(quantity * price_at_order), 0) FROM order_items WHERE order_id = $1`
	var total int
	// Исполнение запроса агрегации
	err := s.db.QueryRow(query, orderID).Scan(&total)
	if err != nil {
		return 0, fmt.Errorf("failed to get order total: %w", err)
	}
	return total, nil
}

// Вычисление средней стоимости заказа за промежуток времени
func (s *OrderStorage) GetAverageOrderValue(since, until *time.Time) (float64, error) {
	// Подготовка комплексного агрегирующего запроса
	query := `SELECT COALESCE(AVG(total), 0) FROM (
		SELECT order_id, SUM(quantity * price_at_order) as total
		FROM order_items
		WHERE order_id IN (SELECT id FROM orders WHERE created_at >= $1 AND created_at <= $2)
		GROUP BY order_id
	) subquery`

	args := []interface{}{}
	// Установка начального времени расчетного периода
	if since == nil {
		args = append(args, time.Time{})
	} else {
		args = append(args, *since)
	}
	// Установка конечного времени расчетного периода
	if until == nil {
		args = append(args, time.Now())
	} else {
		args = append(args, *until)
	}

	var avg float64
	// Совершение выборки среднего значения
	err := s.db.QueryRow(query, args...).Scan(&avg)
	if err != nil {
		return 0, fmt.Errorf("failed to get average order value: %w", err)
	}
	return avg, nil
}

// Составление списка самых продаваемых товаров
func (s *OrderStorage) GetTopProducts(limit int, since, until *time.Time) ([]TopProduct, error) {
	// Конструирование запроса группировки и сортировки по количеству проданных единиц
	query := `SELECT product_id, SUM(quantity) as total_quantity
		FROM order_items
		WHERE order_id IN (
			SELECT id FROM orders 
			WHERE created_at >= $1 AND created_at <= $2
		)
		GROUP BY product_id
		ORDER BY total_quantity DESC
		LIMIT $3`

	args := []interface{}{}
	// Установка начальной отсечки временного диапазона
	if since == nil {
		args = append(args, time.Time{})
	} else {
		args = append(args, *since)
	}
	// Установка конечной отсечки временного диапазона
	if until == nil {
		args = append(args, time.Now())
	} else {
		args = append(args, *until)
	}
	// Добавление ограничения размера выборки
	args = append(args, limit)

	// Исполнение запроса топ-списка
	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to get top products: %w", err)
	}
	// Гарантия закрытия строк ответа
	defer rows.Close()

	var topProducts []TopProduct
	// Построчное сканирование результатов статистики
	for rows.Next() {
		var tp TopProduct
		if err := rows.Scan(&tp.ProductID, &tp.TotalQuantity); err != nil {
			return nil, fmt.Errorf("failed to scan top product: %w", err)
		}
		topProducts = append(topProducts, tp)
	}

	return topProducts, nil
}

// Структура аналитических данных по популярному товару
type TopProduct struct {
	ProductID    int `json:"product_id"`
	TotalQuantity int `json:"total_quantity"`
}
