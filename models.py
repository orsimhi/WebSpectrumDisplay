from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import func
from datetime import datetime
import uuid

db = SQLAlchemy()

class RFScan(db.Model):
    __tablename__ = 'rf_scans'
    
    scan_time = db.Column(db.DateTime(timezone=True), primary_key=True, nullable=False)
    scan_id = db.Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    flags = db.Column(ARRAY(db.Text), default=[])
    instance_name = db.Column(db.Text)
    powers = db.Column(ARRAY(db.Float), nullable=False)
    config_info = db.Column(JSONB, nullable=False)
    
    # Relationships
    markers = db.relationship('ScanMarker', backref='scan', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'scan_time': self.scan_time.isoformat(),
            'scan_id': str(self.scan_id),
            'flags': self.flags or [],
            'instance_name': self.instance_name,
            'powers': self.powers,
            'config_info': self.config_info,
            'marker_count': len(self.markers)
        }
    
    @property
    def center_frequency(self):
        """Get center frequency from config_info"""
        return float(self.config_info.get('cf', 0))
    
    @property
    def span(self):
        """Get span from config_info"""
        return float(self.config_info.get('span', 0))
    
    @property
    def name(self):
        """Get name from config_info"""
        return self.config_info.get('name', '')

class AnalysisPreset(db.Model):
    __tablename__ = 'analysis_presets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text)
    preset_config = db.Column(JSONB, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'preset_config': self.preset_config,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ScanMarker(db.Model):
    __tablename__ = 'scan_markers'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_time = db.Column(db.DateTime(timezone=True), nullable=False)
    scan_id = db.Column(UUID(as_uuid=True), nullable=False)
    marker_name = db.Column(db.Text, nullable=False)
    frequency_mhz = db.Column(db.Float, nullable=False)
    power_dbm = db.Column(db.Float, nullable=False)
    marker_type = db.Column(db.Text, default='manual')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Foreign key constraint
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['scan_time', 'scan_id'],
            ['rf_scans.scan_time', 'rf_scans.scan_id'],
            ondelete='CASCADE'
        ),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'scan_time': self.scan_time.isoformat(),
            'scan_id': str(self.scan_id),
            'marker_name': self.marker_name,
            'frequency_mhz': self.frequency_mhz,
            'power_dbm': self.power_dbm,
            'marker_type': self.marker_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }