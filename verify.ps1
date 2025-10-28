param()

Write-Host "[verify] Creating venv if missing..."
if (-not (Test-Path .venv)) {
	python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host "[verify] Installing requirements..."
pip install -r requirements.txt | Out-Null

Write-Host "[verify] Running unit tests..."
pytest -q

if ($LASTEXITCODE -eq 0) {
	Write-Host "[verify] All tests passed." -ForegroundColor Green
	exit 0
} else {
	Write-Host "[verify] Tests failed." -ForegroundColor Red
	exit 1
}
