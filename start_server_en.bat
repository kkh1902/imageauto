@echo off
cd /d C:\DEV\imageauto

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing packages...
pip install -r requirements.txt

echo Starting server...
echo Open browser: http://localhost:5000
echo Press Ctrl+C to stop server

python run.py

pause
