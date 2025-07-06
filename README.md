# RF Amplitude Graph Viewer

A modern Python web application for visualizing and analyzing RF (Radio Frequency) amplitude data with interactive graphs, navigation controls, and marker functionality.

## Features

### 📊 Interactive Graphs
- **Plotly.js Integration**: High-performance, responsive plotting with zoom, pan, and scaling
- **Real-time Interaction**: Hover for frequency/power details
- **Zoom Controls**: Built-in zoom, pan, and reset functionality

### 🎯 Marker System
- **Click-to-Add**: Click anywhere on the graph to place markers
- **Marker Management**: View all markers with frequency, power, and record information
- **Persistent Markers**: Markers remain when navigating between records
- **Easy Removal**: Remove individual markers or clear all at once

### 🎮 Navigation Controls
- **Button Navigation**: First, Previous, Next, Last record buttons
- **Auto-Play**: Automatic progression through records with adjustable speed
- **Hold-to-Navigate**: Hold Previous/Next buttons for fast navigation
- **Keyboard Shortcuts**:
  - `Arrow Left/Right`: Navigate between records
  - `Space`: Toggle auto-play
  - `Home/End`: Go to first/last record
  - `Escape`: Reset zoom
  - `M`: Toggle marker mode
  - `C`: Clear all markers

### 📱 Modern UI
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark Theme**: Professional appearance with gradient backgrounds
- **Real-time Info**: Display current record info (timestamp, center frequency, span)
- **Status Updates**: Visual feedback for all actions

### 🗄️ Database Integration
- **SQLite Database**: Efficient storage and retrieval of RF data
- **Timestamped Records**: Track when measurements were taken
- **Flexible Schema**: Supports various RF measurement formats

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup
1. **Clone or download the project files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

## Data Structure

The application expects RF data with the following structure:

```python
{
    "timestamp": "2024-01-01 12:00:00",
    "center_frequency": 2400.0,  # MHz
    "span": 100.0,               # MHz  
    "powers": [...]              # Array of power values in dBm
}
```

- **Timestamp**: When the measurement was taken
- **Center Frequency**: The center frequency of the measurement in MHz
- **Span**: The frequency span of the measurement in MHz
- **Powers**: Array of power measurements in dBm for the y-axis
- **X-axis**: Automatically calculated from center frequency and span

## Data Migration

If you have existing RF data in files, you can create a migration script:

```python
# migrate_data.py
import sqlite3
import json
from datetime import datetime

def migrate_file_data(file_path):
    """
    Example migration function for your existing data files
    Modify this based on your current data format
    """
    conn = sqlite3.connect('rf_data.db')
    cursor = conn.cursor()
    
    # Read your existing data file
    with open(file_path, 'r') as f:
        data = json.load(f)  # Adjust based on your file format
    
    # Insert into database
    for record in data:
        cursor.execute('''
            INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
            VALUES (?, ?, ?, ?)
        ''', (
            record['timestamp'],
            record['center_frequency'],
            record['span'],
            json.dumps(record['powers'])
        ))
    
    conn.commit()
    conn.close()

# Usage
# migrate_file_data('your_rf_data.json')
```

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