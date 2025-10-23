@echo off

REM This script runs the Flask backend for the media library.

REM Navigate to the Flask app directory
cd media_library_web

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the Flask application
python src\main.py

