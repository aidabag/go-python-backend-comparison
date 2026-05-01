# T5: Mixed Production Load — итоговый контрольный тест
# Запуск: .\benchmarks\run_t5.ps1
param(
    [string]$BaseUrl = 'http://localhost:8080'
)

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

function Run-MixedTest($Service, $LangKey) {
    Write-Host "`n>>> T5 Mixed Production Load for $Service ($LangKey)" -ForegroundColor Cyan

    for ($run = 1; $run -le $Runs; $run++) {
        Write-Host "`n--- Mixed | Run $run/$Runs ---" -ForegroundColor Yellow

        docker-compose down -v 2>$null
        docker-compose up -d $Service
        Wait-ForHealthy $Service

        $OutDir = "$ResultsBase/$LangKey/t5_mixed"
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

        $OutputFile = "$OutDir/run$run.json"
        Write-Host "Running k6 mixed test..." -ForegroundColor White

        docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run `
            /app/benchmarks/scenarios/t5_mixed.js `
            --out json=/app/$OutputFile `
            --env BASE_URL=$BaseUrl

        Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
        Read-Host "Press Enter to continue..."
    }

    docker-compose down -v
}

# --- PYTHON ---
Write-Host "========== T5 MIXED PRODUCTION LOAD ==========" -ForegroundColor Magenta
Run-MixedTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-MixedTest "golang-service" "go"

Write-Host "`nT5 Mixed Production Load complete!" -ForegroundColor Green
