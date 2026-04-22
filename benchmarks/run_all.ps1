# Регламентация процедур запуска бенчмарков (PowerShell)
# Обеспечение выполнения полного цикла испытаний для обеих программных реализаций и генерация отчетных материалов.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScenarioNames = @("s1_browsing", "s2_orders", "s3_admin", "s4_analytics", "s5_mixed")
$ResultsDir = "benchmarks/results"

function Run-Tests($Service, $LangKey) {
    Write-Host "Инициализация тестирования для $Service ($LangKey)..." -ForegroundColor Cyan
    
    # Активация контейнера сервиса с предварительной очисткой
    docker-compose down -v
    docker-compose up -d $Service
    
    Write-Host "Ожидание перехода сервиса в состояние healthy..."
    while ($(docker inspect --format='{{.State.Health.Status}}' $Service) -ne "healthy") {
        Start-Sleep -Seconds 2
    }
    Write-Host "Готовность сервиса $Service подтверждена!" -ForegroundColor Green

    # Исполнение тестовых сценариев
    foreach ($Scenario in $ScenarioNames) {
        $OutputFile = "$ResultsDir/$Scenario`_$LangKey.json"
        Write-Host "--- Выполнение сценария: $Scenario ---" -ForegroundColor Yellow
        
        # Инициация k6 в изолированной среде Docker
        docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run /app/benchmarks/scenarios/$Scenario.js --out json=/app/$OutputFile
        
        Write-Host "Сценарий завершен." -ForegroundColor Gray
        Read-Host "Нажмите Enter для перехода к следующему этапу..."
    }
    
    docker-compose down -v
}

# Деструкция результатов предыдущих циклов тестирования
if (Test-Path $ResultsDir) { Remove-Item -Recurse $ResultsDir }
New-Item -ItemType Directory -Path "$ResultsDir/charts"

# Цикл тестирования Python (Первый этап)
Run-Tests "python-service" "py"

Write-Host "`n========================================================" -ForegroundColor Magenta
Write-Host "ПЕРВЫЙ ЭТАП (PYTHON) ЗАВЕРШЕН" -ForegroundColor Magenta
Write-Host "Рекомендуется технологический перерыв 5-10 минут." -ForegroundColor Magenta
Write-Host "========================================================`n" -ForegroundColor Magenta
Read-Host "Нажмите Enter для начала второго этапа (тестирование Go)..."

# Цикл тестирования Go (Второй этап)
Run-Tests "golang-service" "go"

# Аналитическая обработка полученного массива данных
Write-Host "`n>>> Генерация аналитических отчетов и графических материалов..." -ForegroundColor Cyan
foreach ($Scenario in $ScenarioNames) {
    if (Test-Path "$ResultsDir/$Scenario`_go.json" -And Test-Path "$ResultsDir/$Scenario`_py.json") {
        python benchmarks/analyze.py --go "$ResultsDir/$Scenario`_go.json" --py "$ResultsDir/$Scenario`_py.json" --name $Scenario
    }
}

Write-Host "Тестирование успешно завершено! Отчеты доступны в benchmarks/results/charts." -ForegroundColor Green
