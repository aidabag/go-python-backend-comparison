# T2: Stress Test — поиск точки отказа (до 2000 VUs)
# Запуск: .\benchmarks\run_t2.ps1
param(
    [string]$BaseUrl = 'http://localhost:8080'
)

$Runs = 3
$ResultsBase = "benchmarks/results"

function Prompt-VPSReset($Service) {
    Write-Host "`n[VPS ACTION REQUIRED]" -ForegroundColor Red
    Write-Host "Please connect to VPS via SSH and run the following command:" -ForegroundColor Yellow
    Write-Host "  docker-compose down -v && docker-compose up -d $Service" -ForegroundColor Cyan
    Write-Host "Wait a few seconds for the database to seed." -ForegroundColor Yellow
    Read-Host "Press Enter HERE once the VPS service is ready..."
}

function Run-StressTest($Service, $LangKey) {
    Write-Host "`n>>> T2 Stress Test for $Service ($LangKey)" -ForegroundColor Cyan

    for ($run = 1; $run -le $Runs; $run++) {
        Write-Host "`n--- Stress | Run $run/$Runs ---" -ForegroundColor Yellow

        Prompt-VPSReset $Service

        $OutDir = "$ResultsBase/$LangKey/t2_stress"
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

        $OutputFile = "$OutDir/run$run.json"
        Write-Host "Running native k6 stress test..." -ForegroundColor White

        k6 run benchmarks/scenarios/t2_stress.js `
            --out json=$OutputFile `
            --env BASE_URL=$BaseUrl

        Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
        Read-Host "Press Enter to continue..."
    }

    Write-Host "Finished all runs for $Service." -ForegroundColor DarkGray
}

# --- PYTHON ---
Write-Host "========== T2 STRESS TEST ==========" -ForegroundColor Magenta
Run-StressTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-StressTest "golang-service" "go"

Write-Host "`nT2 Stress Test complete!" -ForegroundColor Green
