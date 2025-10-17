#!/bin/bash
# Geographic Translation Editor Launcher
# This script helps launch the GUI with the correct Python environment and dependencies

echo "🌏 Geographic Translation Editor Launcher"
echo "=========================================="

# Function to test tkinter availability
test_tkinter() {
    $1 -c "import tkinter; print('✅ tkinter is available')" 2>/dev/null
    return $?
}

# Function to test requests availability
test_requests() {
    $1 -c "import requests; print('✅ requests is available')" 2>/dev/null
    return $?
}

# Function to test both tkinter and requests
test_python_environment() {
    local python_cmd=$1
    local env_name=$2
    
    echo -n "Testing $env_name: "
    
    if test_tkinter $python_cmd; then
        echo -n "tkinter ✅ "
        if test_requests $python_cmd; then
            echo "requests ✅ - Full functionality available!"
            return 0  # Perfect - can run with full features
        else
            echo "requests ❌ - Limited functionality (no web search)"
            return 1  # Good enough - can run with basic features
        fi
    else
        echo "tkinter ❌ - Cannot run GUI"
        return 2  # Cannot run at all
    fi
}

# Function to launch with appropriate warning
launch_editor() {
    local python_cmd=$1
    local has_requests=$2
    
    echo ""
    if [ "$has_requests" = "true" ]; then
        echo "🚀 Starting Geographic Translation Editor with full functionality..."
    else
        echo "⚠️  Starting Geographic Translation Editor with limited functionality..."
        echo "   (Web search disabled - only built-in translations available)"
    fi
    echo ""
    cd "/Users/syuen/Video_editor_Project/Vacaction_Media_Org"
    $python_cmd geo_translation_editor.py
}

# Try different Python interpreters
echo "Testing Python interpreters for tkinter and requests support..."
echo ""

# Test virtual environment first (if available)
if [ -f ".venv/bin/python" ]; then
    test_python_environment ".venv/bin/python" "Virtual Environment (.venv)"
    result=$?
    if [ $result -eq 0 ]; then
        launch_editor ".venv/bin/python" "true"
        exit 0
    elif [ $result -eq 1 ]; then
        launch_editor ".venv/bin/python" "false"
        exit 0
    fi
fi

# Test current python3
test_python_environment "python3" "System Python3"
result=$?
if [ $result -eq 0 ]; then
    launch_editor "python3" "true"
    exit 0
elif [ $result -eq 1 ]; then
    launch_editor "python3" "false"
    exit 0
fi

# Test system Python
test_python_environment "/usr/bin/python3" "macOS System Python"
result=$?
if [ $result -eq 0 ]; then
    launch_editor "/usr/bin/python3" "true"
    exit 0
elif [ $result -eq 1 ]; then
    launch_editor "/usr/bin/python3" "false"
    exit 0
fi

# If no working Python found, provide installation instructions
echo ""
echo "❌ No suitable Python interpreter found!"
echo ""
echo "🛠️  Installation Instructions:"
echo ""
echo "1. Fix tkinter (if missing):"
echo "   brew install python-tk"
echo ""
echo "2. Install requests library:"
echo "   # For virtual environment:"
echo "   source .venv/bin/activate"
echo "   pip install requests"
echo ""
echo "   # For system Python:"
echo "   pip3 install --user --break-system-packages requests"
echo ""
echo "3. Alternative: Install Python from python.org (includes tkinter by default):"
echo "   https://www.python.org/downloads/"
echo ""
echo "4. Check VS Code's Python interpreter:"
echo "   - In VS Code: Cmd+Shift+P → 'Python: Select Interpreter'"
echo "   - See which Python path VS Code is using"
echo ""
echo "📋 Current Status Summary:"
echo "   - tkinter: Required for GUI (install with: brew install python-tk)"
echo "   - requests: Optional for web search (install with: pip install requests)"
echo "   - App works without requests but with limited translation suggestions"
echo ""