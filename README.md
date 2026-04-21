# Сравнение производительности Go и Python

Данный проект представляет собой монорепозиторий для высокоточного тестирования и сравнения производительности бэкенд-сервисов, написанных на **Go** и **Python**. 

Цель проекта — замер производительности языков в идентичных условиях:
1. Единая SQL-схема БД.
2. Идентичные SQL-запросы (через общие файлы).
3. Одинаковые лимиты ресурсов (CPU/RAM).
4. Одинаковые настройки пула соединений и retry-логики.

---

## Методология тестирования

Для получения научно достоверных результатов рекомендуется **последовательное** тестирование. Запуск обоих сервисов одновременно может исказить результаты из-за конкуренции за ресурсы хост-машины (Disk I/O, CPU Cache).

**Общий порт**: Оба сервиса настроены на внешний порт **8080**, что позволяет использовать один и тот же тестовый скрипт без изменения конфигурации.

### Тестовый прогон для Go:
1. Запуск стека: `docker-compose up -d golang-service`
2. Проведение тестов (на `localhost:8080`)
3. Полная очистка: `docker-compose down -v`

### Тестовый прогон для Python:
1. Запуск стека: `docker-compose up -d python-service`
2. Проведение тестов (на `localhost:8080`)
3. Полная очистка: `docker-compose down -v`

---

## Инфраструктура

| Параметр | Go Service | Python Service |
|---|---|---|
| **Язык / Рантайм** | Go 1.25 (Alpine) | Python 3.12 (Alpine) |
| **Веб-фреймворк** | Стандартный `net/http` | `Starlette` + `Uvicorn` |
| **Драйвер БД** | `lib/pq` | `asyncpg` |
| **Лимит CPU** | 4.0 Cores | 4.0 Cores |
| **Лимит RAM** | 3.0 GB | 3.0 GB |
| **Пул БД** | 20 соединений | 20 соединений |

---

## Полная проверка API (Все 16 эндпоинтов)

Команды идентичны для обоих сервисов (порт 8080).

### 1. Системные запросы
- **Health Check**:
  ```bash
  curl http://localhost:8080/health
  ```
- **Метрики Prometheus**:
  ```bash
  curl http://localhost:8080/metrics
  ```

### 2. Склад и Товары (Products)
- **Создать товар**: 
  ```bash
  curl -X POST http://localhost:8080/products \
       -d '{"name": "Laptop", "price": 100000, "stock": 50}'
  ```
- **Список товаров** (пагинация и сортировка `id_desc`, `id_asc`, `name`, `price`): 
  ```bash
  curl "http://localhost:8080/products?limit=5&offset=0&sort=price"
  ```
- **Получить товар по ID**: 
  ```bash
  curl http://localhost:8080/products/1
  ```
- **Обновить данные товара** (PUT/PATCH): 
  ```bash
  curl -X PUT http://localhost:8080/products/1 \
       -d '{"name": "Laptop Pro", "price": 110000, "stock": 45}'
  ```
- **Удалить товар**: 
  ```bash
  curl -X DELETE http://localhost:8080/products/1
  ```

### 3. Заказы (Orders)
- **Создать новый заказ**: 
  ```bash
  curl -X POST http://localhost:8080/orders \
       -H "Content-Type: application/json" \
       -d '{"items": [{"product_id": 1, "quantity": 1}]}'
  ```
- **Просмотреть список заказов** (фильтр по статусу): 
  ```bash
  curl "http://localhost:8080/orders?status=new&include_items=true"
  ```
- **Получить заказ по ID**: 
  ```bash
  curl http://localhost:8080/orders/1
  ```
- **Добавить позицию в заказ**: 
  ```bash
  curl -X POST http://localhost:8080/orders/1/items \
       -d '{"product_id": 2, "quantity": 1}'
  ```
- **Удалить позицию из заказа**: 
  ```bash
  curl -X DELETE http://localhost:8080/orders/1/items/2
  ```
- **Получить итоговую сумму заказа**: 
  ```bash
  curl http://localhost:8080/orders/1/total
  ```
- **Детальная квитанция (Summary)**: 
  ```bash
  curl http://localhost:8080/orders/1/summary
  ```

### 4. Аналитика (Analytics)
- **Запросить средний чек**: 
  ```bash
  curl http://localhost:8080/analytics/orders/average
  ```
- **Топ самых продаваемых товаров**: 
  ```bash
  curl "http://localhost:8080/analytics/products/top?limit=3"
  ```
