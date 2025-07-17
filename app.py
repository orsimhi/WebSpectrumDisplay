from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go
import plotly.utils
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import threading
import time
import os
import sqlite3
from scipy import signal
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rf_spectrum_analyzer_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "rf-spectrum-token"
INFLUXDB_ORG = "rf-org"
INFLUXDB_BUCKET = "rf-spectrum-data"

# Global variables
influx_client = None
auto_play = False
current_record_index = 0

def init_influxdb():
    """Initialize InfluxDB connection and create sample data if needed"""
    global influx_client
    
    try:
        # Try to connect to InfluxDB
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Test connection
        health = influx_client.health()
        if health.status == "pass":
            print("✓ Connected to InfluxDB successfully")
            
            # Check if we have data, if not create sample data
            query_api = influx_client.query_api()
            query = f'''
                from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "rf_spectrum")
                |> count()
            '''
            
            result = query_api.query(query)
            data_exists = False
            for table in result:
                for record in table.records:
                    if record.get_value() > 0:
                        data_exists = True
                        break
            
            if not data_exists:
                print("No data found, creating sample RF spectrum data...")
                create_sample_data()
            else:
                print("✓ RF spectrum data found in InfluxDB")
                
        else:
            print("❌ InfluxDB connection failed")
            
    except Exception as e:
        print(f"❌ InfluxDB connection error: {e}")
        print("Falling back to SQLite database...")
        init_sqlite_fallback()

def init_sqlite_fallback():
    """Initialize SQLite database as fallback"""
    conn = sqlite3.connect('rf_spectrum.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rf_spectrum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            frequency REAL,
            power REAL,
            device_id TEXT,
            measurement_type TEXT,
            bandwidth REAL,
            gain REAL
        )
    ''')
    
    # Check if we have data
    cursor.execute('SELECT COUNT(*) FROM rf_spectrum')
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Creating sample RF spectrum data in SQLite...")
        create_sample_sqlite_data(conn)
    
    conn.close()
    print("✓ SQLite fallback database initialized")

def create_sample_data():
    """Create comprehensive sample RF spectrum data in InfluxDB"""
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    
    # Generate multiple RF spectrum sweeps
    num_sweeps = 50
    start_freq = 2.4e9  # 2.4 GHz
    end_freq = 2.5e9    # 2.5 GHz
    num_points = 1000
    
    base_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    for sweep_idx in range(num_sweeps):
        timestamp = base_time + timedelta(seconds=sweep_idx * 5)
        frequencies = np.linspace(start_freq, end_freq, num_points)
        
        # Generate realistic RF spectrum with signals
        noise_floor = -90  # dBm
        powers = np.random.normal(noise_floor, 2, num_points)
        
        # Add some realistic signals
        # WiFi channel signal
        wifi_center = 2.437e9
        wifi_bw = 20e6
        wifi_mask = np.exp(-((frequencies - wifi_center) / (wifi_bw/4))**2)
        powers += wifi_mask * 30  # 30 dB above noise floor
        
        # Bluetooth signal
        bt_center = 2.442e9
        bt_bw = 1e6
        bt_mask = np.exp(-((frequencies - bt_center) / (bt_bw/4))**2)
        powers += bt_mask * 15  # 15 dB above noise floor
        
        # Microwave oven interference (if present)
        if sweep_idx % 10 == 0:  # Intermittent interference
            mw_center = 2.45e9
            mw_bw = 50e6
            mw_mask = np.exp(-((frequencies - mw_center) / (mw_bw/4))**2)
            powers += mw_mask * 40  # Strong interference
        
        # Write data points
        points = []
        for freq, power in zip(frequencies, powers):
            point = Point("rf_spectrum") \
                .tag("device_id", f"SDR-{sweep_idx % 3 + 1}") \
                .tag("measurement_type", "spectrum_sweep") \
                .field("frequency", float(freq)) \
                .field("power", float(power)) \
                .field("bandwidth", 100000.0) \
                .field("gain", 20.0) \
                .time(timestamp, WritePrecision.NS)
            points.append(point)
        
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
        
        if sweep_idx % 10 == 0:
            print(f"Created {sweep_idx + 1}/{num_sweeps} spectrum sweeps...")
    
    print("✓ Sample RF spectrum data created successfully")

def create_sample_sqlite_data(conn):
    """Create sample RF spectrum data in SQLite"""
    cursor = conn.cursor()
    
    # Generate sample data similar to InfluxDB version
    num_sweeps = 20
    start_freq = 2.4e9
    end_freq = 2.5e9
    num_points = 500  # Fewer points for SQLite
    
    base_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    for sweep_idx in range(num_sweeps):
        timestamp = base_time + timedelta(seconds=sweep_idx * 10)
        frequencies = np.linspace(start_freq, end_freq, num_points)
        
        noise_floor = -90
        powers = np.random.normal(noise_floor, 2, num_points)
        
        # Add WiFi signal
        wifi_center = 2.437e9
        wifi_bw = 20e6
        wifi_mask = np.exp(-((frequencies - wifi_center) / (wifi_bw/4))**2)
        powers += wifi_mask * 30
        
        for freq, power in zip(frequencies, powers):
            cursor.execute('''
                INSERT INTO rf_spectrum 
                (timestamp, frequency, power, device_id, measurement_type, bandwidth, gain)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(),
                float(freq),
                float(power),
                f"SDR-{sweep_idx % 2 + 1}",
                "spectrum_sweep",
                100000.0,
                20.0
            ))
    
    conn.commit()
    print("✓ Sample SQLite data created")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/spectrum_data')
