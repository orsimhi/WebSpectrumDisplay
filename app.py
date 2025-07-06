from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
import plotly.graph_objects as go
import plotly.utils
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rf_amplitude_viewer_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "rf-amplitude-token"
INFLUXDB_ORG = "rf-org"
INFLUXDB_BUCKET = "rf-amplitude-data"

# Global InfluxDB client
influx_client = None

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
                |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
                |> count()
            '''
            
            try:
                result = query_api.query(query)
                has_data = any(len(table.records) > 0 for table in result)
                
                if not has_data:
                    print("No RF data found, creating sample data...")
                    create_sample_data()
                else:
                    print("✓ RF data found in database")
                    
            except Exception as e:
                print(f"Creating sample data (query error: {e})")
                create_sample_data()
                
        else:
            raise Exception(f"InfluxDB health check failed: {health.status}")
            
    except Exception as e:
        print(f"⚠ InfluxDB not available ({e}), falling back to mock data mode")
        influx_client = None

def create_sample_data():
    """Create sample RF amplitude data in InfluxDB"""
    if not influx_client:
        return
        
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    
    print("Creating sample RF amplitude data...")
    
    # Generate sample data over the last 24 hours
    import random
    base_time = datetime.now(timezone.utc)
    
    for i in range(100):  # Create 100 sample measurements
        # Create timestamp (spread over last 24 hours)
        timestamp = base_time - pd.Timedelta(hours=24-i*0.24)
        
        # Generate realistic RF parameters
        center_frequency = 2400.0 + random.uniform(-50, 50)  # MHz
        span = 100.0  # MHz
        
        # Generate realistic RF power data (in dBm)
        num_points = 1000
        frequencies = np.linspace(center_frequency - span/2, center_frequency + span/2, num_points)
        
        # Create realistic RF spectrum with noise and signals
        powers = -80 + 10 * np.random.randn(num_points)  # Base noise floor
        
        # Add some signal peaks
        for _ in range(random.randint(1, 3)):
            peak_freq = random.uniform(center_frequency - span/3, center_frequency + span/3)
            peak_idx = int((peak_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
            if 0 <= peak_idx < num_points:
                peak_power = random.uniform(-40, -20)
                width = random.randint(5, 20)
                for j in range(max(0, peak_idx - width), min(num_points, peak_idx + width)):
                    powers[j] = max(powers[j], peak_power - abs(j - peak_idx) * 0.5)
        
        # Create InfluxDB point
        point = Point("rf_amplitude") \
            .tag("device_id", "spectrum_analyzer_001") \
            .tag("location", "lab_1") \
            .field("center_frequency", center_frequency) \
            .field("span", span) \
            .field("powers", json.dumps(powers.tolist())) \
            .field("num_points", num_points) \
            .time(timestamp, WritePrecision.NS)
        
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    
    print(f"✓ Created 100 sample RF measurements")

def get_mock_data():
    """Return mock data when InfluxDB is not available"""
    mock_records = []
    base_time = datetime.now(timezone.utc)
    
    for i in range(10):
        timestamp = base_time - pd.Timedelta(minutes=i*5)
        center_freq = 2400.0 + np.random.uniform(-50, 50)
        span = 100.0
        powers = (-80 + 10 * np.random.randn(1000)).tolist()
        
        mock_records.append({
            'id': f'mock_{i}',
            'timestamp': timestamp.isoformat(),
            'center_frequency': center_freq,
            'span': span,
            'powers': powers,
            'device_id': 'mock_device'
        })
    
    return mock_records

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rf_data')
def get_rf_data():
    """Get RF amplitude records with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not influx_client:
        # Return mock data if InfluxDB not available
        records = get_mock_data()
        return jsonify({
            'records': records[:per_page],
            'page': page,
            'per_page': per_page,
            'total': len(records),
            'has_next': len(records) > per_page,
            'has_prev': page > 1
        })
    
    try:
        query_api = influx_client.query_api()
        
        # Build time range
        if not start_time:
            start_time = "-24h"
        if not end_time:
            end_time = "now()"
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: {per_page}, offset: {offset})
        '''
        
        result = query_api.query(query)
        records = []
        
        for table in result:
            for record in table.records:
                rf_record = {
                    'id': f"{record.get_time().timestamp()}",
                    'timestamp': record.get_time().isoformat(),
                    'center_frequency': record.values.get('center_frequency', 0),
                    'span': record.values.get('span', 0),
                    'powers': json.loads(record.values.get('powers', '[]')),
                    'device_id': record.values.get('device_id', 'unknown')
                }
                records.append(rf_record)
        
        # Get total count for pagination
        count_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
            |> count()
        '''
        
        count_result = query_api.query(count_query)
        total = 0
        for table in count_result:
            for record in table.records:
                total = record.get_value()
                break
        
        return jsonify({
            'records': records,
            'page': page,
            'per_page': per_page,
            'total': total,
            'has_next': (page * per_page) < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return jsonify({'error': 'Database query failed'}), 500

@app.route('/api/rf_data/<record_id>')
def get_rf_record(record_id):
    """Get specific RF amplitude record"""
    if not influx_client:
        # Return mock data
        mock_data = get_mock_data()
        for record in mock_data:
            if record['id'] == record_id:
                return jsonify(record)
        return jsonify({'error': 'Record not found'}), 404
    
    try:
        # Convert record_id back to timestamp
        timestamp = datetime.fromtimestamp(float(record_id), tz=timezone.utc)
        
        query_api = influx_client.query_api()
        query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {timestamp.isoformat()}, stop: {(timestamp + pd.Timedelta(seconds=1)).isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = query_api.query(query)
        
        for table in result:
            for record in table.records:
                rf_record = {
                    'id': record_id,
                    'timestamp': record.get_time().isoformat(),
                    'center_frequency': record.values.get('center_frequency', 0),
                    'span': record.values.get('span', 0),
                    'powers': json.loads(record.values.get('powers', '[]')),
                    'device_id': record.values.get('device_id', 'unknown')
                }
                return jsonify(rf_record)
        
        return jsonify({'error': 'Record not found'}), 404
        
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return jsonify({'error': 'Database query failed'}), 500

@app.route('/api/plot/<record_id>')
def get_plot_data(record_id):
    """Generate plot data for a specific record"""
    try:
        # Get the record data
        record_response = get_rf_record(record_id)
        if record_response.status_code != 200:
            return record_response
        
        record_data = record_response.get_json()
        
        center_freq = record_data['center_frequency']
        span = record_data['span']
        powers = record_data['powers']
        timestamp = record_data['timestamp']
        
        # Calculate frequency axis
        num_points = len(powers)
        start_freq = center_freq - span / 2
        end_freq = center_freq + span / 2
        frequencies = np.linspace(start_freq, end_freq, num_points)
        
        # Create Plotly figure
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=frequencies.tolist(),
            y=powers,
            mode='lines',
            name='RF Amplitude',
            line=dict(color='blue', width=1)
        ))
        
        fig.update_layout(
            title=f'RF Amplitude - {timestamp}',
            xaxis_title='Frequency (MHz)',
            yaxis_title='Power (dBm)',
            hovermode='x unified',
            showlegend=True,
            height=600,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Convert to JSON
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'plot': graphJSON,
            'center_frequency': center_freq,
            'span': span,
            'timestamp': timestamp,
            'frequencies': frequencies.tolist(),
            'powers': powers
        })
        
    except Exception as e:
        print(f"Error generating plot: {e}")
        return jsonify({'error': 'Plot generation failed'}), 500

@app.route('/api/live_data')
def get_live_data():
    """Get the latest RF data for real-time updates"""
    if not influx_client:
        return jsonify(get_mock_data()[:1])
    
    try:
        query_api = influx_client.query_api()
        query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1m)
            |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 1)
        '''
        
        result = query_api.query(query)
        records = []
        
        for table in result:
            for record in table.records:
                rf_record = {
                    'id': f"{record.get_time().timestamp()}",
                    'timestamp': record.get_time().isoformat(),
                    'center_frequency': record.values.get('center_frequency', 0),
                    'span': record.values.get('span', 0),
                    'powers': json.loads(record.values.get('powers', '[]')),
                    'device_id': record.values.get('device_id', 'unknown')
                }
                records.append(rf_record)
        
        return jsonify(records)
        
    except Exception as e:
        print(f"Error getting live data: {e}")
        return jsonify([])

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'msg': 'Connected to RF Amplitude Viewer'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_live_update')
def handle_live_update_request():
    """Send live data update to client"""
    try:
        live_data = get_live_data()
        emit('live_data_update', live_data.get_json())
    except Exception as e:
        emit('error', {'msg': f'Live update failed: {e}'})

# Background thread for periodic updates
def background_thread():
    """Send periodic updates to connected clients"""
    while True:
        time.sleep(5)  # Update every 5 seconds
        try:
            if influx_client:
                live_data = get_live_data()
                socketio.emit('live_data_update', live_data.get_json())
        except Exception as e:
            print(f"Background update error: {e}")
        time.sleep(5)

# Start background thread
thread = threading.Thread(target=background_thread)
thread.daemon = True

if __name__ == '__main__':
    print("Starting RF Amplitude Graph Viewer with Time-Series Database...")
    print("=" * 60)
    
    # Initialize InfluxDB
    init_influxdb()
    
    # Start background thread
    thread.start()
    
    print("\nStarting Flask-SocketIO server...")
    print("Application available at: http://localhost:5000")
    print("Features:")
    print("  • Time-series database storage (InfluxDB)")
    print("  • Real-time data updates via WebSockets")
    print("  • Pagination support for large datasets")
    print("  • NDJSON data format support")
    print("  • Automatic data loading")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)