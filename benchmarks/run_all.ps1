# Benchmarking runner script (English version for encoding safety)
$ScenarioNames = @("s1_browsing", "s2_orders", "s3_admin", "s4_analytics", "s5_mixed")
$ResultsDir = "benchmarks/results"

function Run-Tests($Service, $LangKey) {
    Write-Host "`n>>> Initializing tests for $Service ($LangKey)..." -ForegroundColor Cyan
    
    # Restart containers with volume cleanup
    docker-compose down -v
    docker-compose up -d $Service
    
    Write-Host "Waiting for service to be healthy..."
    while ($(docker inspect --format='{{.State.Health.Status}}' $Service) -ne "healthy") {
        Start-Sleep -Seconds 2
    }
    Write-Host "Service $Service is READY!" -ForegroundColor Green

    # Execute scenarios
    foreach ($Scenario in $ScenarioNames) {
        $OutputFile = "$ResultsDir/${Scenario}_$LangKey.json"
        Write-Host "--- Running scenario: $Scenario ---" -ForegroundColor Yellow
        
        # Run k6 via Docker
        docker run --rm --network host -v ${PWD}:/app -i grafana/k6 run /app/benchmarks/scenarios/$Scenario.js --out json=/app/$OutputFile
        
        Write-Host "Done." -ForegroundColor Gray
        Read-Host "Press Enter to continue (Cooling break)..."
    }
    
    docker-compose down -v
}

# Cleanup old results
if (Test-Path $ResultsDir) { Remove-Item -Recurse $ResultsDir }
New-Item -ItemType Directory -Path "$ResultsDir/charts"

# Phase 1: Python
Run-Tests "python-service" "py"

Write-Host "`n========================================================" -ForegroundColor Magenta
Write-Host "PHASE 1 (PYTHON) COMPLETE. LET THE COMPUTER COOL DOWN." -ForegroundColor Magenta
Write-Host "Rest for 5-10 minutes is recommended." -ForegroundColor Magenta
Write-Host "========================================================`n" -ForegroundColor Magenta
Read-Host "Press Enter to start Phase 2 (Go testing)..."

# Phase 2: Go
Run-Tests "golang-service" "go"

# Post-processing
Write-Host "`n>>> Generating analytical reports..." -ForegroundColor Cyan
foreach ($Scenario in $ScenarioNames) {
    if (Test-Path "$ResultsDir/${Scenario}_go.json" -And Test-Path "$ResultsDir/${Scenario}_py.json") {
        python benchmarks/analyze.py --go "$ResultsDir/${Scenario}_go.json" --py "$ResultsDir/${Scenario}_py.json" --name $Scenario
    }
}

Write-Host "All tests complete! Check benchmarks/results/charts for PNG files." -ForegroundColor Green
