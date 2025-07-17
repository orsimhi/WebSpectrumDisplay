@echo off
setlocal enabledelayedexpansion

:: RF Spectrum Analyzer - Windows Development Setup
:: This script sets up a local development environment

echo ================================================================
echo    RF Spectrum Analyzer - Windows Development Setup
echo ================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from:
    echo https://www.python.org/downloads/windows/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

:: Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

:: Create virtual environment
echo.
echo Creating Python virtual environment...
if exist "venv" (
    echo Virtual environment already exists, removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Create logs directory
if not exist "logs" (
    mkdir logs
)

:: Check if PostgreSQL is available (for TimescaleDB)
echo.
echo Checking for PostgreSQL/TimescaleDB...
psql --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: PostgreSQL client not found in PATH
    echo For local development, you have two options:
    echo.
    echo 1. Install PostgreSQL with TimescaleDB extension locally
    echo 2. Use Docker for just the database:
    echo    docker run -d --name timescaledb -p 5432:5432 ^
    echo    -e POSTGRES_DB=rf_spectrum_db ^
    echo    -e POSTGRES_USER=rf_user ^
    echo    -e POSTGRES_PASSWORD=rf_password_123 ^
    echo    timescale/timescaledb:latest-pg15
    echo.
) else (
    echo PostgreSQL client found
)

:: Set environment variables for development
echo.
echo Setting up environment variables...
set DATABASE_URL=postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db
set FLASK_ENV=development
set PYTHONPATH=%CD%

:: Create a development environment file
echo # Development Environment Variables > .env
echo DATABASE_URL=postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db >> .env
echo FLASK_ENV=development >> .env
echo PYTHONPATH=%CD% >> .env

echo.
echo ================================================================
echo              Development Setup Complete!
echo ================================================================
echo.
echo To start the application:
echo   1. Activate virtual environment: venv\Scripts\activate.bat
echo   2. Ensure TimescaleDB is running (Docker or local install)
echo   3. Run: python app.py
echo.
echo To generate sample data:
echo   python sample_data_generator.py
echo.
echo Database connection:
echo   %DATABASE_URL%
echo.
echo The virtual environment is currently activated.
echo Would you like to start the database with Docker? (y/n)
set /p START_DB="Start TimescaleDB with Docker? (y/n): "

if /i "%START_DB%"=="y" (
    echo.
    echo Starting TimescaleDB container...
    docker run -d --name rf-timescaledb -p 5432:5432 ^
    -e POSTGRES_DB=rf_spectrum_db ^
    -e POSTGRES_USER=rf_user ^
    -e POSTGRES_PASSWORD=rf_password_123 ^
    -v "%CD%\init_db.sql:/docker-entrypoint-initdb.d/init_db.sql" ^
    timescale/timescaledb:latest-pg15
    
    echo.
    echo Waiting for database to start...
    timeout /t 10
    
    echo.
    echo Database should be ready. You can now run:
    echo   python app.py
)

echo.
echo Press any key to continue...
pause >nul