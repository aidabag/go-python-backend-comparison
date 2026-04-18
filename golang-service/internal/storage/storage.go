package storage

import (
	"database/sql"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

// Структура подключения к базе данных
type Storage struct {
	db *sql.DB
}

// Инициализация соединения с базой данных и настройка пула
func New(dsn string, maxConn int) (*Storage, error) {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	db.SetMaxOpenConns(maxConn)
	db.SetMaxIdleConns(maxConn / 2)
	db.SetConnMaxLifetime(5 * time.Minute)

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Storage{db: db}, nil
}

// Закрытие соединения с базой данных
func (s *Storage) Close() error {
	return s.db.Close()
}

// Получение объекта базы данных
func (s *Storage) DB() *sql.DB {
	return s.db
}

var embeddedSQLFS fs.FS

// Установка встроенной файловой системы для файлов SQL
func SetEmbeddedSQLFS(fs fs.FS) {
	embeddedSQLFS = fs
}

// Чтение содержимого SQL-скрипта по имени файла
func LoadSQLFile(filename string) (string, error) {
	// Попытка чтения файла из встроенной файловой системы
	// Встроенная ФС содержит файлы из директории sql
	if embeddedSQLFS != nil {
		// Проверка возможных путей во встроенной файловой системе
		// Структура путей: *.sql, migrations/*.sql, seed/*.sql
		paths := []string{
			filename,
			"migrations/" + filename,
			"seed/" + filename,
		}

		for _, path := range paths {
			if data, err := fs.ReadFile(embeddedSQLFS, path); err == nil {
				return string(data), nil
			}
		}

		// Поиск файла путем полного обхода директорий встроенной файловой системы
		var foundPath string
		fs.WalkDir(embeddedSQLFS, ".", func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return nil // Переход к следующему элементу
			}
			if !d.IsDir() && strings.HasSuffix(path, filename) {
				foundPath = path
				return nil
			}
			return nil
		})

		if foundPath != "" {
			if data, err := fs.ReadFile(embeddedSQLFS, foundPath); err == nil {
				return string(data), nil
			}
		}
	}

	// Резервное чтение из файловой системы для процесса разработки
	wd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("sql file not found: %s (failed to get working directory)", filename)
	}

	// Проверка локальных каноничных путей проекта
	fsPaths := []string{
		filepath.Join(wd, "sql", filename),
		filepath.Join(wd, "sql", "migrations", filename),
		filepath.Join(wd, "sql", "seed", filename),
		// Поиск при запуске из родительской директории
		filepath.Join(wd, "golang-service", "sql", filename),
		filepath.Join(wd, "golang-service", "sql", "migrations", filename),
		filepath.Join(wd, "golang-service", "sql", "seed", filename),
	}

	for _, path := range fsPaths {
		if data, err := os.ReadFile(path); err == nil {
			return string(data), nil
		}
	}

	return "", fmt.Errorf("sql file not found: %s", filename)
}

// Применение миграций схемы базы данных
func (s *Storage) ApplyMigrations() error {
	schema, err := LoadSQLFile("001_schema.sql")
	if err != nil {
		return fmt.Errorf("failed to load schema migration: %w", err)
	}
	
	if _, err := s.db.Exec(schema); err != nil {
		return fmt.Errorf("failed to apply schema migration: %w", err)
	}
	
	return nil
}
