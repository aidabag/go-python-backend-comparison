package handlers

import (
	"encoding/json"
	"net/http"
)

// Проверка состояния работоспособности сервиса
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	// Проверка соответствия HTTP-метода
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Формирование успешного ответа
	response := map[string]string{
		"status": "ok",
	}

	// Установка заголовков и отправка результата
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
