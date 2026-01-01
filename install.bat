@echo off
echo.
echo ========================================
echo   IndexerAPI - Installation
echo ========================================
echo.

REM Check Python version
python --version 2>NUL
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate and install
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e ".[dev]"

REM Copy example env
if not exist .env (
    echo Creating .env from example...
    copy .env.example .env
)

REM Create data directory
if not exist data mkdir data

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To get started:
echo   1. Edit .env with your settings
echo   2. Run: run.bat
echo.
pause
