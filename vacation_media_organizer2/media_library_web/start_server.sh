#!/bin/bash

echo "🚀 Starting Vacation Media Library Flask Application"
echo "======================================================"
echo

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the media_library_web directory."
    exit 1
fi

# Check if database exists
DB_PATH="media_organizer.db"
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Warning: Database not found at $DB_PATH"
    echo "   Please run scan_main.py first to create and populate the database"
    echo
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements if they exist
if [ -f "requirements.txt" ]; then
    echo "📚 Installing requirements..."
    pip install -r requirements.txt
else
    echo "📚 Installing Flask requirements..."
    pip install Flask Flask-SQLAlchemy gunicorn
fi

echo
echo "Choose server mode:"
echo "1. Development server (Flask built-in) - Good for testing"
echo "2. Production server (Gunicorn) - Better for large files and performance"
echo

read -p "Enter choice (1-2) [default: 1]: " choice
choice=${choice:-1}

if [ "$choice" = "2" ]; then
    echo "🌟 Starting Gunicorn production server on http://localhost:5001"
    echo "   Press Ctrl+C to stop the server"
    echo
    
    # Start with Gunicorn for better performance with large files
    gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 --max-requests 1000 --preload src.main:app
else
    echo "🌟 Starting Flask development server on http://localhost:5001"
    echo "   Press Ctrl+C to stop the server"
    echo "   Note: For large media files, consider using option 2 (Gunicorn)"
    echo
    
    # Set environment variables for better performance
    export FLASK_ENV=development
    export PYTHONUNBUFFERED=1
    
    # Start the Flask application
    python src/main.py
fi