@echo off
setlocal

:: Change to script directory
cd /d "%~dp0"

:: Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

:: Start the application
echo Starting Helper AI...
echo Press F2 to toggle the overlay (or your configured hotkey)
echo.

.venv\Scripts\python.exe main.py

:: If python exits with error
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
