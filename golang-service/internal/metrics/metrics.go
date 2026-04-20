package metrics

import (
	"fmt"
	"net/http"
	"runtime"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"endpoint"},
	)

	appMemoryBytes = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "app_memory_bytes",
			Help: "Application memory usage in bytes",
		},
	)

	appCPUSecondsTotal = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "app_cpu_seconds_total",
			Help: "Total CPU time used by the application (placeholder)",
		},
	)

	dbLockWaitSecondsTotal = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "db_lock_wait_seconds_total",
			Help: "Total time spent waiting for database locks",
		},
	)
)

var registry *prometheus.Registry

// Инициализация системы метрик Prometheus
func Init() {
	registry = prometheus.NewRegistry()
	registry.MustRegister(httpRequestsTotal)
	registry.MustRegister(httpRequestDuration)
	registry.MustRegister(appMemoryBytes)
	registry.MustRegister(appCPUSecondsTotal)
	registry.MustRegister(dbLockWaitSecondsTotal)

	// Запуск фоновой горутины профилирования потребления памяти
	go updateMemoryMetrics()
}

// Забор статистики потребления оперативной памяти
func updateMemoryMetrics() {
	ticker := time.NewTicker(5 * time.Second)
	// Отложенная остановка таймера
	defer ticker.Stop()

	for range ticker.C {
		var m runtime.MemStats
		// Чтение состояния распределения памяти
		runtime.ReadMemStats(&m)
		appMemoryBytes.Set(float64(m.Alloc))
	}
}

// Интеграция промежуточного слоя сбора HTTP-статистики
func MetricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(rw, r)

		duration := time.Since(start).Seconds()
		endpoint := normalizePath(r.URL.Path)

		statusCode := fmt.Sprintf("%d", rw.statusCode)
		// Увеличение счетчика входящих запросов
		httpRequestsTotal.WithLabelValues(r.Method, endpoint, statusCode).Inc()
		// Наблюдение за задержками времени ответа
		httpRequestDuration.WithLabelValues(endpoint).Observe(duration)
	})
}

// Структура перехватчика HTTP ответов для захвата статус-кода
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

// Захват записи заголовка ответа
func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Возврат HTTP обработчика модуля Prometheus
func Handler() http.Handler {
	return promhttp.HandlerFor(registry, promhttp.HandlerOpts{})
}

// Регистрация времени ожидания блокировок СУБД
func RecordDBLockWait(duration time.Duration) {
	dbLockWaitSecondsTotal.Add(duration.Seconds())
}
