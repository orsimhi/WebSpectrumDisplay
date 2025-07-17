@echo off

:: RF Spectrum Analyzer - Stop Application Script for Windows

echo ================================================================
echo        RF Spectrum Analyzer - Stopping Application
echo ================================================================
echo.

:: Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not available - nothing to stop
    pause
    exit /b 0
)

:: Stop Docker Compose services
echo Stopping RF Spectrum Analyzer containers...
docker compose down

echo.
echo Checking for any remaining containers...
docker ps --filter "name=rf-" --format "table {{.Names}}\t{{.Status}}"

echo.
echo ================================================================
echo              Application Stopped Successfully
echo ================================================================
echo.
echo All RF Spectrum Analyzer containers have been stopped.
echo.
echo To start again, run: setup.bat
echo.
pause