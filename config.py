import os
from dotenv import load_dotenv
from pydantic import BaseSettings
from typing import Optional

load_dotenv()

class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    # TimescaleDB connection settings
    host: str = os.getenv("TIMESCALE_HOST", "localhost")
    port: int = int(os.getenv("TIMESCALE_PORT", "5432"))
    database: str = os.getenv("TIMESCALE_DB", "spectrum_data")
    username: str = os.getenv("TIMESCALE_USER", "postgres")
    password: str = os.getenv("TIMESCALE_PASSWORD", "")
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global config instance
db_config = DatabaseConfig()