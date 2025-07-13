@echo off
REM Nexora Virtual Environment Activation Script
REM This script activates the virtual environment for the Nexora project

echo.
echo ============================================================================
echo NEXORA PROJECT - VIRTUAL ENVIRONMENT ACTIVATION
echo ============================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run the setup script first to create the virtual environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo ============================================================================
echo VIRTUAL ENVIRONMENT ACTIVATED SUCCESSFULLY!
echo ============================================================================
echo.
echo You can now run Django commands:
echo   python manage.py runserver    - Start development server
echo   python manage.py check        - Check for issues
echo   python manage.py migrate      - Apply database migrations
echo   python manage.py collectstatic - Collect static files
echo.
echo To deactivate the virtual environment, type: deactivate
echo ============================================================================
echo.

REM Keep the command prompt open
cmd /k
