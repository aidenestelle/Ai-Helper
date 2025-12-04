@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo    Helper AI - Quick Setup
echo ============================================
echo.
echo This script will:
echo   1. Create a virtual environment
echo   2. Install all dependencies
echo   3. Launch Helper AI
echo.
echo ============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Create venv if needed
if not exist ".venv" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

:: Activate and install
echo [*] Installing dependencies (this may take a minute)...
call .venv\Scripts\activate.bat

pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [NOTE] FFmpeg not found - voice input disabled.
    echo        Install with: winget install ffmpeg
    echo                  or: choco install ffmpeg
    echo.
)

:: Launch
echo ============================================
echo    Starting Helper AI...
echo ============================================
echo.
echo Press F2 to toggle the overlay!
echo.

.venv\Scripts\python.exe main.py
