from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
import math
from datetime import datetime

from database import get_db, ScanData
from models import ScanDataResponse, ScanDataFilter, PaginatedResponse

app = FastAPI(title="TimescaleDB Scan Data API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TimescaleDB Scan Data API"}

@app.get("/api/scans", response_model=PaginatedResponse)
async def get_scans(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    instance_name: Optional[str] = Query(None, description="Filter by instance name"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    flags_contains: Optional[str] = Query(None, description="Filter by flags containing text"),
    config_name: Optional[str] = Query(None, description="Filter by config name"),
    sort_by: str = Query("scan_time", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated scan data with optional filtering
    """
    query = db.query(ScanData)
    
    # Apply filters
    filters = []
    
    if instance_name:
        filters.append(ScanData.instance_name.ilike(f"%{instance_name}%"))
    
    if start_time:
        filters.append(ScanData.scan_time >= start_time)
    
    if end_time:
        filters.append(ScanData.scan_time <= end_time)
    
    if flags_contains:
        filters.append(ScanData.flags.op('&&')(f'{{{flags_contains}}}'))
    
    if config_name:
        filters.append(ScanData.config_info['name'].astext.ilike(f"%{config_name}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply sorting
    if hasattr(ScanData, sort_by):
        order_column = getattr(ScanData, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
    else:
        query = query.order_by(desc(ScanData.scan_time))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = math.ceil(total / size)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@app.get("/api/scans/{scan_id}", response_model=ScanDataResponse)
async def get_scan_by_id(
    scan_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific scan by ID
    """
    scan = db.query(ScanData).filter(ScanData.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get basic statistics about the data
    """
    total_scans = db.query(func.count(ScanData.scan_id)).scalar()
    unique_instances = db.query(func.count(func.distinct(ScanData.instance_name))).scalar()
    
    # Get date range
    date_range = db.query(
        func.min(ScanData.scan_time).label('earliest'),
        func.max(ScanData.scan_time).label('latest')
    ).first()
    
    # Get most common instance names
    common_instances = db.query(
        ScanData.instance_name,
        func.count(ScanData.scan_id).label('count')
    ).group_by(ScanData.instance_name).order_by(desc('count')).limit(5).all()
    
    return {
        "total_scans": total_scans,
        "unique_instances": unique_instances,
        "date_range": {
            "earliest": date_range.earliest,
            "latest": date_range.latest
        },
        "common_instances": [{"name": inst.instance_name, "count": inst.count} for inst in common_instances]
    }

@app.get("/api/instance-names")
async def get_instance_names(db: Session = Depends(get_db)):
    """
    Get list of unique instance names for filtering
    """
    instance_names = db.query(ScanData.instance_name).distinct().all()
    return [name[0] for name in instance_names if name[0]]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)