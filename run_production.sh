#!/bin/bash
echo "Starting Viddy Downloader in production mode..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 wsgi:app