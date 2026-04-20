package storage

import (
	"database/sql"
	"fmt"
	"math/rand"
	"strings"
	"time"
)

// Структура транзакции базы данных
type Transaction struct {
	tx *sql.Tx
}

// Запуск новой транзакции базы данных
func (s *Storage) Begin() (*Transaction, error) {
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	return &Transaction{tx: tx}, nil
}

// Фиксация изменений транзакции
func (t *Transaction) Commit() error {
	return t.tx.Commit()
}

// Откат изменений транзакции при ошибке
func (t *Transaction) Rollback() error {
	return t.tx.Rollback()
}

// Наложение блокировки строк на товар для предотвращения состояний гонки
func (t *Transaction) LockProduct(id int) (price int, stock int, err error) {
	// Загрузка SQL-запроса загрузки товара
	query, err := LoadSQLFile("lock_product.sql")
	if err != nil {
		return 0, 0, fmt.Errorf("failed to load lock_product.sql: %w", err)
	}

	// Выполнение запроса и извлечение данных о товаре
	err = t.tx.QueryRow(query, id).Scan(&price, &stock)
	if err == sql.ErrNoRows {
		return 0, 0, fmt.Errorf("product not found")
	}
	if err != nil {
		return 0, 0, fmt.Errorf("failed to lock product: %w", err)
	}
	return price, stock, nil
}

// Обновление складских остатков товара
func (t *Transaction) UpdateStock(id int, delta int) error {
	// Формирование текста SQL-запроса изменения стока
	query := `UPDATE products SET stock = stock + $1 WHERE id = $2`
	// Исполнение запроса в базе данных
	_, err := t.tx.Exec(query, delta, id)
	if err != nil {
		return fmt.Errorf("failed to update stock: %w", err)
	}
	return nil
}

// Создание записи о новом заказе
func (t *Transaction) CreateOrder() (*Order, error) {
	// Чтение SQL-скрипта с жесткого диска
	query, err := LoadSQLFile("insert_order.sql")
	if err != nil {
		return nil, fmt.Errorf("failed to load insert_order.sql: %w", err)
	}

	order := &Order{}
	// Исполнение запроса и сканирование идентификатора
	err = t.tx.QueryRow(query).Scan(&order.ID, &order.Status, &order.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to create order: %w", err)
	}
	return order, nil
}

// Добавление отдельной позиции заказа (товара)
func (t *Transaction) AddOrderItem(orderID, productID, quantity, priceAtOrder int) error {
	// Извлечение текста SQL-команды
	query, err := LoadSQLFile("insert_order_item.sql")
	if err != nil {
		return fmt.Errorf("failed to load insert_order_item.sql: %w", err)
	}

	// Выполнение SQL-инструкции вставки позиции
	_, err = t.tx.Exec(query, orderID, productID, quantity, priceAtOrder)
	if err != nil {
		return fmt.Errorf("failed to add order item: %w", err)
	}
	return nil
}

// Удаление отдельной позиции из заказа
func (t *Transaction) DeleteOrderItem(orderID, productID int) (int, error) {
	// Чтение текста SQL-инструкции
	query, err := LoadSQLFile("delete_order_item.sql")
	if err != nil {
		return 0, fmt.Errorf("failed to load delete_order_item.sql: %w", err)
	}

	var quantity int
	// Исполнение SQL-инструкции и сканирование количества удаленного товара
	err = t.tx.QueryRow(query, orderID, productID).Scan(&quantity)
	if err == sql.ErrNoRows {
		return 0, fmt.Errorf("order item not found")
	}
	if err != nil {
		return 0, fmt.Errorf("failed to delete order item: %w", err)
	}

	return quantity, nil
}

// Обертка вызова транзакции с механизмом перезапуска при блокировках БД
func RetryTransaction(storage *Storage, maxRetries int, fn func(*Transaction) error) error {
	var lastErr error
	// Инициализация генератора псевдослучайных чисел для паузы
	rand.Seed(time.Now().UnixNano())

	// Цикл повторного исполнения попыток транзакции
	for attempt := 0; attempt < maxRetries; attempt++ {
		// Старт новой транзакции
		tx, err := storage.Begin()
		if err != nil {
			return fmt.Errorf("failed to begin transaction: %w", err)
		}

		// Вызов функции бизнес-логики с текущей транзакцией
		err = fn(tx)
		if err == nil {
			// Фиксация изменений в БД
			commitErr := tx.Commit()
			if commitErr == nil {
				return nil
			}
			lastErr = commitErr
			// Сброс транзакции при ошибке фиксации
			tx.Rollback()
			// Исключение несовместимых ошибок из цикла попыток
			if !isRetryableError(commitErr) {
				return commitErr
			}
		} else {
			lastErr = err
			// Откат изменений при системной или бизнес-ошибке в функции
			tx.Rollback()
			// Исключение несовместимых ошибок
			if !isRetryableError(err) {
				return err
			}
		}

		// Применение задержки (exponential backoff) перед следующей попыткой
		if attempt < maxRetries-1 {
			backoff := time.Duration(50+rand.Intn(150)) * time.Millisecond
			time.Sleep(backoff * time.Duration(1<<uint(attempt)))
		}
	}

	return fmt.Errorf("transaction failed after %d retries: %w", maxRetries, lastErr)
}

// Определение необходимости перезапуска транзакции при ошибках базы данных
func isRetryableError(err error) bool {
	if err == nil {
		return false
	}
	errStr := err.Error()
	// Проверка на коды сбоя сериализации или взаимной блокировки (PostgreSQL 40001)
	return strings.Contains(errStr, "serialization") || 
		   strings.Contains(errStr, "deadlock") || 
		   strings.Contains(errStr, "could not serialize") ||
		   strings.Contains(errStr, "40001") // Код ошибки сериализации PostgreSQL
}
