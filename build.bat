@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo    Helper AI - Build Executable
echo ============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

:: Activate venv
call .venv\Scripts\activate.bat

:: Install PyInstaller if not present
echo [*] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller ready

:: Build the executable
echo.
echo [*] Building executable...
echo    This may take a few minutes...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "HelperAI" ^
    --add-data "settings.json;." ^
    --add-data "config.py;." ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "whisper" ^
    --hidden-import "sounddevice" ^
    --hidden-import "scipy" ^
    --hidden-import "numpy" ^
    --collect-all "customtkinter" ^
    --collect-all "whisper" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Build Complete!
echo ============================================
echo.
echo Executable created in: dist\HelperAI\
echo Run: dist\HelperAI\HelperAI.exe
echo.
echo Note: You can copy the entire HelperAI folder
echo       to any location and run the exe from there.
echo.
pause
