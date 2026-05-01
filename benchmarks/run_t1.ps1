# T1: Load Test — 4 бизнес-сценария (S1-S4)
# Запуск: .\benchmarks\run_t1.ps1
# Порядок: Python (3 прогона × 4 сценария) → Go (3 прогона × 4 сценария)
param(
    [string]$BaseUrl = 'http://localhost:8080'
)

$Scenarios = @("browsing", "orders", "admin", "analytics")
$Runs = 3
$ResultsBase = "benchmarks/results"

function Wait-ForHealthy($Service) {
    Write-Host "Waiting for $Service to be healthy..." -ForegroundColor DarkGray
    $attempts = 0
    while ($attempts -lt 60) {
        $status = docker inspect --format='{{.State.Health.Status}}' $Service 2>$null
        if ($status -eq "healthy") {
            Write-Host "$Service is READY!" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
        $attempts++
    }
    Write-Host "WARNING: $Service did not become healthy in time!" -ForegroundColor Red
}

function Run-LoadTest($Service, $LangKey) {
    Write-Host "`n>>> T1 Load Test for $Service ($LangKey)" -ForegroundColor Cyan

    foreach ($Scenario in $Scenarios) {
        for ($run = 1; $run -le $Runs; $run++) {
            Write-Host "`n--- $Scenario | Run $run/$Runs ---" -ForegroundColor Yellow

            # Полный сброс БД перед каждым прогоном
            Write-Host "Resetting environment..." -ForegroundColor DarkGray
            docker-compose down -v 2>$null
            docker-compose up -d $Service
            Wait-ForHealthy $Service

            # Создание директории для результатов
            $OutDir = "$ResultsBase/$LangKey/t1_load/s_$Scenario"
            New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

            $OutputFile = "$OutDir/run$run.json"
            Write-Host "Running k6 (SCENARIO=$Scenario)..." -ForegroundColor White

            docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run `
                /app/benchmarks/scenarios/t1_load.js `
                --out json=/app/$OutputFile `
                --env BASE_URL=$BaseUrl `
                --env SCENARIO=$Scenario

            Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
            Read-Host "Press Enter to continue..."
        }
    }

    docker-compose down -v
}

# --- PYTHON ---
Write-Host "========== T1 LOAD TEST ==========" -ForegroundColor Magenta
Run-LoadTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-LoadTest "golang-service" "go"

Write-Host "`nT1 Load Test complete!" -ForegroundColor Green
