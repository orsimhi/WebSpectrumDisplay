@echo off
setlocal

:: RF Spectrum Analyzer - Quick Run Script for Windows

echo ================================================================
echo        RF Spectrum Analyzer - Starting Application
echo ================================================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup_dev.bat first to set up the development environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Set environment variables
set DATABASE_URL=postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db
set FLASK_ENV=development
set PYTHONPATH=%CD%

:: Check if database is running
echo Checking database connection...
python -c "import psycopg2; psycopg2.connect('postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db')" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Cannot connect to TimescaleDB
    echo Please ensure the database is running. You can start it with:
    echo   docker run -d --name rf-timescaledb -p 5432:5432 ^
    echo   -e POSTGRES_DB=rf_spectrum_db ^
    echo   -e POSTGRES_USER=rf_user ^
    echo   -e POSTGRES_PASSWORD=rf_password_123 ^
    echo   timescale/timescaledb:latest-pg15
    echo.
    echo Or use Docker Compose: docker compose up -d timescaledb
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        pause
        exit /b 1
    )
) else (
    echo Database connection successful!
)

echo.
echo Starting RF Spectrum Analyzer...
echo Application will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

:: Start the application
python app.py