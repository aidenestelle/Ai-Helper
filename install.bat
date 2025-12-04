@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo    Helper AI - Installation Script
echo ============================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version

:: Check if venv exists, create if not
if not exist ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

:: Activate venv and install dependencies
echo.
echo [*] Installing dependencies...
call .venv\Scripts\activate.bat

pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!

:: Check for FFmpeg (required for voice input)
echo.
echo [*] Checking for FFmpeg (required for voice input)...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found. Voice input will not work.
    echo To install FFmpeg:
    echo   - Windows: winget install ffmpeg
    echo   - Or download from https://ffmpeg.org/download.html
    echo.
) else (
    echo [OK] FFmpeg found
)

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo To start Helper AI, run: start.bat
echo Or double-click start.bat
echo.
pause
