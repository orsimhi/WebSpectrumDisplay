import os
from sqlalchemy import create_engine, Column, DateTime, String, Text, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv
import uuid

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Get table name from environment
TABLE_NAME = os.getenv("TABLE_NAME", "scans")

class ScanData(Base):
    __tablename__ = TABLE_NAME
    
    scan_time = Column(DateTime, primary_key=True)
    scan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flags = Column(ARRAY(Text))
    instance_name = Column(String)
    powers = Column(ARRAY(Text))  # Assuming array of text, adjust as needed
    config_info = Column(JSON)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()