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

function Prompt-VPSReset($Service, $Cpus, $Workers) {
    Write-Host "`n[VPS ACTION REQUIRED - SCALING TEST]" -ForegroundColor Red
    Write-Host "Please connect to VPS via SSH and run the following command to scale to $Cpus CPUs:" -ForegroundColor Yellow
    Write-Host "  export APP_CPUS=$Cpus && export WORKERS=$Workers && docker-compose down -v && docker-compose up -d $Service" -ForegroundColor Cyan
    Write-Host "Wait a few seconds for the database to seed." -ForegroundColor Yellow
    Read-Host "Press Enter HERE once the VPS service is ready..."
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

            # Сбрасываем и масштабируем VPS
            Prompt-VPSReset $Service $cpus $workers

            $OutDir = "$ResultsBase/$LangKey/t4_scale/$label"
            New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

            $OutputFile = "$OutDir/run$run.json"
            Write-Host "Running native k6 (SCALE_VUS=$vus, CPU=$cpus)..." -ForegroundColor White

            k6 run benchmarks/scenarios/t4_scale.js `
                --out json=$OutputFile `
                --env BASE_URL=$BaseUrl `
                --env SCALE_VUS=$vus

            Write-Host "Run $run done. Results: $OutputFile" -ForegroundColor Gray
            Read-Host "Press Enter to continue..."
        }
    }

    Write-Host "Finished all scale runs for $Service." -ForegroundColor DarkGray
}

# --- PYTHON ---
Write-Host "========== T4 SCALABILITY TEST ==========" -ForegroundColor Magenta
Run-ScaleTest "python-service" "python"

Write-Host "`n===== PYTHON DONE. REST BEFORE GO =====" -ForegroundColor Magenta
Read-Host "Press Enter to start Go testing..."

# --- GO ---
Run-ScaleTest "golang-service" "go"

Write-Host "`nT4 Scalability Test complete!" -ForegroundColor Green
