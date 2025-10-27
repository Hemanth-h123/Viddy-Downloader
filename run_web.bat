@echo off
echo Starting ALL-in-one Downloader Web Application...
echo.

REM Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist venv\Lib\site-packages\flask (
    echo Installing requirements...
    pip install -r requirements_web.txt
)

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=development

REM Run the Flask application
echo Starting Flask application...
echo.
echo Access the application at http://127.0.0.1:5000
echo Press CTRL+C to stop the server
echo.
flask run

pause