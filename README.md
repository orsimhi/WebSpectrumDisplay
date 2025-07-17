# RF Spectrum Analyzer - Professional Analysis Suite

A comprehensive, modern Python web application for advanced **RF (Radio Frequency) spectrum analysis** with real-time data visualization, sophisticated signal processing capabilities, and professional-grade analysis tools. Features **time-series database integration**, **interactive visualization**, **peak detection**, **spectrum occupancy analysis**, and **real-time streaming support**.

## 🚀 Key Features

### 📊 Advanced RF Analysis
- **Peak Detection**: Intelligent signal identification with configurable thresholds
- **Spectrum Occupancy Analysis**: Calculate bandwidth utilization and identify occupied frequency bands
- **Signal Characterization**: Automatic analysis of signal strength, noise floor, and dynamic range
- **Real-time Processing**: Live analysis with configurable update intervals
- **Multi-device Support**: Handle data from multiple SDR devices simultaneously

### 🗄️ Time-Series Database Integration
- **InfluxDB Support**: Purpose-built for time-stamped RF measurements
- **SQLite Fallback**: Automatic fallback for development and testing
- **High Performance**: Optimized for millions of RF data points
- **Data Retention**: Configurable policies for long-term storage
- **Real-time Ingestion**: Live data streaming and processing

### 🎮 Interactive Visualization
- **Plotly.js Integration**: Professional-grade, responsive plotting with zoom, pan, and scaling
- **Real-time Updates**: Live graph updates via WebSocket connections
- **Advanced Markers**: Click-to-add markers with detailed frequency/power information
- **Hover Details**: Comprehensive information on mouse hover
- **Export Capabilities**: Save plots and data in multiple formats

### 🎯 Professional User Interface
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Dark Theme**: Professional spectrum analyzer appearance optimized for long usage
- **Keyboard Shortcuts**: Complete keyboard navigation for power users
- **Auto-play Mode**: Automatic progression through spectrum records
- **Hold-to-Navigate**: Rapid navigation with hold-to-repeat functionality

### ⌨️ Comprehensive Controls
- **Navigation**: First, Previous, Next, Last record buttons with pagination
- **Analysis Tools**: One-click peak detection and occupancy analysis
- **Marker System**: Click-to-add markers with persistent storage across records
- **Zoom Controls**: Built-in zoom, pan, and reset functionality
- **Keyboard Shortcuts**: Full keyboard control for efficient operation

## 🔧 Technical Specifications

### RF Analysis Capabilities
- **Frequency Range**: Configurable (default 2.4-2.5 GHz for demonstration)
- **Resolution**: Up to 1000+ frequency points per sweep
- **Dynamic Range**: Full SDR dynamic range support
- **Signal Types**: WiFi, Bluetooth, cellular, ISM band, custom signals
- **Analysis Algorithms**: 
  - Peak detection with prominence and width analysis
  - Spectrum occupancy with threshold-based detection
  - Noise floor estimation and dynamic range calculation
  - Signal-to-noise ratio analysis

### Database Architecture
- **Primary**: InfluxDB 2.7+ for time-series data
- **Fallback**: SQLite for development and testing
- **Data Model**: Optimized for frequency-power-time relationships
- **Indexing**: Time-based indexing for fast queries
- **Retention**: Configurable data retention policies

### Web Application Stack
- **Backend**: Flask 2.3+ with Socket.IO for real-time communication
- **Frontend**: Bootstrap 5.3, Plotly.js 2.26, FontAwesome 6.4
- **Real-time**: WebSocket-based live updates
- **API**: RESTful endpoints for data and analysis
- **Containerization**: Docker and Docker Compose support

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Clone and start the complete stack
git clone <repository>
cd rf-spectrum-analyzer
docker-compose up -d

# Access the application
open http://localhost:5000
```

### Option 2: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start InfluxDB (optional - will use SQLite fallback)
docker run -p 8086:8086 -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \
  -e DOCKER_INFLUXDB_INIT_ORG=rf-org \
  -e DOCKER_INFLUXDB_INIT_BUCKET=rf-spectrum-data \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=rf-spectrum-token \
  influxdb:2.7

# Start the RF analyzer
python app.py

# Access the application
open http://localhost:5000
```

### Option 3: Automated Setup Script
```bash
# Make script executable and run
chmod +x start_app.sh
./start_app.sh
```

## 📊 Sample Data

The application automatically generates realistic sample RF spectrum data including:

- **WiFi Signals**: IEEE 802.11 channel simulation at 2.437 GHz
- **Bluetooth**: Low-energy signals at 2.442 GHz
- **Interference**: Simulated microwave oven interference at 2.45 GHz
- **Noise Floor**: Realistic -90 dBm noise floor with variations
- **Time Variation**: 50+ spectrum sweeps with temporal changes

## 🎮 User Interface Guide

### Navigation Controls
- **First/Last**: Jump to beginning or end of dataset
- **Previous/Next**: Navigate through spectrum records
- **Auto-play**: Automatic progression with configurable speed
- **Page Info**: Current position and total records display

