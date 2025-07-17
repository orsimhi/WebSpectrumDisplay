from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

class ConfigInfo(BaseModel):
    name: Optional[str] = None
    cf: Optional[float] = None
    span: Optional[float] = None
    sample_amount: Optional[int] = None
    rbw: Optional[float] = None
    vbw: Optional[float] = None
    ref_level: Optional[float] = None

class ScanDataResponse(BaseModel):
    scan_time: datetime
    scan_id: UUID
    flags: Optional[List[str]] = None
    instance_name: Optional[str] = None
    powers: Optional[List[str]] = None
    config_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ScanDataFilter(BaseModel):
    instance_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    flags_contains: Optional[str] = None
    config_name: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[ScanDataResponse]
    total: int
    page: int
    size: int
    pages: int