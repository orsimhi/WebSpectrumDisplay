# RF Amplitude Graph Viewer

A modern Python web application for visualizing and analyzing RF (Radio Frequency) amplitude data with **time-series database storage**, **real-time updates**, **pagination**, and **NDJSON streaming support**. Features interactive graphs, navigation controls, and comprehensive marker functionality.

## Features

### � Time-Series Database
- **InfluxDB Integration**: Purpose-built time-series database for RF data
- **Real-time Streaming**: Live data ingestion and visualization
- **High Performance**: Optimized for time-stamped RF measurements
- **Scalable Storage**: Handle millions of RF data points efficiently
- **Data Retention**: Configurable retention policies for long-term storage

### �📊 Interactive Graphs
- **Plotly.js Integration**: High-performance, responsive plotting with zoom, pan, and scaling
- **Real-time Updates**: Automatic graph updates via WebSockets
- **Hover Details**: Frequency/power information on mouse hover
- **Zoom Controls**: Built-in zoom, pan, and reset functionality

### 🎯 Advanced Marker System
- **Click-to-Add**: Click anywhere on the graph to place markers
- **Cross-Record Markers**: Markers tied to specific timestamps and records
- **Detailed Info**: View frequency, power, timestamp, and device info
- **Persistent Storage**: Markers remain when navigating between records
- **Batch Management**: Remove individual markers or clear all at once

### 🎮 Enhanced Navigation
- **Pagination**: Handle large datasets with page-based navigation
- **Auto-Loading**: Automatic data loading and smooth transitions
- **Button Navigation**: First, Previous, Next, Last record buttons
- **Page Navigation**: Previous/Next page buttons for large datasets
- **Auto-Play**: Automatic progression through records with adjustable speed
- **Hold-to-Navigate**: Hold Previous/Next buttons for rapid navigation
- **Load More**: Dynamically load additional data as needed

### ⌨️ Comprehensive Keyboard Shortcuts
- `Arrow Left/Right`: Navigate between records
- `Space`: Toggle auto-play
- `Home/End`: Go to first/last record
- `PageUp/PageDown`: Navigate between pages
- `R`: Toggle auto-reload for live data
- `M`: Toggle marker mode
- `C`: Clear all markers
- `Escape`: Reset zoom

### 📡 Real-Time Features
- **WebSocket Updates**: Live data streaming from InfluxDB
- **Auto-Reload**: Automatic detection and loading of new RF measurements
- **Background Sync**: Periodic updates without interrupting user interaction
- **Connection Status**: Visual indicators for real-time connection status

### 📱 Modern UI & UX
- **Responsive Design**: Works flawlessly on desktop, tablet, and mobile
- **Dark Theme**: Professional appearance with gradient backgrounds and glass morphism
- **Real-time Info**: Display current record info (timestamp, center frequency, span, device)
- **Status Updates**: Visual feedback for all user actions
- **Smooth Animations**: Elegant transitions and loading states
- **Pagination Controls**: Intuitive page navigation with status indicators

### 🗄️ Database & Data Management
- **InfluxDB Storage**: Time-series database optimized for RF measurements
- **NDJSON Support**: Native support for newline-delimited JSON streaming
- **Batch Processing**: Efficient handling of large data imports
- **Multiple Formats**: Support for JSON, CSV, NumPy, and NDJSON files
- **Device Tagging**: Track data from multiple RF devices and locations
- **Metadata Storage**: Store additional measurement parameters and tags

## Installation

### Prerequisites
- Python 3.7 or higher
- Docker and Docker Compose (recommended for InfluxDB)
- pip (Python package manager)

### Quick Start
1. **Clone or download the project files**

2. **Start the application with automatic setup:**
   ```bash
   chmod +x start_app.sh
   ./start_app.sh
   ```
   
   This script will:
   - Start InfluxDB using Docker Compose
   - Create a Python virtual environment
   - Install all dependencies
   - Launch the Flask application

3. **Access the applications:**
   - **RF Viewer**: http://localhost:5000
   - **InfluxDB UI**: http://localhost:8086 (admin/rf-password-123)

### Manual Setup
If you prefer manual installation:

1. **Start InfluxDB:**
   ```bash
   docker-compose up -d influxdb
   ```

2. **Setup Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

### Alternative: InfluxDB without Docker
If you prefer to install InfluxDB directly:
1. Install InfluxDB 2.x on your system
2. Create organization: `rf-org`
3. Create bucket: `rf-amplitude-data`
4. Create token: `rf-amplitude-token`
5. Update connection settings in `app.py` if needed

## Data Structure

The application supports multiple data formats, with **NDJSON** being the preferred format for streaming data:

