@echo off
REM GxP Sentinel Local Edition - launcher. No developer tooling required.
title GxP Sentinel
cd /d "%~dp0"
where python >nul 2>nul || (
  echo.
  echo GxP Sentinel needs Python 3.12. It was not found on this computer.
  echo Install it from the Microsoft Store, then double-click this file again.
  echo.
  pause & exit /b 1
)
echo Starting GxP Sentinel...
python scripts\run_assessment.py
echo.
pause
