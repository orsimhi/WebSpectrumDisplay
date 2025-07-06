from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.utils

app = Flask(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('rf_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rf_amplitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            center_frequency REAL NOT NULL,
            span REAL NOT NULL,
            powers TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM rf_amplitudes')
    if cursor.fetchone()[0] == 0:
        insert_sample_data(cursor)
    
    conn.commit()
    conn.close()

def insert_sample_data(cursor):
    """Insert sample RF amplitude data"""
    import random
    
    # Generate sample data
    for i in range(50):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        
        powers_json = json.dumps(powers.tolist())
        
        cursor.execute('''
            INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, center_frequency, span, powers_json))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rf_data')
def get_rf_data():
    """Get all RF amplitude records"""
    conn = sqlite3.connect('rf_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, timestamp, center_frequency, span, powers 
        FROM rf_amplitudes 
        ORDER BY timestamp DESC
    ''')
    
    records = []
    for row in cursor.fetchall():
        record = {
            'id': row[0],
            'timestamp': row[1],
            'center_frequency': row[2],
            'span': row[3],
            'powers': json.loads(row[4])
        }
        records.append(record)
    
    conn.close()
    return jsonify(records)

@app.route('/api/rf_data/<int:record_id>')
def get_rf_record(record_id):
    """Get specific RF amplitude record"""
    conn = sqlite3.connect('rf_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, timestamp, center_frequency, span, powers 
        FROM rf_amplitudes 
        WHERE id = ?
    ''', (record_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        record = {
            'id': row[0],
            'timestamp': row[1],
            'center_frequency': row[2],
            'span': row[3],
            'powers': json.loads(row[4])
        }
        return jsonify(record)
    else:
        return jsonify({'error': 'Record not found'}), 404

@app.route('/api/plot/<int:record_id>')
def get_plot_data(record_id):
    """Generate plot data for a specific record"""
    conn = sqlite3.connect('rf_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, center_frequency, span, powers 
        FROM rf_amplitudes 
        WHERE id = ?
    ''', (record_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Record not found'}), 404
    
    timestamp, center_freq, span, powers_json = row
    powers = json.loads(powers_json)
    
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)