### NDJSON Format (Recommended)
Each line contains a complete RF measurement event:
```json
{"timestamp": "2024-01-01T12:00:00Z", "center_frequency": 2400.0, "span": 100.0, "device_id": "analyzer_001", "location": "lab_a", "powers": [-85.2, -84.8, -45.2, -85.5]}
{"timestamp": "2024-01-01T12:00:05Z", "center_frequency": 2405.0, "span": 100.0, "device_id": "analyzer_001", "location": "lab_a", "powers": [-84.9, -85.2, -35.8, -85.1]}
```

### Standard JSON Format
```json
{
    "timestamp": "2024-01-01T12:00:00Z",
    "center_frequency": 2400.0,
    "span": 100.0,
    "device_id": "spectrum_analyzer_001",
    "location": "lab_a",
    "powers": [...],
    "additional_field": "value"
}
```

### Field Descriptions
- **timestamp**: ISO 8601 timestamp (e.g., "2024-01-01T12:00:00Z")
- **center_frequency**: Center frequency in MHz
- **span**: Frequency span in MHz
- **powers**: Array of power measurements in dBm (y-axis data)
- **device_id**: Identifier for the RF measurement device
- **location**: Physical location or lab identifier
- **X-axis**: Automatically calculated from center frequency and span

## Data Migration

The included `migrate_data.py` utility supports multiple data formats:

### NDJSON Migration (Streaming)
```bash
# Standard NDJSON migration
python migrate_data.py --ndjson rf_data.ndjson

# Streaming for large files
python migrate_data.py --stream rf_data.ndjson --batch-size 1000

# Directory migration
python migrate_data.py --directory ./rf_measurements --pattern "*.ndjson"
```

### Other Formats
```bash
# JSON files
python migrate_data.py --json rf_data.json

# CSV files (requires frequency parameters)
python migrate_data.py --csv data.csv --center-freq 2400 --span 100

# NumPy arrays
python migrate_data.py --numpy rf_array.npy --center-freq 2400 --span 100

# Export from InfluxDB
python migrate_data.py --export exported_data.ndjson --time-range "-7d"
```

### Migration Options
- `--device-id`: Set device identifier (default: "spectrum_analyzer")
- `--location`: Set measurement location (default: "lab")
- `--batch-size`: Batch size for streaming (default: 100)
- `--clear`: Clear existing data before migration
- `--help`: Show all available options

## API Endpoints

The application provides REST API endpoints for programmatic access:

- `GET /api/rf_data` - Get all RF records
- `GET /api/rf_data/<id>` - Get specific RF record
- `GET /api/plot/<id>` - Get plot data for specific record

## Usage Tips

### Navigation
- Use **Previous/Next** buttons for single-step navigation
- **Hold** Previous/Next buttons to navigate rapidly through many records
- Use **Auto-Play** to automatically cycle through records
- Adjust **playback speed** for auto-play (from 0.2s to 2s intervals)

### Markers
- **Toggle marker mode** with the "Add Marker" button or press `M`
- **Click anywhere** on the graph to place a marker when in marker mode
- **View all markers** in the markers panel below the graph
- **Remove markers** individually or clear all at once

### Graph Interaction
- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Click and drag to pan around the graph
- **Reset**: Use "Reset Zoom" button or press `Escape`
- **Hover**: Move mouse over graph to see frequency/power values

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| ← → | Navigate Previous/Next |
| Space | Toggle Auto-Play |
| Home/End | Go to First/Last |
| Escape | Reset Zoom |
| M | Toggle Marker Mode |
| C | Clear All Markers |

## Customization

### Sample Data
The application includes realistic sample RF data that simulates:
- **Noise floor**: Base noise level around -80 dBm
- **Signal peaks**: Random signal peaks between -40 to -20 dBm
- **Frequency range**: Around 2.4 GHz (WiFi/ISM band)
- **Multiple records**: 50 sample measurements

### Styling
Modify `static/css/style.css` to customize:
- Color schemes
- Layout and spacing
- Responsive breakpoints
- Animation effects

### Functionality
Modify `static/js/app.js` to add:
- Additional marker types
- Custom analysis tools
- Export functionality
- Additional keyboard shortcuts

## Browser Compatibility

- **Chrome/Chromium** (recommended)
- **Firefox**
- **Safari**
- **Edge**

## Performance

- Handles datasets with thousands of frequency points per record
- Optimized for smooth navigation between records
- Efficient marker management
- Responsive design for various screen sizes

## Future Enhancements

Potential features for future versions:
- **Export functionality** (PNG, PDF, CSV)
- **Measurement tools** (bandwidth, peak detection)
- **Comparison mode** (overlay multiple records)
- **Database import/export**
- **Custom marker colors and shapes**
- **Annotation tools**

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py`:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

2. **Module not found**: Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database issues**: Delete `rf_data.db` to recreate with sample data

4. **Browser compatibility**: Use a modern browser with JavaScript enabled

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the code comments
3. Modify the sample data format to match your existing data structure