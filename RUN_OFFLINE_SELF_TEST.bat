@echo off
title GxP Sentinel - Offline Self Test
cd /d "%~dp0"
python scripts\offline_self_test.py
echo.
pause
