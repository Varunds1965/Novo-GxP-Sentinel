@echo off
REM Run a complete GxP Sentinel assessment
REM This launcher executes the offline assessment pipeline

setlocal enabledelayedexpansion

REM Get the script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found
    pause
    exit /b 1
)

REM Set Python path
set PYTHONPATH=%SCRIPT_DIR%backend

REM Run assessment
echo Running GxP Sentinel assessment...
echo.
python scripts/run_assessment.py

echo.
echo Assessment complete. Results are in docs/evidence/
pause
