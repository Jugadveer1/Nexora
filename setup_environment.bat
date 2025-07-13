@echo off
REM Nexora Project Environment Setup Script
REM This script sets up the complete development environment

echo.
echo ============================================================================
echo NEXORA PROJECT - ENVIRONMENT SETUP
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher and try again.
    echo.
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
) else (
    echo Virtual environment already exists.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing project dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo RUNNING DJANGO SYSTEM CHECKS...
echo ============================================================================
echo.

REM Run Django checks
python manage.py check

echo.
echo ============================================================================
echo COLLECTING STATIC FILES...
echo ============================================================================
echo.

REM Collect static files
python manage.py collectstatic --noinput

echo.
echo ============================================================================
echo SETUP COMPLETED SUCCESSFULLY!
echo ============================================================================
echo.
echo Your Nexora development environment is now ready!
echo.
echo To start the development server:
echo   python manage.py runserver
echo.
echo To activate the virtual environment in the future:
echo   Run activate_venv.bat or use: venv\Scripts\activate
echo.
echo ============================================================================
echo.

pause