### Analysis Tools
- **Peak Detection**: Identify and analyze signal peaks above threshold
- **Spectrum Occupancy**: Calculate bandwidth utilization statistics
- **Marker System**: Add and manage frequency markers
- **Export**: Save analysis results and plots

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `←` `→` | Navigate between records |
| `Home` `End` | First/last record |
| `Space` | Toggle auto-play |
| `P` | Peak detection analysis |
| `O` | Occupancy analysis |
| `C` | Clear all markers |
| `R` | Reset zoom |
| `?` | Show keyboard shortcuts |

## 🔌 API Endpoints

### Data Retrieval
```http
GET /api/spectrum_data?page=1&per_page=1
# Returns spectrum data with pagination

Response:
{
  "frequencies": [2400000000, 2400100000, ...],
  "powers": [-85.2, -87.1, ...],
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "device_id": "SDR-1",
    "measurement_type": "spectrum_sweep",
    "bandwidth": 100000.0,
    "gain": 20.0
  },
  "pagination": {
    "current_page": 1,
    "total_pages": 50,
    "total_records": 50,
    "per_page": 1
  }
}
```

### Analysis Endpoints
```http
GET /api/analysis/peak_detection?page=1&threshold=-70
# Performs peak detection analysis

GET /api/analysis/occupancy?page=1&threshold=-80
# Calculates spectrum occupancy statistics
```

## 🔧 Configuration

### Environment Variables
```bash
# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=rf-spectrum-token
INFLUXDB_ORG=rf-org
INFLUXDB_BUCKET=rf-spectrum-data

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Analysis Parameters
- **Peak Detection Threshold**: Default -70 dBm (configurable)
- **Occupancy Threshold**: Default -80 dBm (configurable)
- **Auto-play Interval**: 2 seconds (configurable)
- **Frequency Resolution**: Configurable based on data source

## 🏗️ Architecture

### Data Flow
```
SDR Device → Data Ingestion → InfluxDB → Web API → Real-time Visualization
                    ↓
              Analysis Engine → Results → User Interface
```

### Component Architecture
- **Data Layer**: InfluxDB/SQLite with optimized time-series storage
- **API Layer**: Flask REST endpoints with real-time WebSocket support
- **Analysis Layer**: SciPy-based signal processing and analysis
- **Presentation Layer**: Modern web interface with interactive visualization

## 🔬 Analysis Algorithms

### Peak Detection
- **Algorithm**: SciPy find_peaks with prominence and width analysis
- **Parameters**: Configurable height threshold and minimum distance
- **Output**: Peak frequency, power, prominence, and width characteristics

### Spectrum Occupancy
- **Method**: Threshold-based occupancy calculation
- **Metrics**: Total bandwidth, occupied bandwidth, occupancy percentage
- **Band Detection**: Automatic identification of occupied frequency bands

### Statistical Analysis
- **Noise Floor**: 10th percentile power level estimation
- **Dynamic Range**: Difference between maximum and minimum power
- **Average Power**: Mean power across the spectrum
- **Signal Characterization**: Automatic signal type identification

## 🚀 Performance

### Optimization Features
- **Lazy Loading**: Efficient data loading with pagination
- **Real-time Updates**: WebSocket-based live data streaming
- **Responsive Design**: Optimized for various screen sizes
- **Caching**: Intelligent caching for improved performance
- **Database Indexing**: Time-based indexing for fast queries

### Scalability
- **Time-series Database**: Handles millions of data points efficiently
- **Horizontal Scaling**: Docker-based deployment for easy scaling
- **Resource Management**: Configurable memory and CPU usage
- **Data Retention**: Automatic cleanup of old data

## 🔒 Security

### Best Practices
- **Input Validation**: Comprehensive validation of all user inputs
- **SQL Injection Protection**: Parameterized queries and ORM usage
- **Cross-Site Scripting (XSS) Protection**: Input sanitization and CSP headers
- **Authentication Ready**: Framework for user authentication and authorization

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>
cd rf-spectrum-analyzer

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Start development server
python app.py
```

### Code Structure
```
rf-spectrum-analyzer/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
├── Dockerfile         # Container definition
├── templates/         # HTML templates
│   └── index.html     # Main application interface
├── static/           # Static assets
│   ├── css/         # Stylesheets
│   └── js/          # JavaScript application
└── README.md        # This file
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **InfluxDB**: Time-series database excellence
- **Plotly.js**: Outstanding visualization capabilities
- **Flask**: Reliable and flexible web framework
- **Bootstrap**: Professional UI components
- **SciPy**: Powerful scientific computing capabilities

---

**RF Spectrum Analyzer** - Professional RF analysis made accessible and powerful. Perfect for RF engineers, researchers, and hobbyists who need comprehensive spectrum analysis capabilities with modern web-based visualization.

For support, feature requests, or contributions, please open an issue or submit a pull request.