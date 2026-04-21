# test_golang.ps1

function Run-ApiTests {
    param ([string]$BaseUrl = "http://localhost:8080")

    Write-Host "`n--- ШАГ 1: ПРОВЕРКА СОСТОЯНИЯ (HEALTH CHECK) ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing

    Write-Host "`n--- ШАГ 2: МЕТРИКИ ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/metrics" -UseBasicParsing

    Write-Host "`n--- ШАГ 3: СОЗДАНИЕ ТОВАРА 1 ---" -ForegroundColor Cyan
    $p1_body = '{"name": "Laptop", "price": 100000, "stock": 50}'
    $p1 = Invoke-RestMethod -Uri "$BaseUrl/products" -Method Post -Body $p1_body -ContentType "application/json"
    $p1
    $p1Id = $p1.id

    Write-Host "`n--- ШАГ 4: СОЗДАНИЕ ТОВАРА 2 ---" -ForegroundColor Cyan
    $p2_body = '{"name": "Smartphone", "price": 50000, "stock": 100}'
    $p2 = Invoke-RestMethod -Uri "$BaseUrl/products" -Method Post -Body $p2_body -ContentType "application/json"
    $p2
    $p2Id = $p2.id

    Write-Host "`n--- ШАГ 5: СПИСОК ТОВАРОВ ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/products?limit=5" -UseBasicParsing

    Write-Host "`n--- ШАГ 6: СОЗДАНИЕ ЗАКАЗА 1 (Товар 1: 5 шт) ---" -ForegroundColor Cyan
    $o1_body = '{"items": [{"product_id": ' + $p1Id + ', "quantity": 5}]}'
    $o1 = Invoke-RestMethod -Uri "$BaseUrl/orders" -Method Post -Body $o1_body -ContentType "application/json"
    $o1
    $o1Id = $o1.id

    Write-Host "`n--- ШАГ 7: ПРОВЕРКА ОСТАТКОВ (ТОВАР 1, ожидается 45) ---" -ForegroundColor Cyan
    Invoke-RestMethod -Uri "$BaseUrl/products/$p1Id"

    Write-Host "`n--- ШАГ 8: СОЗДАНИЕ ЗАКАЗА 2 (Товар 2: 1 шт) ---" -ForegroundColor Cyan
    $o2_body = '{"items": [{"product_id": ' + $p2Id + ', "quantity": 1}]}'
    $o2 = Invoke-RestMethod -Uri "$BaseUrl/orders" -Method Post -Body $o2_body -ContentType "application/json"
    $o2
    $o2Id = $o2.id

    Write-Host "`n--- ШАГ 9: ПРОВЕРКА ОСТАТКОВ (ТОВАР 2, ожидается 99) ---" -ForegroundColor Cyan
    Invoke-RestMethod -Uri "$BaseUrl/products/$p2Id"

    Write-Host "`n--- ШАГ 10: СОЗДАНИЕ ЗАКАЗА 3 (Смешанный) ---" -ForegroundColor Cyan
    $o3_body = '{"items": [{"product_id": ' + $p1Id + ', "quantity": 1}, {"product_id": ' + $p2Id + ', "quantity": 2}]}'
    $o3 = Invoke-RestMethod -Uri "$BaseUrl/orders" -Method Post -Body $o3_body -ContentType "application/json"
    $o3
    $o3Id = $o3.id

    Write-Host "`n--- ШАГ 11: ФИНАЛЬНЫЕ ОСТАТКИ ---" -ForegroundColor Cyan
    Write-Host "Товар 1:"
    Invoke-RestMethod -Uri "$BaseUrl/products/$p1Id"
    Write-Host "Товар 2:"
    Invoke-RestMethod -Uri "$BaseUrl/products/$p2Id"

    Write-Host "`n--- ШАГ 12: ИТОГО ПО ЗАКАЗУ 3 ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/orders/$o3Id/total" -UseBasicParsing

    Write-Host "`n--- ШАГ 13: СВОДКА ПО ЗАКАЗУ 3 ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/orders/$o3Id/summary" -UseBasicParsing

    Write-Host "`n--- ШАГ 14: АНАЛИТИКА (СРЕДНИЙ ЧЕК) ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/analytics/orders/average" -UseBasicParsing

    Write-Host "`n--- ШАГ 15: АНАЛИТИКА (ТОП ТОВАРОВ) ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/analytics/products/top?limit=3" -UseBasicParsing

    Write-Host "`n--- ШАГ 16: ОБНОВЛЕНИЕ ТОВАРА ---" -ForegroundColor Cyan
    $upd_body = '{"name": "Laptop Pro", "price": 110000, "stock": 44}'
    Invoke-RestMethod -Uri "$BaseUrl/products/$p1Id" -Method Put -Body $upd_body -ContentType "application/json"

    Write-Host "`n--- ШАГ 17: УДАЛЕНИЕ ПОЗИЦИИ ИЗ ЗАКАЗА 3 ---" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BaseUrl/orders/$o3Id/items/$p1Id" -Method Delete -UseBasicParsing
    Write-Host "Остаток после восстановления:"
    Invoke-RestMethod -Uri "$BaseUrl/products/$p1Id"

    Write-Host "`n--- ШАГ 18: ТЕСТ ОШИБКИ УДАЛЕНИЯ ---" -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri "$BaseUrl/products/$p2Id" -Method Delete -UseBasicParsing -ErrorAction Stop
    } catch {
        if ($_.Exception.Response) { $_.Exception.Response } else { $_.Exception.Message }
    }
}

# SETUP
docker-compose down -v
docker-compose up -d golang-service

Write-Host "Ожидание запуска сервиса..." -NoNewline
while ($true) {
    try {
        $check = Invoke-RestMethod "http://localhost:8080/health" -ErrorAction SilentlyContinue
        if ($check.status -eq "ok") { break }
    } catch {}
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 2
}
Write-Host " ГОТОВО!" -ForegroundColor Green

Run-ApiTests