def get_spectrum_data():
    """Get RF spectrum data for plotting"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 1))
    
    try:
        if influx_client:
            return get_influx_spectrum_data(page, per_page)
        else:
            return get_sqlite_spectrum_data(page, per_page)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_influx_spectrum_data(page, per_page):
    """Get spectrum data from InfluxDB"""
    query_api = influx_client.query_api()
    
    # Get unique timestamps first
    timestamp_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -24h)
        |> filter(fn: (r) => r["_measurement"] == "rf_spectrum")
        |> group(columns: ["_time"])
        |> first()
        |> keep(columns: ["_time"])
        |> sort(columns: ["_time"], desc: true)
    '''
    
    timestamp_result = query_api.query(timestamp_query)
    timestamps = []
    for table in timestamp_result:
        for record in table.records:
            timestamps.append(record.get_time())
    
    if not timestamps:
        return jsonify({"error": "No data found"}), 404
    
    # Calculate pagination
    total_records = len(timestamps)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    if start_idx >= total_records:
        return jsonify({"error": "Page out of range"}), 404
    
    # Get the specific timestamp for this page
    target_timestamp = timestamps[start_idx:end_idx]
    
    if not target_timestamp:
        return jsonify({"error": "No data for this page"}), 404
    
    # Get spectrum data for the first timestamp on this page
    time_str = target_timestamp[0].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    data_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {time_str}, stop: {time_str})
        |> filter(fn: (r) => r["_measurement"] == "rf_spectrum")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    data_result = query_api.query(data_query)
    
    frequencies = []
    powers = []
    metadata = {}
    
    for table in data_result:
        for record in table.records:
            frequencies.append(record.values.get('frequency', 0))
            powers.append(record.values.get('power', 0))
            if not metadata:
                metadata = {
                    'timestamp': record.get_time().isoformat(),
                    'device_id': record.values.get('device_id', 'unknown'),
                    'measurement_type': record.values.get('measurement_type', 'spectrum'),
                    'bandwidth': record.values.get('bandwidth', 0),
                    'gain': record.values.get('gain', 0)
                }
    
    # Sort by frequency
    if frequencies and powers:
        sorted_data = sorted(zip(frequencies, powers))
        frequencies, powers = zip(*sorted_data)
    
    return jsonify({
        'frequencies': list(frequencies),
        'powers': list(powers),
        'metadata': metadata,
        'pagination': {
            'current_page': page,
            'total_pages': math.ceil(total_records / per_page),
            'total_records': total_records,
            'per_page': per_page
        }
    })

def get_sqlite_spectrum_data(page, per_page):
    """Get spectrum data from SQLite"""
    conn = sqlite3.connect('rf_spectrum.db')
    cursor = conn.cursor()
    
    # Get unique timestamps
    cursor.execute('''
        SELECT DISTINCT timestamp 
        FROM rf_spectrum 
        ORDER BY timestamp DESC
    ''')
    timestamps = [row[0] for row in cursor.fetchall()]
    
    if not timestamps:
        conn.close()
        return jsonify({"error": "No data found"}), 404
    
    # Calculate pagination
    total_records = len(timestamps)
    start_idx = (page - 1) * per_page
    
    if start_idx >= total_records:
        conn.close()
        return jsonify({"error": "Page out of range"}), 404
    
    target_timestamp = timestamps[start_idx]
    
    # Get spectrum data for this timestamp
    cursor.execute('''
        SELECT frequency, power, device_id, measurement_type, bandwidth, gain, timestamp
        FROM rf_spectrum 
        WHERE timestamp = ?
        ORDER BY frequency
    ''', (target_timestamp,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return jsonify({"error": "No data for this timestamp"}), 404
    
    frequencies = [row[0] for row in rows]
    powers = [row[1] for row in rows]
    
    metadata = {
        'timestamp': rows[0][6],
        'device_id': rows[0][2],
        'measurement_type': rows[0][3],
        'bandwidth': rows[0][4],
        'gain': rows[0][5]
    }
    
    return jsonify({
        'frequencies': frequencies,
        'powers': powers,
        'metadata': metadata,
        'pagination': {
            'current_page': page,
            'total_pages': math.ceil(total_records / per_page),
            'total_records': total_records,
            'per_page': per_page
        }
    })

@app.route('/api/analysis/peak_detection')
def peak_detection():
    """Perform peak detection analysis on current spectrum"""
    page = int(request.args.get('page', 1))
    threshold = float(request.args.get('threshold', -70))  # dBm threshold
    
    # Get current spectrum data
    try:
        if influx_client:
            data_response = get_influx_spectrum_data(page, 1)
        else:
            data_response = get_sqlite_spectrum_data(page, 1)
        
        data = data_response.get_json()
        if 'error' in data:
            return jsonify(data), 500
        
        frequencies = np.array(data['frequencies'])
        powers = np.array(data['powers'])
        
        # Find peaks above threshold
        peaks, properties = signal.find_peaks(powers, height=threshold, distance=10)
        
        peak_data = []
        for i, peak_idx in enumerate(peaks):
            peak_data.append({
                'frequency': frequencies[peak_idx],
                'power': powers[peak_idx],
                'prominence': properties.get('prominences', [0])[i] if 'prominences' in properties else 0,
                'width': properties.get('widths', [0])[i] if 'widths' in properties else 0
            })
        
        # Sort by power (strongest first)
        peak_data.sort(key=lambda x: x['power'], reverse=True)
        
        return jsonify({
            'peaks': peak_data,
            'analysis': {
                'total_peaks': len(peak_data),
                'strongest_signal': peak_data[0] if peak_data else None,
                'average_power': float(np.mean(powers)),
                'noise_floor': float(np.percentile(powers, 10)),
                'dynamic_range': float(np.max(powers) - np.min(powers))
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/occupancy')
def spectrum_occupancy():
    """Calculate spectrum occupancy statistics"""
    page = int(request.args.get('page', 1))
    threshold = float(request.args.get('threshold', -80))  # dBm threshold
    
    try:
        if influx_client:
            data_response = get_influx_spectrum_data(page, 1)
        else:
            data_response = get_sqlite_spectrum_data(page, 1)
        
        data = data_response.get_json()
        if 'error' in data:
            return jsonify(data), 500
        
        frequencies = np.array(data['frequencies'])
        powers = np.array(data['powers'])
        
        # Calculate occupancy
        occupied_mask = powers > threshold
        occupied_freqs = frequencies[occupied_mask]
        
        total_bandwidth = frequencies[-1] - frequencies[0]
        occupied_bandwidth = np.sum(np.diff(frequencies)[:-1][occupied_mask[:-1]])
        occupancy_percentage = (occupied_bandwidth / total_bandwidth) * 100
        
        # Find occupied bands
        bands = []
        if len(occupied_freqs) > 0:
            # Group consecutive frequency points
            freq_diff = np.diff(frequencies)[0]  # Assume uniform spacing
            breaks = np.where(np.diff(occupied_freqs) > freq_diff * 2)[0]
            
            start_indices = [0] + list(breaks + 1)
            end_indices = list(breaks) + [len(occupied_freqs) - 1]
            
            for start_idx, end_idx in zip(start_indices, end_indices):
                bands.append({
                    'start_freq': occupied_freqs[start_idx],
                    'end_freq': occupied_freqs[end_idx],
                    'bandwidth': occupied_freqs[end_idx] - occupied_freqs[start_idx],
                    'center_freq': (occupied_freqs[start_idx] + occupied_freqs[end_idx]) / 2
                })
        
        return jsonify({
            'occupancy_percentage': occupancy_percentage,
            'total_bandwidth': total_bandwidth,
            'occupied_bandwidth': occupied_bandwidth,
            'occupied_bands': bands,
            'statistics': {
                'threshold_dbm': threshold,
                'points_above_threshold': int(np.sum(occupied_mask)),
                'total_points': len(powers)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to RF Spectrum Analyzer'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('toggle_autoplay')
def handle_toggle_autoplay():
    """Toggle auto-play mode"""
    global auto_play
    auto_play = not auto_play
    emit('autoplay_status', {'enabled': auto_play})
    
    if auto_play:
        start_autoplay()

def start_autoplay():
    """Start auto-play in a separate thread"""
    def autoplay_loop():
        global auto_play, current_record_index
        while auto_play:
            time.sleep(2)  # 2 second interval
            if auto_play:  # Check again in case it was toggled
                current_record_index += 1
                socketio.emit('autoplay_next', {'index': current_record_index})
    
    thread = threading.Thread(target=autoplay_loop)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    print("🚀 Starting RF Spectrum Analyzer...")
    init_influxdb()
    print("🌐 Starting web server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)