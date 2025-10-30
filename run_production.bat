@echo off
echo Starting Viddy Downloader in production mode...
set PYTHONPATH=%PYTHONPATH%;%cd%
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 wsgi:app