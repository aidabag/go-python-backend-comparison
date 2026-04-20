package main

import (
	"fmt"
	"log"
	"net/http"
	"strings"

	"golang-service/internal/config"
	"golang-service/internal/handlers"
	"golang-service/internal/metrics"
	"golang-service/internal/middleware"
	"golang-service/internal/service"
	"golang-service/internal/storage"
)

// Точка входа в приложение веб-сервера
func main() {
	// Инициализация конфигурации
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Структурирование строки подключения к базе данных
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		cfg.DBHost, cfg.DBPort, cfg.DBUser, cfg.DBPass, cfg.DBName)

	// Инициализация слоя подключения к базе данных
	st, err := storage.New(dsn, cfg.DBPoolMaxConn)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	
	// Применение миграций схемы базы данных (создание таблиц)
	if err := st.ApplyMigrations(); err != nil {
		log.Fatalf("Failed to apply migrations: %v", err)
	}
	// Отложенное закрытие пула соединений
	defer st.Close()

	// Инициализация системы сбора метрик Prometheus
	metrics.Init()

	// Инстанцирование хранилищ бизнес-сущностей
	productStorage := storage.NewProductStorage(st.DB())
	orderStorage := storage.NewOrderStorage(st.DB())

	// Создание сервисов бизнес-логики
	productService := service.NewProductService(productStorage)
	orderService := service.NewOrderService(orderStorage, productStorage, st, cfg.MaxTxRetries)

	// Регистрация контроллеров веб-запросов
	productHandler := handlers.NewProductHandler(productService)
	orderHandler := handlers.NewOrderHandler(orderService)

	// Настройка корневого маршрутизатора Mux
	mux := http.NewServeMux()

	// Привязка маршрутов товаров
	mux.HandleFunc("/products", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			productHandler.CreateProduct(w, r)
		case http.MethodGet:
			productHandler.ListProducts(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/products/", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			productHandler.GetProduct(w, r)
		case http.MethodPut:
			productHandler.UpdateProduct(w, r)
		case http.MethodDelete:
			productHandler.DeleteProduct(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Привязка маршрутов заказов
	mux.HandleFunc("/orders", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			orderHandler.CreateOrder(w, r)
		case http.MethodGet:
			orderHandler.ListOrders(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Делегирование обработки вложенных маршрутов заказов
	mux.HandleFunc("/orders/", func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path

		// Маршрутизация удаления связи товара и заказа
		if strings.Contains(path, "/items/") && r.Method == http.MethodDelete {
			orderHandler.DeleteOrderItem(w, r)
			return
		}

		// Маршрутизация добавления товара в заказ
		if strings.HasSuffix(path, "/items") && r.Method == http.MethodPost {
			orderHandler.AddOrderItem(w, r)
			return
		}

		// Расчет суммы заказа
		if strings.HasSuffix(path, "/total") && r.Method == http.MethodGet {
			orderHandler.GetOrderTotal(w, r)
			return
		}

		// Генерация сводной информации по заказу
		if strings.HasSuffix(path, "/summary") && r.Method == http.MethodGet {
			orderHandler.GetOrderSummary(w, r)
			return
		}

		// Извлечение информации о конкретном заказе
		if r.Method == http.MethodGet {
			orderHandler.GetOrder(w, r)
			return
		}

		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	})

	// Интеграция аналитических эндпоинтов
	mux.HandleFunc("/analytics/orders/average", orderHandler.GetAverageOrderValue)
	mux.HandleFunc("/analytics/products/top", orderHandler.GetTopProducts)

	// Настройка конечных точек состояния
	mux.HandleFunc("/health", handlers.HealthHandler)
	mux.HandleFunc(cfg.MetricsPath, metrics.Handler().ServeHTTP)

	// Оборачивание обработчиков в промежуточное ПО (Middleware)
	handler := middleware.LoggingMiddleware(mux)
	handler = metrics.MetricsMiddleware(handler)

	// Запуск сетевого прослушивателя сервера
	addr := fmt.Sprintf(":%s", cfg.ServicePort)
	fmt.Printf("Server starting on %s\n", addr)
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
