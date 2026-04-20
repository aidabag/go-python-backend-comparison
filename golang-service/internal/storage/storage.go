package storage

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"time"

	_ "github.com/lib/pq"
)

// Подключение к базе данных ресурсов
type Storage struct {
	db *sql.DB
}

// Инициализация соединения с базой данных и конфигурация пула
func New(dsn string, maxConn int) (*Storage, error) {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Установка ограничений для пула соединений
	db.SetMaxOpenConns(maxConn)
	db.SetMaxIdleConns(maxConn / 2)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Проверка доступности узла базы данных
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Storage{db: db}, nil
}

// Закрытие соединения с базой данных
func (s *Storage) Close() error {
	return s.db.Close()
}

// Возврат объекта базы данных
func (s *Storage) DB() *sql.DB {
	return s.db
}

// Чтение содержимого SQL-скрипта из файловой системы
func LoadSQLFile(filename string) (string, error) {
	// Определение рабочей директории
	wd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("sql file not found: %s (failed to get working directory)", filename)
	}

	// Формирование списка каноничных путей поиска файлов
	fsPaths := []string{
		filepath.Join(wd, "sql", filename),
		filepath.Join(wd, "sql", "migrations", filename),
		filepath.Join(wd, "sql", "seed", filename),
		// Поиск путей от корня монорепозитория (рекомендуемый вариант)
		filepath.Join(wd, "..", "sql", filename),
		filepath.Join(wd, "..", "sql", "migrations", filename),
		filepath.Join(wd, "..", "sql", "seed", filename),
	}

	// Итеративное чтение файла по путям
	for _, path := range fsPaths {
		if data, err := os.ReadFile(path); err == nil {
			return string(data), nil
		}
	}

	return "", fmt.Errorf("sql file not found: %s", filename)
}

// Исполнение миграций схемы базы данных при старте сервиса
func (s *Storage) ApplyMigrations() error {
	// Чтение скрипта миграций
	schema, err := LoadSQLFile("001_schema.sql")
	if err != nil {
		return fmt.Errorf("failed to load schema migration: %w", err)
	}
	
	// Выполнение инструкций создания таблиц
	if _, err := s.db.Exec(schema); err != nil {
		return fmt.Errorf("failed to apply schema migration: %w", err)
	}
	
	return nil
}
