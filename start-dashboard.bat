@echo off
REM WSU Migration Verification Dashboard - Setup Script
REM This script installs dependencies and starts the dashboard

echo.
echo ========================================
echo WSU Migration Verification Dashboard
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

echo.
echo [2/4] Installing dependencies...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully

echo.
echo [3/4] Installing Playwright Chromium browser...
python -m playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install Playwright Chromium
    pause
    exit /b 1
)
echo Playwright Chromium installed successfully

echo.
echo [4/4] Starting Dashboard...
echo.
echo Opening dashboard at http://localhost:5000
echo.
echo Dashboard ready! Press Ctrl+C to stop.
echo.

python app.py

pause
