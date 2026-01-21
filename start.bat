@echo off
echo ========================================
echo Arabic Grammar Analyzer - Quick Start
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please create .env file with your OpenAI API key
    echo Copy .env.example to .env and add your API key
    echo.
    pause
    exit /b 1
)

REM Install/Update requirements
echo.
echo Installing/Updating dependencies...
pip install -r requirements-dev.txt

REM Create necessary directories
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads

REM Start the application
echo.
echo ========================================
echo Starting Arabic Grammar Analyzer...
echo ========================================
echo.
echo Open your browser and go to:
echo http://localhost:5000
echo.
echo Login with:
echo Username: teacher1
echo Password: 1234
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause
