@echo off
echo.
echo ============================================
echo   Voice Generator - Setup Script
echo   AI Text-to-Speech for YouTube
echo ============================================
echo.

REM Check Python version
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Installing espeak-ng (required for Kokoro TTS)...
echo.
echo ========================================
echo  IMPORTANT: Install espeak-ng manually!
echo ========================================
echo.
echo 1. Go to: https://github.com/espeak-ng/espeak-ng/releases
echo 2. Download: espeak-ng-X64.msi (latest version)
echo 3. Run the installer
echo.
echo Press any key after installing espeak-ng...
pause > nul

echo [3/4] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Setup complete!
echo.
echo ============================================
echo   To start the app, run:
echo   start.bat
echo ============================================
echo.
pause
