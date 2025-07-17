@echo off
setlocal

:: RF Spectrum Analyzer - Sample Data Generator for Windows

echo ================================================================
echo      RF Spectrum Analyzer - Sample Data Generator
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
set PYTHONPATH=%CD%

:: Check if database is running
echo Checking database connection...
python -c "import psycopg2; psycopg2.connect('postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db')" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Cannot connect to TimescaleDB
    echo Please ensure the database is running. You can start it with:
    echo   docker run -d --name rf-timescaledb -p 5432:5432 ^
    echo   -e POSTGRES_DB=rf_spectrum_db ^
    echo   -e POSTGRES_USER=rf_user ^
    echo   -e POSTGRES_PASSWORD=rf_password_123 ^
    echo   timescale/timescaledb:latest-pg15
    echo.
    echo Or use Docker Compose: docker compose up -d timescaledb
    pause
    exit /b 1
)

echo Database connection successful!
echo.

:: Ask user for number of scans
echo How many sample RF scans would you like to generate?
echo   - 100 scans (quick test) - about 30 seconds
echo   - 500 scans (good dataset) - about 2 minutes  
echo   - 1000 scans (large dataset) - about 4 minutes
echo.
set /p NUM_SCANS="Enter number of scans (default 200): "

:: Use default if no input
if "%NUM_SCANS%"=="" set NUM_SCANS=200

:: Validate input is numeric
echo %NUM_SCANS%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo ERROR: Please enter a valid number
    pause
    exit /b 1
)

echo.
echo Generating %NUM_SCANS% sample RF scans...
echo This includes realistic data for:
echo   - WiFi channel surveys (2.4 GHz and 5 GHz)
echo   - Bluetooth frequency hopping analysis
echo   - Cellular/LTE band monitoring
echo   - FM radio band scanning
echo   - GPS and amateur radio frequencies
echo.
echo Please wait...

:: Generate sample data
python sample_data_generator.py %NUM_SCANS%

if errorlevel 1 (
    echo.
    echo ERROR: Failed to generate sample data
    pause
    exit /b 1
)

echo.
echo ================================================================
echo             Sample Data Generation Complete!
echo ================================================================
echo.
echo Generated %NUM_SCANS% RF spectrum scans with markers
echo.
echo You can now:
echo   1. Start the application: run_app.bat
echo   2. Access the web interface: http://localhost:5000
echo   3. Explore the generated RF spectrum data
echo.
echo The data includes various realistic RF scenarios and
echo automatically generated markers for signal analysis.
echo.
pause