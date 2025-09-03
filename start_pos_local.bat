@echo off
echo =========================================
echo   POS System with M-Pesa Integration
echo =========================================
echo.

REM Change to the admin directory
cd /d "%~dp0"


REM Check if virtual environment exists
if exist "env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found at env\Scripts\activate.bat
    echo Using system Python...
)

REM Install pyngrok if not already installed
echo Checking for pyngrok...
python -c "import pyngrok" >nul 2>&1
if errorlevel 1 (
    echo Installing pyngrok for ngrok integration...
    pip install pyngrok
)

REM Check if ngrok is installed
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ngrok is not installed or not in PATH
    echo.
    echo To enable M-Pesa payments, please:
    echo 1. Download ngrok from https://ngrok.com/download
    echo 2. Extract ngrok.exe to a folder in your PATH
    echo 3. Sign up at https://ngrok.com and get your auth token
    echo 4. Run: ngrok authtoken YOUR_AUTH_TOKEN
    echo.
    echo Continuing without ngrok - M-Pesa payments will not work
    echo.
    python start_pos_local.py --no-ngrok
) else (
    echo Starting POS system with ngrok tunnel...
    python start_pos_local.py
)

echo.
echo Press any key to exit...
pause >nul