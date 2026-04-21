# Подготовка сборочного образа
FROM python:3.12-alpine AS builder

WORKDIR /app

# Установка системных зависимостей для сборки psutil и asyncpg
RUN apk --no-cache add gcc musl-dev python3-dev postgresql-dev linux-headers

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование файла зависимостей
COPY python-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода приложения
COPY python-service/ .

# Копирование общих SQL файлов монорепозитория
# (Сборка должна происходить из корня проекта: docker build -f python-service/Dockerfile .)
COPY sql/ /app/sql/

# Инициализация финального образа
FROM python:3.12-alpine

WORKDIR /app

RUN apk --no-cache add libpq

# Перенос виртуального окружения
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Перенос исходного кода
COPY --from=builder /app /app

EXPOSE 8080

# Запуск сервера веб-приложения
CMD ["python", "main.py"]
