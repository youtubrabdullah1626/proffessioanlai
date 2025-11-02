# Nexhan Nova (Don) Self-Check Runner

Write-Host "Nexhan Nova (Don) Self-Check Runner" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
    Write-Host "Activated virtual environment" -ForegroundColor Yellow
} else {
    Write-Host "Virtual environment not found, using system Python" -ForegroundColor Yellow
}

# Run self-check
Write-Host "Running self-check..." -ForegroundColor Cyan
python -c "from don.self_check import run_self_check_and_report; run_self_check_and_report()"

Write-Host ""
Write-Host "Self-check completed." -ForegroundColor Green
Write-Host "Press any key to continue..." -ForegroundColor Gray
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")