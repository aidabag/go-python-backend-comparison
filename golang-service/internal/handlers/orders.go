package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"time"

	"golang-service/internal/service"
)

// Структура обработчика маршрутов для заказов
type OrderHandler struct {
	service *service.OrderService
}

// Инициализация слоя обработчиков заказов
func NewOrderHandler(orderService *service.OrderService) *OrderHandler {
	return &OrderHandler{service: orderService}
}

// Обработка запроса на формирование нового заказа
func (h *OrderHandler) CreateOrder(w http.ResponseWriter, r *http.Request) {
	// Валидация HTTP-метода
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req service.CreateOrderRequest
	// Декодирование JSON-структуры запроса
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid request body", nil)
		return
	}

	// Делегирование процессинга создания заказа сервисному слою
	order, err := h.service.CreateOrder(&req)
	if err != nil {
		// Идентификация ошибки нехватки товаров
		if strings.Contains(err.Error(), "insufficient stock") {
			writeError(w, http.StatusConflict, "insufficient_stock", err.Error(), nil)
			return
		}
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Отправка кода успешного создания и тела документа
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(order)
}

// Обработка запроса на извлечение сведений о заказе
func (h *OrderHandler) GetOrder(w http.ResponseWriter, r *http.Request) {
	// Контроль метода
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Парсинг идентификатора из URL-пути
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 3 {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	id, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	// Делегирование операции чтения заказа
	order, err := h.service.GetOrder(id, true)
	if err != nil {
		// Отработка ошибки отсутствующей сущности
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Order not found", nil)
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Сериализация и отправка результата клиенту
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

// Обработка директивы на получение списка заказов
func (h *OrderHandler) ListOrders(w http.ResponseWriter, r *http.Request) {
	// Валидация метода
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	limit := 100
	offset := 0
	// Извлечение параметров фильтрации из GET-структуры
	status := r.URL.Query().Get("status")
	includeItems := r.URL.Query().Get("include_items") == "true"

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil {
			offset = o
		}
	}

	// Запрос агрегированной коллекции у сервиса
	orders, err := h.service.ListOrders(limit, offset, status, includeItems)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Выгрузка массива клиенту
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(orders)
}

// Управление интеграцией дополнительной позиции в спецификацию заказа
func (h *OrderHandler) AddOrderItem(w http.ResponseWriter, r *http.Request) {
	// Подтверждение метода модификации
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 4 || pathParts[3] != "items" {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid path", nil)
		return
	}

	orderID, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	var req struct {
		ProductID int `json:"product_id"`
		Quantity  int `json:"quantity"`
	}
	// Декодирование тела запроса
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid request body", nil)
		return
	}

	// Инициализация процедуры добавления позиции
	if err := h.service.AddOrderItem(orderID, req.ProductID, req.Quantity); err != nil {
		// Анализ возможных путей возникновения ошибок бизнес-логики
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", err.Error(), nil)
			return
		}
		if strings.Contains(err.Error(), "insufficient stock") {
			writeError(w, http.StatusConflict, "insufficient_stock", err.Error(), nil)
			return
		}
		if strings.Contains(err.Error(), "can only modify") {
			writeError(w, http.StatusConflict, "validation_failed", err.Error(), nil)
			return
		}
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Загрузка обновленного состояния заказа
	order, err := h.service.GetOrder(orderID, true)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	// Отправка сериализованного представления
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

// Контроль процесса удаления позиции из закрытого заказа
func (h *OrderHandler) DeleteOrderItem(w http.ResponseWriter, r *http.Request) {
	// Подтверждение метода удаления
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 5 || pathParts[3] != "items" {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid path", nil)
		return
	}

	orderID, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	productID, err := strconv.Atoi(pathParts[4])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid product ID", nil)
		return
	}

	// Делегирование запуска функции удаления
	if err := h.service.DeleteOrderItem(orderID, productID); err != nil {
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", err.Error(), nil)
			return
		}
		if strings.Contains(err.Error(), "can only modify") {
			writeError(w, http.StatusConflict, "validation_failed", err.Error(), nil)
			return
		}
		writeError(w, http.StatusBadRequest, "validation_failed", err.Error(), nil)
		return
	}

	// Отправка ответа об успешном удалении
	w.WriteHeader(http.StatusNoContent)
}

// Запрос суммарной стоимости заказа
func (h *OrderHandler) GetOrderTotal(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 4 || pathParts[3] != "total" {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid path", nil)
		return
	}

	orderID, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	// Передача вычислений сервисному слою
	total, err := h.service.GetOrderTotal(orderID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Order not found", nil)
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	response := map[string]interface{}{
		"order_id": orderID,
		"total":    total,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Обработка вызова агрегированной статистики по заказу
func (h *OrderHandler) GetOrderSummary(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 4 || pathParts[3] != "summary" {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid path", nil)
		return
	}

	orderID, err := strconv.Atoi(pathParts[2])
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_failed", "Invalid order ID", nil)
		return
	}

	// Извлечение агрегированного итога
	summary, err := h.service.GetOrderSummary(orderID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			writeError(w, http.StatusNotFound, "not_found", "Order not found", nil)
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// Аналитический запрос показателей среднего чека
func (h *OrderHandler) GetAverageOrderValue(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var since, until *time.Time

	// Разбор параметров временного интервала
	if sinceStr := r.URL.Query().Get("since"); sinceStr != "" {
		if t, err := time.Parse(time.RFC3339, sinceStr); err == nil {
			since = &t
		}
	}

	if untilStr := r.URL.Query().Get("until"); untilStr != "" {
		if t, err := time.Parse(time.RFC3339, untilStr); err == nil {
			until = &t
		}
	}

	// Делегирование аналитического расчета
	avg, err := h.service.GetAverageOrderValue(since, until)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	response := map[string]interface{}{
		"average": avg,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Аналитический запрос рейтинга популярных товаров
func (h *OrderHandler) GetTopProducts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	limit := 10
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	var since, until *time.Time

	if sinceStr := r.URL.Query().Get("since"); sinceStr != "" {
		if t, err := time.Parse(time.RFC3339, sinceStr); err == nil {
			since = &t
		}
	}

	if untilStr := r.URL.Query().Get("until"); untilStr != "" {
		if t, err := time.Parse(time.RFC3339, untilStr); err == nil {
			until = &t
		}
	}

	// Делегирование математической группировки
	topProducts, err := h.service.GetTopProducts(limit, since, until)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error(), nil)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(topProducts)
}
