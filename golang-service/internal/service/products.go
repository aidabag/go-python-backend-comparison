package service

import (
	"fmt"
	"golang-service/internal/storage"
)

// Структура сервиса управления товарами
type ProductService struct {
	productStorage *storage.ProductStorage
}

// Инициализация сервисного слоя товаров
func NewProductService(productStorage *storage.ProductStorage) *ProductService {
	return &ProductService{productStorage: productStorage}
}

// Регистрация нового товара с проверкой входных параметров
func (s *ProductService) CreateProduct(name string, price, stock int) (*storage.Product, error) {
	// Проверка наличия наименования
	if name == "" {
		return nil, fmt.Errorf("name is required")
	}
	// Проверка корректности цены
	if price < 0 {
		return nil, fmt.Errorf("price must be non-negative")
	}
	// Проверка корректности остатков
	if stock < 0 {
		return nil, fmt.Errorf("stock must be non-negative")
	}

	// Формирование структуры сущности
	product := &storage.Product{
		Name:  name,
		Price: price,
		Stock: stock,
	}

	// Передача записи в слой хранения
	if err := s.productStorage.Create(product); err != nil {
		return nil, err
	}

	return product, nil
}

// Извлечение данных товара по уникальному идентификатору
func (s *ProductService) GetProduct(id int) (*storage.Product, error) {
	// Делегирование запроса слою базы данных
	return s.productStorage.GetByID(id)
}

// Составление списка товаров с проверкой границ пагинации
func (s *ProductService) ListProducts(limit, offset int, sort string) ([]*storage.Product, error) {
	// Валидация нижней границы размера выборки
	if limit <= 0 {
		limit = 100
	}
	// Валидация верхней границы размера выборки
	if limit > 1000 {
		limit = 1000
	}
	// Валидация смещения
	if offset < 0 {
		offset = 0
	}

	// Исполнение запроса выборки к базе данных
	return s.productStorage.List(limit, offset, sort)
}

// Безопасное обновление значений полей товара
func (s *ProductService) UpdateProduct(id int, updates map[string]interface{}) error {
	// Инициализация фильтра разрешенных к изменению ключей
	allowedFields := map[string]bool{"name": true, "price": true, "stock": true}
	// Выделение памяти под карту проверенных полей
	validatedUpdates := make(map[string]interface{})

	// Цикл валидации входящих параметров обновления
	for key, value := range updates {
		// Игнорирование недопустимых полей
		if !allowedFields[key] {
			continue
		}

		// Приведение типов и логическая проверка значений
		switch key {
		case "price":
			if price, ok := value.(float64); ok {
				if price < 0 {
					return fmt.Errorf("price must be non-negative")
				}
				validatedUpdates[key] = int(price)
			} else if price, ok := value.(int); ok {
				if price < 0 {
					return fmt.Errorf("price must be non-negative")
				}
				validatedUpdates[key] = price
			}
		case "stock":
			if stock, ok := value.(float64); ok {
				if stock < 0 {
					return fmt.Errorf("stock must be non-negative")
				}
				validatedUpdates[key] = int(stock)
			} else if stock, ok := value.(int); ok {
				if stock < 0 {
					return fmt.Errorf("stock must be non-negative")
				}
				validatedUpdates[key] = stock
			}
		case "name":
			if name, ok := value.(string); ok {
				validatedUpdates[key] = name
			}
		}
	}

	// Прерывание операции при отсутствии корректных данных
	if len(validatedUpdates) == 0 {
		return nil
	}

	// Делегирование операции обновления слою хранения
	return s.productStorage.Update(id, validatedUpdates)
}

// Удаление товара из каталога базы данных
func (s *ProductService) DeleteProduct(id int) error {
	// Отправка команды на физическое удаление с проверкой связей
	return s.productStorage.Delete(id)
}
