#!/bin/bash

# RF Amplitude Graph Viewer Startup Script

echo "🔬 RF Amplitude Graph Viewer with Time-Series Database"
echo "======================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker service is running
check_docker_service() {
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            return 0
        else
            echo "⚠️  Docker is installed but not running"
            echo "   Please start Docker service and try again"
            return 1
        fi
    else
        echo "⚠️  Docker not found. Please install Docker to use InfluxDB"
        echo "   Alternatively, install InfluxDB manually on your system"
        return 1
    fi
}

# Check Docker and start InfluxDB if needed
echo "🐳 Checking Docker and InfluxDB..."
if check_docker_service; then
    # Check if InfluxDB container is running
    if ! docker ps | grep -q "rf-influxdb"; then
        echo "🚀 Starting InfluxDB container..."
        docker-compose up -d influxdb
        
        echo "⏳ Waiting for InfluxDB to be ready..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if docker exec rf-influxdb influx ping >/dev/null 2>&1; then
                echo "✅ InfluxDB is ready!"
                break
            fi
            sleep 2
            timeout=$((timeout-2))
        done
        
        if [ $timeout -le 0 ]; then
            echo "❌ InfluxDB failed to start within 60 seconds"
            echo "   Check Docker logs: docker logs rf-influxdb"
            exit 1
        fi
    else
        echo "✅ InfluxDB container is already running"
    fi
else
    echo "⚠️  Will attempt to run in mock data mode"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    python3 -m venv venv
    
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install Flask plotly numpy pandas python-dateutil influxdb-client Flask-SocketIO
else
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    
    # Check if new dependencies are installed
    if ! python -c "import influxdb_client" 2>/dev/null; then
        echo "📦 Installing new dependencies..."
        pip install influxdb-client Flask-SocketIO
    fi
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found!"
    exit 1
fi

echo ""
echo "🚀 Starting RF Amplitude Graph Viewer..."
echo ""
echo "📊 Application will be available at:"
echo "   http://localhost:5000"
echo ""
echo "🛠️  InfluxDB Admin UI (if running):"
echo "   http://localhost:8086"
echo "   Username: admin"
echo "   Password: rf-password-123"
echo ""
echo "✨ Features:"
echo "   • Time-series database storage (InfluxDB)"
echo "   • Real-time data updates via WebSockets"
echo "   • Pagination support for large datasets"
echo "   • NDJSON data format support"
echo "   • Interactive RF amplitude graphs with zoom/pan"
echo "   • Click to add markers on graphs"
echo "   • Navigate between records with buttons or keyboard"
echo "   • Hold Previous/Next buttons for fast navigation"
echo "   • Auto-play mode with adjustable speed"
echo "   • Auto-reload for new data"
echo ""
echo "⌨️  Keyboard Shortcuts:"
echo "   • Arrow Left/Right: Navigate records"
echo "   • Space: Toggle auto-play"
echo "   • Home/End: Go to first/last record"
echo "   • PageUp/PageDown: Navigate pages"
echo "   • R: Toggle auto-reload"
echo "   • M: Toggle marker mode"
echo "   • C: Clear markers"
echo "   • Escape: Reset zoom"
echo ""
echo "📁 Data Migration:"
echo "   Use migrate_data.py to import existing RF data:"
echo "   python migrate_data.py --ndjson your_data.ndjson"
echo "   python migrate_data.py --help  # for more options"
echo ""
echo "Press Ctrl+C to stop the application"
echo "======================================================"
echo ""

# Start the Flask application
python app.py