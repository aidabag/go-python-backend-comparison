# T5: Mixed Production Load — итоговый контрольный тест
# Запуск: .\benchmarks\run_t5.ps1
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

function Run-MixedTest($Service, $LangKey) {
    Write-Host "`n>>> T5 Mixed Production Load for $Service ($LangKey)" -ForegroundColor Cyan

    for ($run = 1; $run -le $Runs; $run++) {
        Write-Host "`n--- Mixed | Run $run/$Runs ---" -ForegroundColor Yellow

        Prompt-VPSReset $Service

        $OutDir = "$ResultsBase/$LangKey/t5_mixed"
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

        $OutputFile = "$OutDir/run$run.json"
        Write-Host "Running native k6 mixed test..." -ForegroundColor White

        k6 run benchmarks/scenarios/t5_mixed.js `
            --out json=$OutputFile `
            --env BASE_URL=$BaseUrl

        Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
        Read-Host "Press Enter to continue..."
    }

    Write-Host "Finished all runs for $Service." -ForegroundColor DarkGray
}

# --- PYTHON ---
Write-Host "========== T5 MIXED PRODUCTION LOAD ==========" -ForegroundColor Magenta
Run-MixedTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-MixedTest "golang-service" "go"

Write-Host "`nT5 Mixed Production Load complete!" -ForegroundColor Green
