@echo off
title Local Lab - AI Voice Generator
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║         🎙️  LOCAL LAB - AI VOICE GENERATOR  🎙️              ║
echo  ║                                                              ║
echo  ║         Free AI Text-to-Speech for YouTube                   ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

REM Change to script directory
cd /d "%~dp0"

REM ========================================
REM STEP 1: Check Python
REM ========================================
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ⚠️  Python is NOT installed!
    echo.
    echo  Opening Python download page...
    echo  Please install Python and CHECK "Add to PATH" during installation!
    echo.
    start https://www.python.org/downloads/
    echo  After installing Python, run this file again.
    echo.
    pause
    exit /b 1
)
echo ✅ Python found!

REM ========================================
REM STEP 2: Setup Virtual Environment
REM ========================================
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [2/4] First time setup - Creating virtual environment...
    echo      This may take a few minutes...
    echo.
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo [3/4] Installing dependencies...
    pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    
    echo.
    echo [4/4] Downloading AI voice data (first time only)...
    python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"
    
    echo.
    echo ✅ Setup complete!
) else (
    echo [2/4] Virtual environment found ✅
    call venv\Scripts\activate.bat
    echo [3/4] Dependencies ready ✅
    echo [4/4] AI models ready ✅
)

REM ========================================
REM STEP 3: Start the App
REM ========================================
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo  🚀 Starting Local Lab Voice Generator...
echo.
echo  📌 Your app will open at: http://localhost:8000
echo.
echo  💡 TIP: Keep this window open while using the app!
echo  ❌ To stop: Close this window or press Ctrl+C
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM Wait 2 seconds then open browser
timeout /t 2 /nobreak >nul
start http://localhost:8000

REM Start the server
python app.py

pause
