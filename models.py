from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import json

class ConfigInfo(BaseModel):
    """Configuration information for spectrum scan"""
    cf: Optional[float] = Field(None, description="Center frequency")
    span: Optional[float] = Field(None, description="Frequency span")
    sample_amount: Optional[int] = Field(None, description="Number of samples")
    rbw: Optional[float] = Field(None, description="Resolution bandwidth")
    vbw: Optional[float] = Field(None, description="Video bandwidth")
    
    # Additional fields for flexibility
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('extra_fields', pre=True)
    def handle_extra_fields(cls, v, values):
        """Handle any additional fields not explicitly defined"""
        if isinstance(v, dict):
            return v
        return {}

class SpectrumData(BaseModel):
    """Main spectrum data model"""
    scan_time: str = Field(..., description="Timestamp of the scan")
    id: str = Field(..., description="Unique identifier for the scan")
    instance_name: str = Field(..., description="Name of the scanner instance")
    config_info: ConfigInfo = Field(..., description="Configuration parameters")
    
    @validator('scan_time')
    def validate_scan_time(cls, v):
        """Ensure scan_time is a valid timestamp string"""
        try:
            # Try to parse as ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            # If that fails, try other common formats
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}")
        return v
    
    @property
    def scan_datetime(self) -> datetime:
        """Convert scan_time string to datetime object"""
        try:
            return datetime.fromisoformat(self.scan_time.replace('Z', '+00:00'))
        except ValueError:
            return datetime.strptime(self.scan_time, '%Y-%m-%d %H:%M:%S')
    
    class Config:
        # Allow extra fields for forward compatibility
        extra = "allow"