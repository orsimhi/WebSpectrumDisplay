#!/bin/bash

# RF Amplitude Graph Viewer Startup Script

echo "Starting RF Amplitude Graph Viewer..."
echo "======================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install Flask plotly numpy pandas python-dateutil
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found!"
    exit 1
fi

echo "Starting Flask application..."
echo ""
echo "The RF Amplitude Graph Viewer will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Features:"
echo "  - Interactive RF amplitude graphs with zoom/pan"
echo "  - Click to add markers on graphs"
echo "  - Navigate between records with buttons or keyboard"
echo "  - Hold Previous/Next buttons for fast navigation"
echo "  - Auto-play mode with adjustable speed"
echo "  - Keyboard shortcuts (Space, Arrow keys, etc.)"
echo ""
echo "Press Ctrl+C to stop the application"
echo "======================================="
echo ""

# Start the Flask application
python app.py