@echo off
echo Nexhan Nova (Don) Self-Check Runner
echo ==================================

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Activated virtual environment
) else (
    echo Virtual environment not found, using system Python
)

REM Run self-check
echo Running self-check...
python -c "from don.self_check import run_self_check_and_report; run_self_check_and_report()"

echo.
echo Self-check completed.
pause