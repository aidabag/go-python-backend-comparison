# T4: Scalability Test — вертикальная масштабируемость (1/2/4 CPU)
# Запуск: .\benchmarks\run_t4.ps1
param(
    [string]$BaseUrl = 'http://localhost:8080'
)

$Runs = 2
$ResultsBase = "benchmarks/results"

# Конфигурации масштабируемости: CPU → VUs → Workers (Python)
$ScaleConfigs = @(
    @{ Cpus = "1.0"; Vus = 50; Workers = 1; Label = "1cpu" },
    @{ Cpus = "2.0"; Vus = 100; Workers = 2; Label = "2cpu" },
    @{ Cpus = "4.0"; Vus = 200; Workers = 4; Label = "4cpu" }
)

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

function Run-ScaleTest($Service, $LangKey) {
    Write-Host "`n>>> T4 Scalability Test for $Service ($LangKey)" -ForegroundColor Cyan

    foreach ($cfg in $ScaleConfigs) {
        $cpus = $cfg.Cpus
        $vus = $cfg.Vus
        $workers = $cfg.Workers
        $label = $cfg.Label

        for ($run = 1; $run -le $Runs; $run++) {
            Write-Host "`n--- Scale $label ($cpus CPU, $vus VUs) | Run $run/$Runs ---" -ForegroundColor Yellow

            # Установка переменных окружения для docker-compose
            $env:APP_CPUS = $cpus
            $env:WORKERS = $workers

            docker-compose down -v 2>$null
            docker-compose up -d $Service
            Wait-ForHealthy $Service

            $OutDir = "$ResultsBase/$LangKey/t4_scale/$label"
            New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

            $OutputFile = "$OutDir/run$run.json"
            Write-Host "Running k6 (SCALE_VUS=$vus, CPU=$cpus)..." -ForegroundColor White

            docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run `
                /app/benchmarks/scenarios/t4_scale.js `
                --out json=/app/$OutputFile `
                --env BASE_URL=$BaseUrl `
                --env SCALE_VUS=$vus

            Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
            Read-Host "Press Enter to continue..."
        }
    }

    # Восстановление значений по умолчанию
    $env:APP_CPUS = "4.0"
    $env:WORKERS = "4"
    docker-compose down -v
}

# --- PYTHON ---
Write-Host "========== T4 SCALABILITY TEST ==========" -ForegroundColor Magenta
Run-ScaleTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-ScaleTest "golang-service" "go"

Write-Host "`nT4 Scalability Test complete!" -ForegroundColor Green
