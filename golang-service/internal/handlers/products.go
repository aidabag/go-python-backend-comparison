package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"golang-service/internal/service"
)

// Структура обработчика маршрутов для товаров
type ProductHandler struct {
	service *service.ProductService
}

// Инициализация слоя обработчиков товаров
func NewProductHandler(productService *service.ProductService) *ProductHandler {
	return &ProductHandler{service: productService}
}

// Структура запроса на создание товара
type CreateProductRequest struct {
	Name  string `json:"name"`
	Price int    `json:"price"`
	Stock int    `json:"stock"`
}

// Обработка запроса на создание нового товара
func (h *ProductHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
	// Проверка соответствия HTTP-метода
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req CreateProductRequest
	// Декодирование тела запроса в структуру
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid request body", nil)
		return
	}

	// Делегирование создания товара слою сервиса
	product, err := h.service.CreateProduct(req.Name, req.Price, req.Stock)
	if err != nil {
		// Обработка конфликтов уникальности сущности
		if strings.Contains(err.Error(), "duplicate") || strings.Contains(err.Error(), "unique") {
			writeError(w, http.StatusConflict, "validation_failed", err.Error(), nil)
			return
		}
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Отправка ответа об успешной регистрации
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(product)
}

// Обработка запроса на получение данных товара
func (h *ProductHandler) GetProduct(w http.ResponseWriter, r *http.Request) {
	// Валидация HTTP-метода
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Извлечение идентификатора из пути запроса
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 3 {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	id, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	// Получение данных через слой бизнес-логики
	product, err := h.service.GetProduct(id)
	if err != nil {
		// Отработка случая отсутствия данных
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Product not found", nil)
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Сериализация и отправка результата клиенту
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(product)
}

// Извлечение списка товаров с учетом параметров URL
// Установка сортировки по умолчанию: новые записи в начале
// Поддержка сортировок: id_desc, id, id_asc, name, price
func (h *ProductHandler) ListProducts(w http.ResponseWriter, r *http.Request) {
	// Подтверждение правильности метода
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	limit := 100
	offset := 0
	sort := ""

	// Чтение параметра лимита из GET-запроса
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	// Чтение параметра смещения из GET-запроса
	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil {
			offset = o
		}
	}

	// Чтение параметра сортировки
	if sortStr := r.URL.Query().Get("sort"); sortStr != "" {
		sort = sortStr
	}

	// Запрос списка товаров к сервису
	products, err := h.service.ListProducts(limit, offset, sort)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Отправка сериализованного списка массивного ответа
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(products)
}

// Обработка запроса на частичное обновление данных товара (PUT / PATCH)
func (h *ProductHandler) UpdateProduct(w http.ResponseWriter, r *http.Request) {
	// Проверка разрешенного метода изменения
	if r.Method != http.MethodPut {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Извлечение целевого идентификатора товара из URL
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 3 {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	id, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	var updates map[string]interface{}
	// Декодирование тела запроса JSON в словарь
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid request body", nil)
		return
	}

	// Делегирование процесса обновления слою сервисов
	if err := h.service.UpdateProduct(id, updates); err != nil {
		// Отработка ошибки отсутствующего товара
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Product not found", nil)
			return
		}
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Получение актуального состояния модифицированного товара
	product, err := h.service.GetProduct(id)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Формирование и отправка успешного ответа
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(product)
}

// Обработка директивы на удаление товара
func (h *ProductHandler) DeleteProduct(w http.ResponseWriter, r *http.Request) {
	// Проверка корректности метода
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Парсинг идентификатора из URL
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 3 {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	id, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	// Отправка команды удаления
	if err := h.service.DeleteProduct(id); err != nil {
		// Валидация попытки удаления несуществующего товара
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Product not found", nil)
			return
		}
		// Перехват запрета на удаление по внешнему ключу заказов
		if strings.Contains(err.Error(), "used in orders") {
			writeError(w, http.StatusConflict, "validation_failed", err.Error(), nil)
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Отправка статуса 204 без тела сообщения
	w.WriteHeader(http.StatusNoContent)
}
