from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
import plotly.graph_objects as go
import plotly.utils
import threading
import time
import os
import uuid
import logging
from pathlib import Path
from sqlalchemy import text, desc, and_, or_
from sqlalchemy.orm import joinedload

from models import db, RFScan, AnalysisPreset, ScanMarker
from analysis_tools import RFAnalysisTools

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rf_spectrum_analyzer_secret'

# Database configuration - Windows friendly paths
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db'
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Configure logging for Windows
def setup_logging():
    """Setup logging configuration for Windows"""
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'rf_analyzer.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

def init_database():
    """Initialize database and create sample data if needed"""
    with app.app_context():
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            logger.info("✓ Connected to TimescaleDB successfully")
            
            # Check if we have data
            scan_count = db.session.query(RFScan).count()
            if scan_count == 0:
                logger.info("No RF scan data found, database is ready for data generation")
                logger.info("Run 'python sample_data_generator.py' to create sample data")
            else:
                logger.info(f"✓ Found {scan_count} RF scans in database")
                
        except Exception as e:
            logger.error(f"⚠ Database error: {e}")
            logger.info("Make sure TimescaleDB is running and accessible")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scans')
def get_scans():
    """Get RF scans with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    cf_filter = request.args.get('cf')  # Filter by config_info->>'cf'
    name_filter = request.args.get('name')  # Filter by config_info->>'name'
    instance_filter = request.args.get('instance')
    
    try:
        query = db.session.query(RFScan).options(joinedload(RFScan.markers))
        
        # Apply time range filters
        if start_time:
            start_dt = pd.to_datetime(start_time).tz_localize('UTC')
            query = query.filter(RFScan.scan_time >= start_dt)
        if end_time:
            end_dt = pd.to_datetime(end_time).tz_localize('UTC')
            query = query.filter(RFScan.scan_time <= end_dt)
        
        # Apply config filters
        if cf_filter:
            query = query.filter(RFScan.config_info['cf'].astext == cf_filter)
        if name_filter:
            query = query.filter(RFScan.config_info['name'].astext.ilike(f'%{name_filter}%'))
        if instance_filter:
            query = query.filter(RFScan.instance_name.ilike(f'%{instance_filter}%'))
        
        # Order by scan_time descending (most recent first)
        query = query.order_by(desc(RFScan.scan_time))
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        scans = []
        for scan in paginated.items:
            scan_dict = scan.to_dict()
            # Add frequency axis for convenience
            scan_dict['frequencies'] = RFAnalysisTools.calculate_frequency_axis(
                scan.center_frequency, scan.span, len(scan.powers)
            )
            scans.append(scan_dict)
        
        return jsonify({
            'scans': scans,
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        })
        
    except Exception as e:
        logger.error(f"Error querying scans: {e}")
        return jsonify({'error': 'Database query failed'}), 500

@app.route('/api/scans/<scan_id>')
def get_scan(scan_id):
    """Get specific RF scan by ID"""
    try:
        scan = db.session.query(RFScan).options(joinedload(RFScan.markers)).filter_by(scan_id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        scan_dict = scan.to_dict()
        scan_dict['frequencies'] = RFAnalysisTools.calculate_frequency_axis(
            scan.center_frequency, scan.span, len(scan.powers)
        )
        scan_dict['markers'] = [marker.to_dict() for marker in scan.markers]
        
        return jsonify(scan_dict)
        
    except Exception as e:
        logger.error(f"Error getting scan: {e}")
        return jsonify({'error': 'Database query failed'}), 500

@app.route('/api/scans/navigate')
def navigate_scans():
    """Navigate between scans (previous/next) for keyboard navigation"""
    current_scan_time = request.args.get('current_time')
    direction = request.args.get('direction', 'next')  # 'next' or 'prev'
    
    if not current_scan_time:
        return jsonify({'error': 'current_time parameter required'}), 400
    
    try:
        current_dt = pd.to_datetime(current_scan_time).tz_localize('UTC')
        
        if direction == 'next':
            # Get next scan (newer)
            scan = db.session.query(RFScan).filter(
                RFScan.scan_time > current_dt
            ).order_by(RFScan.scan_time.asc()).first()
        else:
            # Get previous scan (older)
            scan = db.session.query(RFScan).filter(
                RFScan.scan_time < current_dt
            ).order_by(RFScan.scan_time.desc()).first()
        
        if not scan:
            return jsonify({'error': 'No more scans in that direction'}), 404
        
        return jsonify({
            'scan_id': str(scan.scan_id),
            'scan_time': scan.scan_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error navigating scans: {e}")
        return jsonify({'error': 'Navigation failed'}), 500

@app.route('/api/plot/<scan_id>')
def get_plot_data(scan_id):
    """Generate plot data for a specific scan"""
    try:
        scan = db.session.query(RFScan).options(joinedload(RFScan.markers)).filter_by(scan_id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        # Calculate frequency axis
        frequencies = RFAnalysisTools.calculate_frequency_axis(
            scan.center_frequency, scan.span, len(scan.powers)
        )
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Main spectrum trace
        fig.add_trace(go.Scatter(
            x=frequencies,
            y=scan.powers,
            mode='lines',
            name='RF Spectrum',
            line=dict(color='blue', width=1),
            hovertemplate='Frequency: %{x:.2f} MHz<br>Power: %{y:.2f} dBm<extra></extra>'
        ))
        
        # Add markers if they exist
        for marker in scan.markers:
            fig.add_trace(go.Scatter(
                x=[marker.frequency_mhz],
                y=[marker.power_dbm],
                mode='markers+text',
                name=marker.marker_name,
                marker=dict(size=10, symbol='diamond'),
                text=marker.marker_name,
                textposition='top center',
                hovertemplate=f'{marker.marker_name}<br>Frequency: %{{x:.2f}} MHz<br>Power: %{{y:.2f}} dBm<br>Type: {marker.marker_type}<extra></extra>'
            ))
        
        fig.update_layout(
            title=f'RF Spectrum - {scan.scan_time.strftime("%Y-%m-%d %H:%M:%S UTC")} - {scan.name}',
            xaxis_title='Frequency (MHz)',
            yaxis_title='Power (dBm)',
            hovermode='x unified',
            showlegend=True,
            height=600,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Convert to JSON
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'plot': graphJSON,
            'scan_info': scan.to_dict(),
            'frequencies': frequencies,
            'powers': scan.powers
        })
        
    except Exception as e:
        logger.error(f"Error generating plot: {e}")
        return jsonify({'error': 'Plot generation failed'}), 500

@app.route('/api/analysis/presets')
def get_analysis_presets():
    """Get all analysis presets"""
    try:
        presets = db.session.query(AnalysisPreset).all()
        return jsonify([preset.to_dict() for preset in presets])
    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        return jsonify({'error': 'Failed to get presets'}), 500

@app.route('/api/analysis/apply/<scan_id>')
def apply_analysis(scan_id):
    """Apply analysis preset to a scan"""
    preset_id = request.args.get('preset_id', type=int)
    
    if not preset_id:
        return jsonify({'error': 'preset_id parameter required'}), 400
    
    try:
        # Get scan and preset
        scan = db.session.query(RFScan).filter_by(scan_id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        preset = db.session.query(AnalysisPreset).filter_by(id=preset_id).first()
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Calculate frequency axis
        frequencies = RFAnalysisTools.calculate_frequency_axis(
            scan.center_frequency, scan.span, len(scan.powers)
        )
        
        # Apply analysis
        analysis_result = RFAnalysisTools.apply_analysis_preset(
            scan.powers, frequencies, preset.preset_config
        )
        
        return jsonify({
            'preset_name': preset.name,
            'scan_id': scan_id,
            'analysis': analysis_result
        })
        
    except Exception as e:
        logger.error(f"Error applying analysis: {e}")
        return jsonify({'error': 'Analysis failed'}), 500

@app.route('/api/markers', methods=['POST'])
def add_marker():
    """Add a marker to a scan"""
    data = request.get_json()
    
    required_fields = ['scan_id', 'marker_name', 'frequency_mhz', 'power_dbm']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Get the scan to validate it exists and get scan_time
        scan = db.session.query(RFScan).filter_by(scan_id=data['scan_id']).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        # Create marker
        marker = ScanMarker(
            scan_time=scan.scan_time,
            scan_id=data['scan_id'],
            marker_name=data['marker_name'],
            frequency_mhz=data['frequency_mhz'],
            power_dbm=data['power_dbm'],
            marker_type=data.get('marker_type', 'manual'),
            notes=data.get('notes')
        )
        
        db.session.add(marker)
        db.session.commit()
        
        return jsonify(marker.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error adding marker: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add marker'}), 500

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
def delete_marker(marker_id):
    """Delete a marker"""
    try:
        marker = db.session.query(ScanMarker).filter_by(id=marker_id).first()
        if not marker:
            return jsonify({'error': 'Marker not found'}), 404
        
        db.session.delete(marker)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting marker: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete marker'}), 500

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('status', {'msg': 'Connected to RF Spectrum Analyzer'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('keyboard_navigation')
def handle_keyboard_navigation(data):
    """Handle keyboard navigation requests"""
    try:
        current_time = data.get('current_time')
        direction = data.get('direction')
        
        if not current_time or not direction:
            emit('navigation_error', {'msg': 'Missing required parameters'})
            return
        
        # Find next/previous scan
        current_dt = pd.to_datetime(current_time).tz_localize('UTC')
        
        if direction == 'next':
            scan = db.session.query(RFScan).filter(
                RFScan.scan_time > current_dt
            ).order_by(RFScan.scan_time.asc()).first()
        else:
            scan = db.session.query(RFScan).filter(
                RFScan.scan_time < current_dt
            ).order_by(RFScan.scan_time.desc()).first()
        
        if scan:
            emit('navigation_result', {
                'scan_id': str(scan.scan_id),
                'scan_time': scan.scan_time.isoformat()
            })
        else:
            emit('navigation_error', {'msg': f'No more scans in {direction} direction'})
            
    except Exception as e:
        logger.error(f"Navigation error: {e}")
        emit('navigation_error', {'msg': f'Navigation failed: {e}'})

def background_thread():
    """Background thread for periodic updates"""
    while True:
        time.sleep(30)  # Update every 30 seconds
        try:
            with app.app_context():
                # Get latest scan for live updates
                latest_scan = db.session.query(RFScan).order_by(desc(RFScan.scan_time)).first()
                if latest_scan:
                    socketio.emit('latest_scan_update', {
                        'scan_id': str(latest_scan.scan_id),
                        'scan_time': latest_scan.scan_time.isoformat(),
                        'instance_name': latest_scan.instance_name,
                        'config_name': latest_scan.name
                    })
        except Exception as e:
            logger.error(f"Background update error: {e}")

if __name__ == '__main__':
    logger.info("Starting RF Spectrum Analyzer with TimescaleDB...")
    logger.info("=" * 60)
    
    # Initialize database
    init_database()
    
    # Start background thread
    thread = threading.Thread(target=background_thread, daemon=True)
    thread.start()
    
    logger.info("\nStarting Flask-SocketIO server...")
    logger.info("Application available at: http://localhost:5000")
    logger.info("Features:")
    logger.info("  • TimescaleDB time-series storage")
    logger.info("  • Real-time data updates via WebSockets")
    logger.info("  • Advanced filtering by config_info fields")
    logger.info("  • Keyboard navigation between scans")
    logger.info("  • Analysis tools and presets")
    logger.info("  • Marker support for signal analysis")
    
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("\nShutting down RF Spectrum Analyzer...")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        input("Press Enter to exit...")