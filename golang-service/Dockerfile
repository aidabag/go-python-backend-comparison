# Подготовка сборочного образа
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Копирование файлов конфигурации модулей
COPY golang-service/go.mod golang-service/go.sum ./
RUN go mod download

# Копирование исходного кода приложения
COPY golang-service/ .

# Сборка исполняемого бинарного файла
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

# Копирование общих SQL файлов монорепозитория 
# (Важно: сборка должна происходить из корня проекта: docker build -f golang-service/Dockerfile .)
COPY sql/ /app/sql/

# Инициализация финального образа
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Перенос бинарного файла из сборочного окружения
COPY --from=builder /app/server .
# Перенос директории с SQL скриптами для работы приложения
COPY --from=builder /app/sql ./sql

EXPOSE 8080

# Запуск сервера веб-приложения
CMD ["sh", "-c", "GOMAXPROCS=4 ./server"]
