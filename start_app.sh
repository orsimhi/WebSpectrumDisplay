#!/bin/bash

# RF Spectrum Analyzer - Professional Analysis Suite
# Automated setup and startup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INFLUXDB_VERSION="2.7"
INFLUXDB_PORT="8086"
FLASK_PORT="5000"
CONTAINER_NAME="rf-influxdb"
APP_NAME="RF Spectrum Analyzer"

echo -e "${BLUE}🚀 Starting ${APP_NAME} - Professional Analysis Suite${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo -e "${BLUE}📋 System Information${NC}"
echo "   Operating System: $OS"
echo "   Python Version: $(python3 --version 2>/dev/null || python --version 2>/dev/null || echo 'Not found')"
echo "   Docker Status: $(docker --version 2>/dev/null || echo 'Not installed')"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    if command_exists netstat; then
        netstat -tuln | grep -q ":$1 "
    elif command_exists ss; then
        ss -tuln | grep -q ":$1 "
    elif command_exists lsof; then
        lsof -i ":$1" >/dev/null 2>&1
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$host:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is ready!${NC}"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            echo -n "   "
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo ""
    echo -e "${YELLOW}⚠️  $service health check timeout, continuing anyway...${NC}"
    return 1
}

# Check Python installation
echo -e "${BLUE}🐍 Checking Python Installation${NC}"
if command_exists python3; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command_exists python; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo -e "${RED}❌ Python not found. Please install Python 3.7+ and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python found: $($PYTHON_CMD --version)${NC}"

# Check pip installation
if ! command_exists $PIP_CMD; then
    echo -e "${RED}❌ pip not found. Please install pip and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip found: $($PIP_CMD --version)${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python Dependencies${NC}"
if [ -f "requirements.txt" ]; then
    echo "   Installing from requirements.txt..."
    $PIP_CMD install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing individual packages...${NC}"
    $PIP_CMD install Flask plotly numpy pandas python-dateutil influxdb-client Flask-SocketIO scipy
    echo -e "${GREEN}✓ Essential packages installed${NC}"
fi
echo ""

# Docker setup for InfluxDB
echo -e "${BLUE}🐳 Setting up InfluxDB Database${NC}"

if command_exists docker; then
    echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"
    
    # Check if InfluxDB port is in use
    if port_in_use $INFLUXDB_PORT; then
        echo -e "${YELLOW}⚠️  Port $INFLUXDB_PORT is already in use${NC}"
        echo "   Checking if InfluxDB container is already running..."
        
        if docker ps | grep -q $CONTAINER_NAME; then
            echo -e "${GREEN}✓ InfluxDB container is already running${NC}"
        else
            echo -e "${YELLOW}⚠️  Port in use by another service. Will use SQLite fallback.${NC}"
        fi
    else
        # Stop existing container if it exists
        if docker ps -a | grep -q $CONTAINER_NAME; then
            echo "   Removing existing InfluxDB container..."
            docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
            docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
        fi
        
        echo "   Starting InfluxDB container..."
        docker run -d \
            --name $CONTAINER_NAME \
            -p $INFLUXDB_PORT:8086 \
            -e DOCKER_INFLUXDB_INIT_MODE=setup \
            -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
            -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \
            -e DOCKER_INFLUXDB_INIT_ORG=rf-org \
            -e DOCKER_INFLUXDB_INIT_BUCKET=rf-spectrum-data \
            -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=rf-spectrum-token \
            influxdb:$INFLUXDB_VERSION >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ InfluxDB container started${NC}"
            wait_for_service "localhost" $INFLUXDB_PORT "InfluxDB"
        else
            echo -e "${YELLOW}⚠️  Failed to start InfluxDB container. Will use SQLite fallback.${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Will use SQLite database as fallback.${NC}"
fi
echo ""

# Check Flask port availability
echo -e "${BLUE}🌐 Checking Web Server Port${NC}"
if port_in_use $FLASK_PORT; then
    echo -e "${YELLOW}⚠️  Port $FLASK_PORT is already in use${NC}"
    echo "   The RF Spectrum Analyzer may already be running."
    echo "   If you want to restart it, please stop the existing process first."
    echo ""
    
    read -p "   Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}👋 Setup cancelled by user${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}✓ Port $FLASK_PORT is available${NC}"
fi
echo ""

# Set environment variables
echo -e "${BLUE}⚙️  Setting up Environment${NC}"
export INFLUXDB_URL="http://localhost:$INFLUXDB_PORT"
export INFLUXDB_TOKEN="rf-spectrum-token"
export INFLUXDB_ORG="rf-org"
export INFLUXDB_BUCKET="rf-spectrum-data"
export FLASK_ENV="development"

echo "   InfluxDB URL: $INFLUXDB_URL"
echo "   Organization: $INFLUXDB_ORG"
echo "   Bucket: $INFLUXDB_BUCKET"
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Display startup information
echo -e "${BLUE}🎯 Starting RF Spectrum Analyzer${NC}"
echo "   Application will start on: http://localhost:$FLASK_PORT"
echo "   InfluxDB UI available at: http://localhost:$INFLUXDB_PORT (if running)"
echo "   Press Ctrl+C to stop the application"
echo ""

# Start the application
echo -e "${GREEN}🚀 Launching ${APP_NAME}...${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ app.py not found in current directory${NC}"
    echo "   Please run this script from the RF Spectrum Analyzer directory"
    exit 1
fi

# Start the Flask application
$PYTHON_CMD app.py

# Cleanup function for graceful shutdown
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Shutting down RF Spectrum Analyzer...${NC}"
    
    if command_exists docker && docker ps | grep -q $CONTAINER_NAME; then
        echo "   Stopping InfluxDB container..."
        docker stop $CONTAINER_NAME >/dev/null 2>&1
        docker rm $CONTAINER_NAME >/dev/null 2>&1
        echo -e "${GREEN}✓ InfluxDB container stopped${NC}"
    fi
    
    echo -e "${BLUE}👋 RF Spectrum Analyzer stopped. Thank you for using!${NC}"
    exit 0
}

# Set up trap for graceful shutdown
trap cleanup SIGINT SIGTERM

# Instructions for manual setup
echo ""
echo -e "${BLUE}📖 Manual Setup Instructions${NC}"
echo "   If automatic setup fails, you can run manually:"
echo ""
echo "   1. Install Python dependencies:"
echo "      $PIP_CMD install -r requirements.txt"
echo ""
echo "   2. Start InfluxDB (optional):"
echo "      docker run -p 8086:8086 -e DOCKER_INFLUXDB_INIT_MODE=setup \\"
echo "        -e DOCKER_INFLUXDB_INIT_USERNAME=admin \\"
echo "        -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \\"
echo "        -e DOCKER_INFLUXDB_INIT_ORG=rf-org \\"
echo "        -e DOCKER_INFLUXDB_INIT_BUCKET=rf-spectrum-data \\"
echo "        -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=rf-spectrum-token \\"
echo "        influxdb:2.7"
echo ""
echo "   3. Start the application:"
echo "      $PYTHON_CMD app.py"
echo ""
echo -e "${BLUE}🔗 Useful Links${NC}"
echo "   Application: http://localhost:$FLASK_PORT"
echo "   InfluxDB UI: http://localhost:$INFLUXDB_PORT"
echo "   GitHub: https://github.com/your-repo/rf-spectrum-analyzer"
echo ""
echo -e "${GREEN}✨ RF Spectrum Analyzer is ready for professional RF analysis!${NC}"