import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import json

from config import db_config
from models import SpectrumData, ConfigInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimescaleDBManager:
    """TimescaleDB database manager for spectrum data"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection with connection pooling"""
        try:
            self.engine = create_engine(
                db_config.connection_string,
                poolclass=QueuePool,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                pool_pre_ping=True,  # Validate connections before use
                echo=False  # Set to True for SQL debugging
            )
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    def create_tables(self):
        """Create TimescaleDB tables and hypertables"""
        create_table_sql = """
        -- Create the main spectrum_data table
        CREATE TABLE IF NOT EXISTS spectrum_data (
            id VARCHAR(255) NOT NULL,
            scan_time TIMESTAMPTZ NOT NULL,
            instance_name VARCHAR(255) NOT NULL,
            cf DOUBLE PRECISION,
            span DOUBLE PRECISION,
            sample_amount INTEGER,
            rbw DOUBLE PRECISION,
            vbw DOUBLE PRECISION,
            config_extra JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (scan_time, id)
        );
        
        -- Create hypertable for time-series optimization
        SELECT create_hypertable('spectrum_data', 'scan_time', 
                                 if_not_exists => TRUE,
                                 chunk_time_interval => INTERVAL '1 day');
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_spectrum_instance_time 
        ON spectrum_data (instance_name, scan_time DESC);
        
        CREATE INDEX IF NOT EXISTS idx_spectrum_id 
        ON spectrum_data (id);
        
        CREATE INDEX IF NOT EXISTS idx_spectrum_cf 
        ON spectrum_data (cf) WHERE cf IS NOT NULL;
        
        -- Create index on JSONB config field
        CREATE INDEX IF NOT EXISTS idx_spectrum_config_gin 
        ON spectrum_data USING GIN (config_extra);
        """
        
        try:
            with self.engine.connect() as conn:
                # Execute each statement separately for better error handling
                statements = [stmt.strip() for stmt in create_table_sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        conn.execute(text(statement))
                        conn.commit()
            logger.info("Tables and hypertables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a raw psycopg2 connection for bulk operations"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                password=db_config.password
            )
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_spectrum_data(self, data_list: List[SpectrumData]) -> int:
        """Bulk insert spectrum data into TimescaleDB"""
        if not data_list:
            return 0
        
        insert_sql = """
        INSERT INTO spectrum_data 
        (id, scan_time, instance_name, cf, span, sample_amount, rbw, vbw, config_extra)
        VALUES %s
        ON CONFLICT (scan_time, id) DO UPDATE SET
            instance_name = EXCLUDED.instance_name,
            cf = EXCLUDED.cf,
            span = EXCLUDED.span,
            sample_amount = EXCLUDED.sample_amount,
            rbw = EXCLUDED.rbw,
            vbw = EXCLUDED.vbw,
            config_extra = EXCLUDED.config_extra
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Prepare data for insertion
                    values = []
                    for data in data_list:
                        # Extract config info
                        config = data.config_info
                        
                        # Prepare extra config fields (excluding known fields)
                        extra_config = {
                            k: v for k, v in config.dict().items() 
                            if k not in ['cf', 'span', 'sample_amount', 'rbw', 'vbw', 'extra_fields']
                        }
                        if config.extra_fields:
                            extra_config.update(config.extra_fields)
                        
                        values.append((
                            data.id,
                            data.scan_datetime,
                            data.instance_name,
                            config.cf,
                            config.span,
                            config.sample_amount,
                            config.rbw,
                            config.vbw,
                            json.dumps(extra_config) if extra_config else None
                        ))
                    
                    # Bulk insert with conflict resolution
                    execute_values(cursor, insert_sql, values, template=None)
                    conn.commit()
                    
                    inserted_count = len(values)
                    logger.info(f"Successfully inserted {inserted_count} spectrum data records")
                    return inserted_count
                    
        except Exception as e:
            logger.error(f"Failed to insert spectrum data: {e}")
            raise
    
    def query_spectrum_data(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          instance_name: Optional[str] = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """Query spectrum data with optional filters"""
        
        base_query = """
        SELECT id, scan_time, instance_name, cf, span, sample_amount, 
               rbw, vbw, config_extra, created_at
        FROM spectrum_data
        WHERE 1=1
        """
        
        params = {}
        
        if start_time:
            base_query += " AND scan_time >= %(start_time)s"
            params['start_time'] = start_time
            
        if end_time:
            base_query += " AND scan_time <= %(end_time)s"
            params['end_time'] = end_time
            
        if instance_name:
            base_query += " AND instance_name = %(instance_name)s"
            params['instance_name'] = instance_name
        
        base_query += " ORDER BY scan_time DESC LIMIT %(limit)s"
        params['limit'] = limit
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(base_query, params)
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Failed to query spectrum data: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT instance_name) as unique_instances,
            MIN(scan_time) as earliest_scan,
            MAX(scan_time) as latest_scan,
            COUNT(DISTINCT DATE(scan_time)) as unique_days
        FROM spectrum_data
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(stats_query)
                    result = cursor.fetchone()
                    return dict(result) if result else {}
                    
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

# Global database manager instance
db_manager = TimescaleDBManager()