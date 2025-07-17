@echo off
setlocal enabledelayedexpansion

:: RF Spectrum Analyzer Setup Script for Windows
:: This script sets up and runs the RF Spectrum Analyzer application

echo ================================================================
echo       RF Spectrum Analyzer - Windows Setup Script
echo ================================================================
echo.

:: Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop for Windows from:
    echo https://docs.docker.com/desktop/install/windows/
    pause
    exit /b 1
)

:: Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available
    echo Please ensure Docker Desktop is running
    pause
    exit /b 1
)

echo Docker is available - proceeding with setup...
echo.

:: Stop any existing containers
echo Stopping any existing RF Analyzer containers...
docker compose down --remove-orphans >nul 2>&1

:: Build and start the application
echo Building and starting RF Spectrum Analyzer...
echo This may take a few minutes on first run...
echo.

docker compose up -d --build

:: Check if containers started successfully
docker compose ps

:: Wait for database to be ready
echo.
echo Waiting for TimescaleDB to be ready...
:wait_db
timeout /t 5 >nul
docker compose exec -T timescaledb pg_isready -U rf_user -d rf_spectrum_db >nul 2>&1
if errorlevel 1 (
    echo Still waiting for database...
    goto wait_db
)

echo.
echo ================================================================
echo               Setup Complete!
echo ================================================================
echo.
echo The RF Spectrum Analyzer is now running:
echo.
echo  Main Application: http://localhost:5000
echo  Grafana Dashboard: http://localhost:3000
echo    - Username: admin
echo    - Password: rf-grafana-123
echo.
echo To generate sample data, run:
echo  python sample_data_generator.py
echo.
echo To stop the application:
echo  docker compose down
echo.
echo Press any key to open the application in your browser...
pause >nul

:: Open the application in default browser
start http://localhost:5000

echo.
echo Application opened in browser. Check Docker logs if needed:
echo  docker compose logs -f
echo.
pause