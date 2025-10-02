#!/bin/bash

# This script runs the Flask backend for the media library.

# Navigate to the Flask app directory
cd media_library_web

# Activate the virtual environment
source venv/bin/activate

# Run the Flask application
python src/main.py

