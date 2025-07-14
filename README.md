# WebSpectrumDisplay - TimescaleDB Migration

A Python application for migrating spectrum analyzer data from NDJSON files to TimescaleDB, optimized for time-series analysis and designed to work on Windows OS.

## Features

- ✅ **TimescaleDB Integration**: Optimized time-series database for spectrum data
- ✅ **NDJSON Migration**: Bulk import from existing NDJSON files
- ✅ **Windows Compatible**: Designed and tested for Windows environments
- ✅ **Batch Processing**: Efficient bulk operations with progress tracking
- ✅ **Data Validation**: Pydantic models ensure data integrity
- ✅ **CLI Interface**: Easy-to-use command line tools
- ✅ **Connection Pooling**: Optimized database connections
- ✅ **Conflict Resolution**: Handle duplicate data gracefully

## Data Structure

The system handles spectrum analyzer data with the following structure:

```json
{
  "scan_time": "2024-01-15T10:30:00Z",
  "id": "scan_001",
  "instance_name": "analyzer_01",
  "config_info": {
    "cf": 2400000000.0,
    "span": 100000000.0,
    "sample_amount": 1024,
    "rbw": 100000.0,
    "vbw": 300000.0
  }
}
```

## Prerequisites

### 1. TimescaleDB Installation (Windows)

**Option A: Docker (Recommended)**
```bash
# Install Docker Desktop for Windows
# Then run TimescaleDB container:
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb:latest-pg16
```

**Option B: Native Installation**
1. Download PostgreSQL for Windows from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install TimescaleDB extension from [timescale.com](https://docs.timescale.com/install/latest/self-hosted/installation-windows/)

### 2. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Environment Configuration

Copy the example environment file and configure your database connection:

```bash
copy .env.example .env
```

Edit `.env` file with your TimescaleDB credentials:

```env
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=spectrum_data
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=your_password
```

### 2. Database Setup

Initialize the database tables and hypertables:

```bash
python cli.py setup
```

### 3. Test Connection

Verify your database connection:

```bash
python cli.py test-connection
```

## Usage

### Command Line Interface

The CLI provides several commands for managing your spectrum data:

```bash
# Show all available commands
python cli.py --help

# Setup database (run once)
python cli.py setup

# Check database statistics
python cli.py stats

# Test database connection
python cli.py test-connection
```

### Data Migration

**Migrate a single NDJSON file:**
```bash
python cli.py migrate -i path\to\your\data.ndjson
```

**Migrate all NDJSON files in a directory:**
```bash
python cli.py migrate -i path\to\data\directory
```

**Custom batch size and file pattern:**
```bash
python cli.py migrate -i path\to\data -b 2000 -p "*.json"
```

### Querying Data

**Show recent data (last 7 days):**
```bash
python cli.py recent
```

**Query with filters:**
```bash
# Specific time range
python cli.py query -s "2024-01-01 00:00:00" -e "2024-01-31 23:59:59"

# Filter by instance
python cli.py query --instance "analyzer_01" --limit 20

# Save results to file
python cli.py query --limit 100 -o results.json
```

### Direct Python Usage

```python
from database import db_manager
from ndjson_migrator import NDJSONMigrator
from pathlib import Path

# Setup database
db_manager.create_tables()

# Migrate NDJSON files
migrator = NDJSONMigrator(batch_size=1000)
migrator.migrate_directory(Path("data/"))

# Query data
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(days=1)

results = db_manager.query_spectrum_data(
    start_time=start_time,
    end_time=end_time,
    limit=100
)

print(f"Found {len(results)} records")
```

## Database Schema

The TimescaleDB schema is optimized for time-series queries:

```sql
-- Main hypertable partitioned by scan_time
CREATE TABLE spectrum_data (
    id VARCHAR(255) NOT NULL,
    scan_time TIMESTAMPTZ NOT NULL,
    instance_name VARCHAR(255) NOT NULL,
    cf DOUBLE PRECISION,           -- Center frequency
    span DOUBLE PRECISION,         -- Frequency span
    sample_amount INTEGER,         -- Number of samples
    rbw DOUBLE PRECISION,          -- Resolution bandwidth
    vbw DOUBLE PRECISION,          -- Video bandwidth
    config_extra JSONB,            -- Additional config fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (scan_time, id)
);

-- Optimized indexes for common queries
CREATE INDEX idx_spectrum_instance_time ON spectrum_data (instance_name, scan_time DESC);
CREATE INDEX idx_spectrum_id ON spectrum_data (id);
CREATE INDEX idx_spectrum_cf ON spectrum_data (cf) WHERE cf IS NOT NULL;
CREATE INDEX idx_spectrum_config_gin ON spectrum_data USING GIN (config_extra);
```

## Performance Optimization

### Batch Size Tuning
- **Small files (< 1MB)**: Use batch_size=500
- **Medium files (1-100MB)**: Use batch_size=1000-2000
- **Large files (> 100MB)**: Use batch_size=5000+

### Query Optimization
- Always include time range filters for better performance
- Use instance_name filter when querying specific analyzers
- Leverage JSONB queries for flexible config filtering

### Example Optimized Queries
```python
# Efficient time-range query with instance filter
results = db_manager.query_spectrum_data(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 2),
    instance_name="analyzer_01"
)

# JSONB query for specific config values
with db_manager.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM spectrum_data 
            WHERE scan_time >= %s 
            AND config_extra->>'cf' = %s
        """, (start_time, "2400000000.0"))
```

## Error Handling

The system includes comprehensive error handling:

- **Connection Issues**: Automatic retry with exponential backoff
- **Data Validation**: Invalid records are logged and skipped
- **Conflict Resolution**: Duplicate data is updated automatically
- **Progress Tracking**: Real-time progress bars for large migrations

## Troubleshooting

### Common Issues on Windows

**1. psycopg2 Installation Error:**
```bash
# Use binary package instead
pip uninstall psycopg2
pip install psycopg2-binary
```

**2. TimescaleDB Connection Error:**
```bash
# Check if TimescaleDB is running
docker ps  # If using Docker
# Or check Windows services for PostgreSQL
```

**3. Permission Errors:**
```bash
# Run Command Prompt as Administrator
# Or check file permissions for NDJSON files
```

### Logging

Enable detailed logging by setting log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review TimescaleDB documentation
3. Create an issue in the repository