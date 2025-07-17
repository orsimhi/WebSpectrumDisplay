@echo off
echo ================================================
echo    WebSpectrumDisplay TimescaleDB Setup
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✓ Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment created
echo.

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo ✓ Dependencies installed
echo.

REM Copy environment file
if not exist .env (
    echo Copying environment configuration template...
    copy .env.example .env
    echo ✓ Environment file created (.env)
    echo.
    echo IMPORTANT: Please edit .env file with your TimescaleDB credentials
    echo.
) else (
    echo ✓ Environment file already exists
    echo.
)

echo ================================================
echo              Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env file with your TimescaleDB credentials
echo 2. Ensure TimescaleDB is running (Docker or local installation)
echo 3. Run: python cli.py test-connection
echo 4. Run: python cli.py setup
echo 5. Try migration: python cli.py migrate -i sample_data.ndjson
echo.
echo To activate the environment in future sessions:
echo   venv\Scripts\activate.bat
echo.
pause