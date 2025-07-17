# RF Spectrum Analyzer with TimescaleDB

A modern web-based RF spectrum analyzer application built with Flask and TimescaleDB, designed for real-time spectrum monitoring, analysis, and visualization.

![RF Spectrum Analyzer](https://img.shields.io/badge/RF-Spectrum%20Analyzer-blue)
![TimescaleDB](https://img.shields.io/badge/Database-TimescaleDB-orange)
![Flask](https://img.shields.io/badge/Backend-Flask-green)
![Docker](https://img.shields.io/badge/Deployment-Docker-blue)

## 🚀 Features

### Core Functionality
- **Real-time RF Spectrum Visualization** - Interactive plots with zoom, pan, and marker support
- **TimescaleDB Integration** - Optimized time-series database for RF scan storage
- **Advanced Filtering** - Filter by center frequency, configuration name, instance, and time range
- **Keyboard Navigation** - Fast navigation between scans using arrow keys
- **Analysis Tools** - Built-in peak detection, signal analysis, and interference detection

### Analysis Capabilities
- **Peak Detection** - Automatic identification of signal peaks with configurable thresholds
- **Signal Statistics** - Comprehensive power statistics and frequency band analysis
- **Interference Detection** - Automated detection of potential interference sources
- **Configurable Presets** - Save and reuse analysis configurations

### Markers and Annotations
- **Interactive Markers** - Click on spectrum to add custom markers
- **Automatic Markers** - Auto-generated markers from peak detection
- **Marker Management** - Add, edit, and delete markers with notes
- **Marker Types** - Support for manual, peak, valley, and reference markers

### User Interface
- **Modern Web UI** - Responsive design with glassmorphism effects
- **Keyboard Shortcuts** - Efficient navigation and control
- **Real-time Updates** - WebSocket-based live data streaming
- **Mobile Friendly** - Responsive design for mobile devices

## 📊 Database Schema

The application uses TimescaleDB with the following main tables:

### RF Scans (`rf_scans`)
```sql
- scan_time (TIMESTAMPTZ) - Primary key, optimized for time-series queries
- scan_id (UUID) - Primary key, unique identifier for each scan
- flags (TEXT[]) - Array of flags (e.g., "high_signal", "interference")
- instance_name (TEXT) - Name of the spectrum analyzer instance
- powers (FLOAT[]) - Array of power values in dBm
- config_info (JSONB) - Configuration parameters including:
  - name: Configuration name
  - cf: Center frequency (MHz)
  - span: Frequency span (MHz)
  - sample_amount: Number of frequency points
  - rbw: Resolution bandwidth
  - vbw: Video bandwidth
  - ref_level: Reference level
```

### Analysis Presets (`analysis_presets`)
```sql
- id (SERIAL) - Primary key
- name (TEXT) - Preset name
- description (TEXT) - Description of the preset
- preset_config (JSONB) - Analysis configuration parameters
```

### Scan Markers (`scan_markers`)
```sql
- id (SERIAL) - Primary key
- scan_time/scan_id - Foreign key to rf_scans
- marker_name (TEXT) - User-defined marker name
- frequency_mhz (FLOAT) - Marker frequency
- power_dbm (FLOAT) - Power at marker frequency
- marker_type (TEXT) - Type: manual, peak, valley, reference
- notes (TEXT) - Optional notes
```

## 🛠️ Installation & Setup

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository:**
```bash
git clone <repository-url>
cd rf-spectrum-analyzer
```

2. **Start the application:**
```bash
docker-compose up -d
```

This will start:
- TimescaleDB database on port 5432
- RF Spectrum Analyzer app on port 5000
- Grafana (optional) on port 3000

3. **Access the application:**
- Main application: http://localhost:5000
- Grafana dashboard: http://localhost:3000 (admin/rf-grafana-123)

### Option 2: Local Development

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up TimescaleDB:**
   - Install PostgreSQL with TimescaleDB extension
   - Create database: `rf_spectrum_db`
   - Run the initialization script: `psql -f init_db.sql`

3. **Set environment variables:**
```bash
export DATABASE_URL=postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db
```

4. **Run the application:**
```bash
python app.py
```

### Generate Sample Data

To populate the database with realistic test data:

```bash
# Generate 200 sample scans (default)
python sample_data_generator.py

# Generate custom number of scans
python sample_data_generator.py 500
```

The sample data generator creates realistic RF spectrum data for various scenarios:
- WiFi channel surveys (2.4 GHz and 5 GHz)
- Bluetooth frequency hopping analysis
- Cellular/LTE band monitoring
- FM radio band scanning
- GPS and amateur radio frequencies

## 🎮 Usage Guide

### Keyboard Shortcuts
- **Arrow Keys (←/→)** - Navigate between scans
- **Space** - Play/pause auto-navigation
- **Home/End** - Go to first/last scan
- **Page Up/Down** - Previous/next page
- **M** - Add marker mode
- **R** - Reset zoom

### Filtering Data
Use the filter controls at the top to narrow down your data:
- **Center Frequency** - Filter by exact center frequency
- **Config Name** - Search by configuration name (partial matches)
- **Instance** - Filter by analyzer instance name
- **Time Range** - Select from predefined time ranges

### Analysis Tools
1. **Select Analysis Preset** - Choose from peak detection, signal analysis, or interference detection
2. **Click Analyze** - Apply the selected analysis to the current scan
3. **View Results** - Analysis results appear in the right panel

### Markers
1. **Click on Spectrum** - Click any point on the spectrum plot to add a marker
2. **Fill Marker Details** - Enter name, type, and optional notes
3. **Save Marker** - Marker will be stored and displayed on the plot
4. **Manage Markers** - View, edit, or delete markers in the markers panel

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `FLASK_ENV` - Flask environment (development/production)

### TimescaleDB Configuration
The database is automatically optimized for time-series data with:
- Hypertable partitioning on `scan_time`
- Indexes on commonly queried fields
- GIN indexes for JSONB configuration searches

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask App     │    │   TimescaleDB   │
│                 │◄──►│                 │◄──►│                 │
│ - Interactive   │    │ - REST API      │    │ - Time-series   │
│   Spectrum Plot │    │ - WebSockets    │    │   optimization  │
│ - Controls      │    │ - Analysis      │    │ - JSONB config  │
│ - Keyboard      │    │   Tools         │    │ - Markers       │
│   Navigation    │    │ - Markers       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📡 API Endpoints

### Scans
- `GET /api/scans` - List scans with filtering and pagination
- `GET /api/scans/<scan_id>` - Get specific scan details
- `GET /api/scans/navigate` - Navigate between scans

### Visualization
- `GET /api/plot/<scan_id>` - Get plot data for specific scan

### Analysis
- `GET /api/analysis/presets` - List available analysis presets
- `GET /api/analysis/apply/<scan_id>` - Apply analysis to scan

### Markers
- `POST /api/markers` - Create new marker
- `DELETE /api/markers/<marker_id>` - Delete marker

## 🔬 Analysis Presets

### Peak Detection
Automatically detects signal peaks with configurable parameters:
- Threshold (dBm)
- Minimum distance between peaks
- Prominence requirements

### Signal Analysis
Provides comprehensive signal statistics:
- Overall power statistics (max, min, mean, std dev)
- Frequency band analysis
- Signal characterization

### Interference Detection
Identifies potential interference sources:
- Baseline calculation with rolling window
- Threshold-based detection
- Interference source grouping

## 🚀 Performance Features

- **TimescaleDB Optimization** - Automatic time-series partitioning and compression
- **Efficient Queries** - Optimized database indexes for fast filtering
- **WebSocket Updates** - Real-time data streaming without polling
- **Responsive UI** - Modern CSS with hardware acceleration
- **Pagination** - Efficient handling of large datasets

## 📈 Monitoring & Observability

The application includes Grafana integration for monitoring:
- Scan volume over time
- Frequency band usage analysis
- Instance performance metrics
- Signal quality trends

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Future Enhancements

- [ ] Real-time spectrum streaming from hardware analyzers
- [ ] Machine learning-based signal classification
- [ ] Advanced signal processing algorithms
- [ ] Multi-user support with role-based access
- [ ] Data export capabilities (CSV, JSON, MATLAB)
- [ ] Custom dashboard creation
- [ ] Alert system for signal anomalies
- [ ] Integration with external spectrum analyzers

---

Built with ❤️ for the RF engineering community