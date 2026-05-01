#!/bin/bash
# Мониторинг потребления ресурсов контейнером (CPU / RAM)
# Использование: ./monitor_resources.sh <container_name> <output_file>
# Пример: ./monitor_resources.sh golang-service results/go/t1_load/resources_run1.csv

CONTAINER=$1
OUTPUT=$2

if [ -z "$CONTAINER" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <container_name> <output_file>"
    exit 1
fi

# Создание директории для выходного файла
mkdir -p "$(dirname "$OUTPUT")"

# Заголовок CSV-файла
echo "timestamp,cpu_percent,mem_usage_mb,mem_limit_mb" > "$OUTPUT"

# Сбор метрик каждую секунду до завершения скрипта (Ctrl+C)
while true; do
    STATS=$(docker stats "$CONTAINER" --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" 2>/dev/null)
    if [ -z "$STATS" ]; then
        sleep 1
        continue
    fi

    TIMESTAMP=$(date +%s)
    # Парсинг: "45.23%,312.5MiB / 3GiB" → "45.23,312.5,3072"
    CPU=$(echo "$STATS" | cut -d',' -f1 | tr -d '%')
    MEM_RAW=$(echo "$STATS" | cut -d',' -f2)
    MEM_USED=$(echo "$MEM_RAW" | awk -F'/' '{gsub(/[^0-9.]/, "", $1); print $1}')
    MEM_LIMIT=$(echo "$MEM_RAW" | awk -F'/' '{gsub(/[^0-9.]/, "", $2); print $2}')

    echo "${TIMESTAMP},${CPU},${MEM_USED},${MEM_LIMIT}" >> "$OUTPUT"
    sleep 1
done
