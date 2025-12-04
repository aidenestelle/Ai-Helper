@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo    Helper AI - Build Executable
echo ============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Detect Python environment
set PYTHON_EXE=
set PYTHON_DIR=

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
    set PYTHON_DIR=.venv\Scripts
    call .venv\Scripts\activate.bat
    echo [OK] Using venv environment
) else (
    :: Try conda
    where conda >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No Python environment found.
        echo Please run install.bat first or activate your conda environment.
        pause
        exit /b 1
    )
    call conda activate helper-ai 2>nul
    if errorlevel 1 (
        echo [ERROR] Could not activate helper-ai conda environment.
        echo Please run: conda activate helper-ai
        pause
        exit /b 1
    )
    echo [OK] Using conda environment
)

:: Kill any running HelperAI processes
echo [*] Checking for running instances...
taskkill /f /im HelperAI.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Clean up old build artifacts and spec file
echo [*] Cleaning previous build...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "HelperAI.spec" del /f "HelperAI.spec" 2>nul
timeout /t 1 /nobreak >nul

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

:: Check for Anaconda DLLs
set CONDA_BIN=F:\anaconda\Library\bin
if exist "!CONDA_BIN!\ffi-8.dll" (
    echo [OK] Found Anaconda DLLs - will bundle them
) else (
    echo [WARNING] Anaconda DLLs not found at !CONDA_BIN!
)

:: Use --onedir mode for better compatibility
:: Include all required Anaconda DLLs directly
pyinstaller --noconfirm --onedir --windowed ^
    --name "HelperAI" ^
    --add-data "config.py;." ^
    --add-binary "F:\anaconda\Library\bin\ffi-8.dll;." ^
    --add-binary "F:\anaconda\Library\bin\ffi.dll;." ^
    --add-binary "F:\anaconda\Library\bin\tcl86t.dll;." ^
    --add-binary "F:\anaconda\Library\bin\tk86t.dll;." ^
    --add-binary "F:\anaconda\Library\bin\liblzma.dll;." ^
    --add-binary "F:\anaconda\Library\bin\libbz2.dll;." ^
    --add-binary "F:\anaconda\Library\bin\libcrypto-3-x64.dll;." ^
    --add-binary "F:\anaconda\Library\bin\libssl-3-x64.dll;." ^
    --add-binary "F:\anaconda\Library\bin\libexpat.dll;." ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "PIL._imagingtk" ^
    --hidden-import "PIL._imaging" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "whisper" ^
    --hidden-import "sounddevice" ^
    --hidden-import "scipy" ^
    --hidden-import "scipy.signal" ^
    --hidden-import "numpy" ^
    --hidden-import "ctypes" ^
    --hidden-import "_ctypes" ^
    --hidden-import "keyboard" ^
    --hidden-import "keyboard._winkeyboard" ^
    --hidden-import "tiktoken_ext" ^
    --hidden-import "tiktoken_ext.openai_public" ^
    --collect-all "customtkinter" ^
    --collect-all "whisper" ^
    --collect-all "keyboard" ^
    --collect-all "PIL" ^
    --collect-binaries "numpy" ^
    --collect-binaries "ctypes" ^
    --collect-binaries "PIL" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    echo.
    echo Common fixes:
    echo   1. Disable antivirus temporarily
    echo   2. Close any running HelperAI.exe
    echo   3. Run as Administrator
    echo   4. Try: pip install --upgrade pyinstaller
    echo.
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
echo Note: Copy the entire HelperAI folder to distribute.
echo.
pause
