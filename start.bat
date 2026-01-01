@echo off
echo.
echo ========================================
echo   Voice Generator - Starting...
echo ========================================
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the server
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
