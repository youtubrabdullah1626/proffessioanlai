param()

Write-Host "[verify] Creating venv if missing..."
if (-not (Test-Path .venv)) {
	python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host "[verify] Installing requirements..."
pip install -r requirements.txt | Out-Null
pip install pyflakes ruff | Out-Null

Write-Host "[verify] Static checks..."
python -m pyflakes .
ruff check .

Write-Host "[verify] Running unit tests..."
pytest -q

Write-Host "[verify] Running exec smoke..."
python scripts/test_exec.py

if ($LASTEXITCODE -eq 0) {
	Write-Host "[verify] All checks passed." -ForegroundColor Green
	exit 0
} else {
	Write-Host "[verify] Checks failed." -ForegroundColor Red
	exit 1
}
