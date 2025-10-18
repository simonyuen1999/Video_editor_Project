#!/bin/bash
# Simple launcher for Geographic Translation Editor
# Auto-detects best Python environment and launches the GUI

echo "🌏 Launching Geographic Translation Editor..."

# Quick test function
has_both() {
    $1 -c "import tkinter, requests" 2>/dev/null
}

# Try different Python environments in order of preference
if [ -f "/Users/syuen/Video_editor_Project/.venv/bin/python" ] && has_both "/Users/syuen/Video_editor_Project/.venv/bin/python"; then
    echo "Using virtual environment with full features..."
    cd "/Users/syuen/Video_editor_Project/Vacaction_Media_Org"
    /Users/syuen/Video_editor_Project/.venv/bin/python geo_translation_editor.py
elif has_both "python3"; then
    echo "Using system Python with full features..."
    cd "/Users/syuen/Video_editor_Project/Vacaction_Media_Org"
    python3 geo_translation_editor.py
elif python3 -c "import tkinter" 2>/dev/null; then
    echo "Using system Python with basic features (no web search)..."
    cd "/Users/syuen/Video_editor_Project/Vacaction_Media_Org"
    python3 geo_translation_editor.py
elif /usr/bin/python3 -c "import tkinter" 2>/dev/null; then
    echo "Using macOS system Python..."
    cd "/Users/syuen/Video_editor_Project/Vacaction_Media_Org"
    /usr/bin/python3 geo_translation_editor.py
else
    echo "❌ No suitable Python found. Please install tkinter:"
    echo "   brew install python-tk"
fi