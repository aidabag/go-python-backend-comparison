package config

import (
	"fmt"
	"os"
	"strconv"
)

// Структура параметров конфигурации сервиса
type Config struct {
	DBHost         string
	DBPort         string
	DBName         string
	DBUser         string
	DBPass         string
	ServicePort    string
	LogLevel       string
	MaxTxRetries   int
	DBPoolMaxConn  int
	MetricsPath    string
}

// Извлечение параметров конфигурации из переменных окружения
func Load() (*Config, error) {
	cfg := &Config{
		DBHost:        getEnv("DB_HOST", "localhost"),
		DBPort:        getEnv("DB_PORT", "5432"),
		DBName:        getEnv("DB_NAME", "go_service"),
		DBUser:        getEnv("DB_USER", "postgres"),
		DBPass:        getEnv("DB_PASS", "postgres"),
		ServicePort:   getEnv("SERVICE_PORT", "8080"),
		LogLevel:      getEnv("LOG_LEVEL", "info"),
		MaxTxRetries:  getEnvInt("MAX_TX_RETRIES", 3),
		DBPoolMaxConn: getEnvInt("DB_POOL_MAX_CONN", 20),
		MetricsPath:   getEnv("METRICS_PATH", "/metrics"),
	}

	// Проверка валидности уровня логирования
	if cfg.LogLevel != "info" && cfg.LogLevel != "warn" && cfg.LogLevel != "error" {
		return nil, fmt.Errorf("invalid LOG_LEVEL: %s (must be info, warn, or error)", cfg.LogLevel)
	}

	return cfg, nil
}

// Получение строкового значения из переменной окружения или возврат значения по умолчанию
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Получение целочисленного значения из переменной окружения или возврат значения по умолчанию
func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}
