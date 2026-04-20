package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// Структура записи журнала активности
type LogEntry struct {
	TS        string `json:"ts"`
	Level     string `json:"level"`
	Service   string `json:"service"`
	Endpoint  string `json:"endpoint"`
	Method    string `json:"method"`
	Path      string `json:"path"`
	Status    int    `json:"status"`
	DurationMs int64 `json:"duration_ms"`
	RequestID string `json:"request_id,omitempty"`
	Msg       string `json:"msg"`
}

// Перехват и журналирование HTTP-запросов
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Фиксация времени начала обработки
		start := time.Now()
		// Генерация уникального идентификатора
		requestID := uuid.New().String()

		// Создание обертки для извлечения статус-кода
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Добавление уникального идентификатора в заголовки
		r.Header.Set("X-Request-ID", requestID)

		// Передача управления следующему обработчику
		next.ServeHTTP(rw, r)

		// Вычисление длительности обработки
		duration := time.Since(start)
		durationMs := duration.Milliseconds()

		// Определение уровня критичности на базе статус-кода
		level := "info"
		if rw.statusCode >= 500 {
			level = "error"
		} else if rw.statusCode >= 400 {
			level = "warn"
		}

		// Формирование записи журнала
		logEntry := LogEntry{
			TS:        time.Now().UTC().Format(time.RFC3339),
			Level:     level,
			Service:   "golang-service",
			Endpoint:  r.URL.Path,
			Method:    r.Method,
			Path:      r.URL.Path,
			Status:    rw.statusCode,
			DurationMs: durationMs,
			RequestID: requestID,
			Msg:       getMessage(r.Method, r.URL.Path, rw.statusCode),
		}

		// Сериализация и вывод в поток стандартного вывода
		logJSON, _ := json.Marshal(logEntry)
		fmt.Println(string(logJSON))
	})
}

// Структура перехватчика ответов
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

// Запись заголовка со статусом
func (rw *responseWriter) WriteHeader(code int) {
	// Сохранение перехваченного кода
	rw.statusCode = code
	// Вызов оригинального метода
	rw.ResponseWriter.WriteHeader(code)
}

// Определение контекстного текста для журнала
func getMessage(method, path string, status int) string {
	if status >= 500 {
		return "internal server error"
	}
	if status >= 400 {
		return "client error"
	}

	switch {
	case method == "POST" && path == "/products":
		return "product created"
	case method == "GET" && path == "/products":
		return "products listed"
	case method == "GET" && len(path) > 9 && path[:9] == "/products":
		return "product retrieved"
	case method == "PUT" && len(path) > 9 && path[:9] == "/products":
		return "product updated"
	case method == "DELETE" && len(path) > 9 && path[:9] == "/products":
		return "product deleted"
	case method == "POST" && path == "/orders":
		return "order created"
	case method == "GET" && path == "/orders":
		return "orders listed"
	case method == "GET" && len(path) > 7 && path[:7] == "/orders":
		return "order retrieved"
	case method == "POST" && len(path) > 13 && path[:13] == "/orders" && path[len(path)-6:] == "/items":
		return "order item added"
	case method == "DELETE" && len(path) > 13 && path[:13] == "/orders":
		return "order item deleted"
	case method == "GET" && len(path) > 13 && path[len(path)-6:] == "/total":
		return "order total calculated"
	case method == "GET" && len(path) > 15 && path[len(path)-8:] == "/summary":
		return "order summary retrieved"
	case method == "GET" && path == "/analytics/orders/average":
		return "average order value calculated"
	case method == "GET" && path == "/analytics/products/top":
		return "top products retrieved"
	case method == "GET" && path == "/health":
		return "health check"
	case method == "GET" && path == "/metrics":
		return "metrics retrieved"
	default:
		return "request processed"
	}
}
