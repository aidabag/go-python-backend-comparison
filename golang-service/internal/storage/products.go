package storage

import (
	"database/sql"
	"fmt"
	"strings"
)

// Структура данных о товаре
type Product struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Price int    `json:"price"`
	Stock int    `json:"stock"`
}

// Обертка подключения к базе данных для управления товарами
type ProductStorage struct {
	db *sql.DB
}

// Инициализация слоя хранения для сущности товаров
func NewProductStorage(db *sql.DB) *ProductStorage {
	return &ProductStorage{db: db}
}

// Запись нового товара в базу данных
func (s *ProductStorage) Create(p *Product) error {
	// Подготовка текста SQL-запроса вставки
	query := `INSERT INTO products (name, price, stock) VALUES ($1, $2, $3) RETURNING id`
	// Выполнение инструкции и сканирование сгенерированного идентификатора
	err := s.db.QueryRow(query, p.Name, p.Price, p.Stock).Scan(&p.ID)
	if err != nil {
		return fmt.Errorf("failed to create product: %w", err)
	}
	return nil
}

// Извлечение данных товара по уникальному идентификатору
func (s *ProductStorage) GetByID(id int) (*Product, error) {
	p := &Product{}
	// Инициализация текста запроса поиска
	query := `SELECT id, name, price, stock FROM products WHERE id = $1`
	// Исполнение запроса и сканирование полей в структуру товара
	err := s.db.QueryRow(query, id).Scan(&p.ID, &p.Name, &p.Price, &p.Stock)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("product not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get product: %w", err)
	}
	return p, nil
}

// Получение списка товаров с применением пагинации и сортировки
func (s *ProductStorage) List(limit, offset int, sort string) ([]*Product, error) {
	// Установка сортировки по умолчанию (новые записи в начале)
	orderBy := "id DESC"
	
	// Безопасное сопоставление строкового параметра с SQL-выражением ORDER BY
	switch sort {
	case "", "id_desc":
		orderBy = "id DESC"
	case "id", "id_asc":
		orderBy = "id ASC"
	case "name":
		orderBy = "name ASC"
	case "price":
		orderBy = "price ASC"
	default:
		// Выбор значения по умолчанию при получении неизвестного параметра сортировки
		orderBy = "id DESC"
	}

	// Формирование итогового SQL-запроса 
	query := fmt.Sprintf(`SELECT id, name, price, stock FROM products ORDER BY %s LIMIT $1 OFFSET $2`, orderBy)
	// Исполнение запроса выборки
	rows, err := s.db.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to list products: %w", err)
	}
	// Отложенное закрытие курсора
	defer rows.Close()

	var products []*Product
	// Построчное чтение результатов выборки
	for rows.Next() {
		p := &Product{}
		if err := rows.Scan(&p.ID, &p.Name, &p.Price, &p.Stock); err != nil {
			return nil, fmt.Errorf("failed to scan product: %w", err)
		}
		// Добавление разобранной структуры в итоговый срез
		products = append(products, p)
	}

	return products, nil
}

// Частичное обновление данных товара (PATCH операция)
func (s *ProductStorage) Update(id int, updates map[string]interface{}) error {
	// Проверка наличия полей для обновления
	if len(updates) == 0 {
		return nil
	}

	setParts := []string{}
	args := []interface{}{}
	argNum := 1

	// Формирование пар ключ-значение для SQL-инструкции SET
	for key, value := range updates {
		setParts = append(setParts, fmt.Sprintf("%s = $%d", key, argNum))
		args = append(args, value)
		argNum++
	}

	// Добавление идентификатора товара в конец списка аргументов
	args = append(args, id)
	// Динамическая склейка SQL-запроса изменения
	query := fmt.Sprintf(`UPDATE products SET %s WHERE id = $%d`, 
		strings.Join(setParts, ", "), argNum)

	// Исполнение инструкции обновления
	_, err := s.db.Exec(query, args...)
	if err != nil {
		return fmt.Errorf("failed to update product: %w", err)
	}
	return nil
}

// Удаление товара из базы данных
func (s *ProductStorage) Delete(id int) error {
	var count int
	// Проверка использования товара в оформленных заказах
	checkQuery := `SELECT COUNT(*) FROM order_items WHERE product_id = $1`
	// Исполнение запроса подсчета связанных записей
	err := s.db.QueryRow(checkQuery, id).Scan(&count)
	if err != nil {
		return fmt.Errorf("failed to check product usage: %w", err)
	}
	if count > 0 {
		return fmt.Errorf("product is used in orders and cannot be deleted")
	}

	// Подготовка SQL-команды удаления
	query := `DELETE FROM products WHERE id = $1`
	// Исполнение инструкции
	_, err = s.db.Exec(query, id)
	if err != nil {
		return fmt.Errorf("failed to delete product: %w", err)
	}
	return nil
}

// Наложение блокировки строк на товар для предотвращения состояний гонки
func (s *ProductStorage) LockProduct(id int) (price int, stock int, err error) {
	// Чтение SQL-запроса из файловой системы монорепозитория
	query, err := LoadSQLFile("lock_product.sql")
	if err != nil {
		return 0, 0, fmt.Errorf("failed to load lock_product.sql: %w", err)
	}

	// Выполнение запроса и извлечение данных
	err = s.db.QueryRow(query, id).Scan(&price, &stock)
	if err == sql.ErrNoRows {
		return 0, 0, fmt.Errorf("product not found")
	}
	if err != nil {
		return 0, 0, fmt.Errorf("failed to lock product: %w", err)
	}
	return price, stock, nil
}

// Обновление складских остатков товара
func (s *ProductStorage) UpdateStock(id int, delta int) error {
	// Подготовка команды обновления запасов
	query := `UPDATE products SET stock = stock + $1 WHERE id = $2`
	// Исполнение команды
	_, err := s.db.Exec(query, delta, id)
	if err != nil {
		return fmt.Errorf("failed to update stock: %w", err)
	}
	return nil
}
