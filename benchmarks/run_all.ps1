# Benchmarking runner script (English version for encoding safety)
# Usage:
#   .\benchmarks\run_all.ps1                             -> both services
#   .\benchmarks\run_all.ps1 -Service golang-service     -> Go only
#   .\benchmarks\run_all.ps1 -Service python-service     -> Python only
param(
    [ValidateSet('python-service','golang-service','both')]
    [string]$Service = 'both'
)

$ScenarioNames = @("s1_browsing", "s2_orders", "s3_admin", "s4_analytics", "s5_mixed")
$ResultsDir = "benchmarks/results"

function Wait-ForHealthy($Service) {
    Write-Host "Waiting for service to be healthy..."
    $attempts = 0
    while ($attempts -lt 60) {
        $status = docker inspect --format='{{.State.Health.Status}}' $Service 2>$null
        if ($status -eq "healthy") {
            Write-Host "Service $Service is READY!" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
        $attempts++
    }
    Write-Host "WARNING: Service did not become healthy in time!" -ForegroundColor Red
}

function Run-Tests($Service, $LangKey) {
    Write-Host "`n>>> Starting test phase for $Service ($LangKey)..." -ForegroundColor Cyan

    foreach ($Scenario in $ScenarioNames) {
        Write-Host "`n--- Scenario: $Scenario ---" -ForegroundColor Yellow

        # Full reset before EVERY scenario: clean DB volumes + rebuild
        Write-Host "Resetting environment (clean database)..." -ForegroundColor DarkGray
        docker-compose down -v 2>$null
        docker-compose up -d $Service
        Wait-ForHealthy $Service

        # Run k6 test
        $OutputFile = "$ResultsDir/${Scenario}_$LangKey.json"
        docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run /app/benchmarks/scenarios/$Scenario.js --out json=/app/$OutputFile

        Write-Host "Done." -ForegroundColor Gray
        Read-Host "Press Enter to continue (Cooling break)..."
    }

    docker-compose down -v
}

# Cleanup: wipe all only for 'both'; otherwise remove only that service's files
if ($Service -eq 'both') {
    if (Test-Path $ResultsDir) { Remove-Item -Recurse $ResultsDir }
} else {
    $langKey = if ($Service -eq 'golang-service') { 'go' } else { 'py' }
    foreach ($s in $ScenarioNames) { Remove-Item -Force "$ResultsDir/${s}_$langKey.json" -ErrorAction SilentlyContinue }
}
New-Item -ItemType Directory -Path "$ResultsDir/charts" -Force | Out-Null

# Phase 1: Python
if ($Service -eq 'both' -or $Service -eq 'python-service') {
    Run-Tests "python-service" "py"
}

if ($Service -eq 'both') {
    Write-Host "`n========================================================" -ForegroundColor Magenta
    Write-Host "PHASE 1 (PYTHON) COMPLETE. LET THE COMPUTER COOL DOWN." -ForegroundColor Magenta
    Write-Host "Rest for 5-10 minutes is recommended." -ForegroundColor Magenta
    Write-Host "========================================================`n" -ForegroundColor Magenta
    Read-Host "Press Enter to start Phase 2 (Go testing)..."
}

# Phase 2: Go
if ($Service -eq 'both' -or $Service -eq 'golang-service') {
    Run-Tests "golang-service" "go"
}

# Post-processing
Write-Host "`n>>> Generating analytical reports..." -ForegroundColor Cyan
foreach ($Scenario in $ScenarioNames) {
    if (Test-Path "$ResultsDir/${Scenario}_go.json" -And Test-Path "$ResultsDir/${Scenario}_py.json") {
        python benchmarks/analyze.py --go "$ResultsDir/${Scenario}_go.json" --py "$ResultsDir/${Scenario}_py.json" --name $Scenario
    }
}

Write-Host "All tests complete! Check benchmarks/results/charts for PNG files." -ForegroundColor Green
