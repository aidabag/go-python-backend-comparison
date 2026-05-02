# T1: Load Test — 4 бизнес-сценария (S1-S4)
# Запуск: .\benchmarks\run_t1.ps1
# Порядок: Python (3 прогона × 4 сценария) → Go (3 прогона × 4 сценария)
param(
    [string]$BaseUrl = 'http://localhost:8080'
)

$Scenarios = @("browsing", "orders", "admin", "analytics")
$Runs = 3
$ResultsBase = "benchmarks/results"

function Prompt-VPSReset($Service) {
    Write-Host "`n[VPS ACTION REQUIRED]" -ForegroundColor Red
    Write-Host "Please connect to VPS via SSH and run the following command:" -ForegroundColor Yellow
    Write-Host "  docker-compose down -v && docker-compose up -d $Service" -ForegroundColor Cyan
    Write-Host "Wait a few seconds for the database to seed." -ForegroundColor Yellow
    Read-Host "Press Enter HERE once the VPS service is ready..."
}

function Run-LoadTest($Service, $LangKey) {
    Write-Host "`n>>> T1 Load Test for $Service ($LangKey)" -ForegroundColor Cyan

    foreach ($Scenario in $Scenarios) {
        for ($run = 1; $run -le $Runs; $run++) {
            Write-Host "`n--- $Scenario | Run $run/$Runs ---" -ForegroundColor Yellow

            # Просим пользователя сбросить БД на VPS
            Prompt-VPSReset $Service

            # Создание директории для результатов
            $OutDir = "$ResultsBase/$LangKey/t1_load/s_$Scenario"
            New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

            $OutputFile = "$OutDir/run$run.json"
            Write-Host "Running native k6 (SCENARIO=$Scenario)..." -ForegroundColor White

            k6 run benchmarks/scenarios/t1_load.js `
                --out json=$OutputFile `
                --env BASE_URL=$BaseUrl `
                --env SCENARIO=$Scenario

            Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
            Read-Host "Press Enter to continue..."
        }
    }

    Write-Host "Finished all runs for $Service." -ForegroundColor DarkGray
}

# --- PYTHON ---
Write-Host "========== T1 LOAD TEST ==========" -ForegroundColor Magenta
Run-LoadTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-LoadTest "golang-service" "go"

Write-Host "`nT1 Load Test complete!" -ForegroundColor Green
