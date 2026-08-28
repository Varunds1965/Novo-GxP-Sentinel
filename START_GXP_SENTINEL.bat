@echo off
REM Start GxP Sentinel application on Windows
REM This launcher starts the Flask web server at 127.0.0.1:8765
REM Then opens the Command Centre in the default browser

setlocal enabledelayedexpansion

REM Get the script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found at .venv\Scripts\activate.bat
    echo Please create it first: python -m venv .venv
    pause
    exit /b 1
)

REM Set Python path
set PYTHONPATH=%SCRIPT_DIR%backend

REM Check dependencies
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask not found. Installing dependencies...
    pip install -r requirements.txt
)

REM Start the server
echo Starting GxP Sentinel API server...
echo Application will be available at http://127.0.0.1:8765
echo Press Ctrl+C to stop the server
echo.

python -m app.api.app

pause
