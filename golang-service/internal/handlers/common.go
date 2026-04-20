package handlers

import (
	"encoding/json"
	"net/http"
)

// Отправка структурированного ответа с ошибкой сервера
func writeError(w http.ResponseWriter, status int, errorType, message string, details interface{}) {
	// Установка заголовка формата данных
	w.Header().Set("Content-Type", "application/json")
	// Запись статус-кода
	w.WriteHeader(status)
	
	// Формирование структуры ответа
	errorResponse := map[string]interface{}{
		"error":   errorType,
		"message": message,
	}
	// Добавление поля дополнительных деталей при наличии данных
	if details != nil {
		errorResponse["details"] = details
	}
	
	// Конвертация структуры в JSON-строку
	json.NewEncoder(w).Encode(errorResponse)
}
