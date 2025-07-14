# Windows Setup Guide for TimescaleDB Migration

This guide provides Windows-specific instructions for setting up and running the TimescaleDB spectrum data migration system.

## Quick Setup (Recommended)

### Option 1: Automated Setup

1. **Download and extract** the project files to a folder (e.g., `C:\spectrum-migration\`)

2. **Run the automated setup**:
   ```cmd
   cd C:\spectrum-migration
   setup_windows.bat
   ```

3. **Edit the environment file**:
   - Open `.env` file in Notepad or VS Code
   - Update the database credentials

4. **Start TimescaleDB** (see options below)

5. **Test the setup**:
   ```cmd
   venv\Scripts\activate
   python quick_start.py
   ```

### Option 2: Docker Setup (Easiest)

1. **Install Docker Desktop for Windows**:
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and restart your computer
   - Start Docker Desktop

2. **Start TimescaleDB**:
   ```cmd
   cd C:\spectrum-migration
   docker-compose up -d
   ```

3. **Verify database is running**:
   ```cmd
   docker ps
   ```
   You should see `spectrum_timescaledb` container running

4. **Optional: Start pgAdmin** (web-based database management):
   ```cmd
   docker-compose --profile admin up -d
   ```
   Access at: http://localhost:8080 (admin@spectrum.local / admin)

## Manual Setup

### 1. Python Environment

```cmd
# Check Python version (requires 3.8+)
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. TimescaleDB Installation Options

#### Option A: Docker (Recommended)
```cmd
# Start TimescaleDB container
docker run -d --name timescaledb ^
  -p 5432:5432 ^
  -e POSTGRES_DB=spectrum_data ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=password ^
  timescale/timescaledb:latest-pg16
```

#### Option B: Native Windows Installation
1. Install PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install TimescaleDB extension: https://docs.timescale.com/install/latest/self-hosted/installation-windows/
3. Create database:
   ```sql
   CREATE DATABASE spectrum_data;
   \c spectrum_data;
   CREATE EXTENSION timescaledb;
   ```

### 3. Configuration

Create `.env` file:
```env
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=spectrum_data
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=password
```

## Usage Examples

### Command Line Usage

```cmd
# Activate environment (run this each time you open new Command Prompt)
venv\Scripts\activate

# Test connection
python cli.py test-connection

# Setup database
python cli.py setup

# Check statistics
python cli.py stats

# Migrate single file
python cli.py migrate -i "C:\path\to\your\data.ndjson"

# Migrate directory
python cli.py migrate -i "C:\data\spectrum_files"

# Query recent data
python cli.py recent -d 7

# Query with filters
python cli.py query -s "2024-01-01 00:00:00" -e "2024-01-31 23:59:59" --instance "analyzer_01"
```

### Python Script Usage

```python
# test_migration.py
import sys
sys.path.append('.')

from database import db_manager
from ndjson_migrator import NDJSONMigrator
from pathlib import Path

# Setup
db_manager.create_tables()

# Migrate
migrator = NDJSONMigrator()
migrator.migrate_directory(Path(r"C:\your\data\directory"))

# Query
results = db_manager.query_spectrum_data(limit=5)
print(f"Found {len(results)} records")
```

## Troubleshooting

### Common Issues

#### 1. Python Not Found
**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
- Install Python from https://python.org
- During installation, check "Add Python to PATH"
- Or manually add Python to PATH:
  - Windows Key + R → `sysdm.cpl` → Advanced → Environment Variables
  - Add Python installation path to PATH

#### 2. psycopg2 Installation Error
**Error**: `Microsoft Visual C++ 14.0 is required`

**Solution**:
```cmd
pip uninstall psycopg2
pip install psycopg2-binary
```

#### 3. TimescaleDB Connection Error
**Error**: `could not connect to server: Connection refused`

**Solutions**:
- **Docker**: Check if container is running:
  ```cmd
  docker ps
  docker logs spectrum_timescaledb
  ```
- **Native**: Check if PostgreSQL service is running:
  - Windows Key + R → `services.msc`
  - Look for "postgresql" service
- **Firewall**: Ensure port 5432 is not blocked
- **Credentials**: Verify `.env` file settings

#### 4. Permission Errors
**Error**: `Access is denied` or `Permission denied`

**Solutions**:
- Run Command Prompt as Administrator
- Check file permissions on NDJSON files
- Ensure antivirus isn't blocking Python

#### 5. Import Errors
**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```cmd
# Make sure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Check installation
pip list
```

### Performance Optimization

#### File Path Handling
```python
# Use raw strings for Windows paths
path = r"C:\data\spectrum\files"

# Or use forward slashes (Python handles conversion)
path = "C:/data/spectrum/files"

# Use Path objects for better cross-platform compatibility
from pathlib import Path
path = Path("C:/data/spectrum/files")
```

#### Large File Processing
```cmd
# For large files, increase batch size
python cli.py migrate -i large_file.ndjson -b 5000

# Process multiple files in parallel (use PowerShell)
Get-ChildItem C:\data\*.ndjson | ForEach-Object -Parallel {
    python cli.py migrate -i $_.FullName
} -ThrottleLimit 4
```

### Development Environment

#### VS Code Setup
1. Install VS Code from https://code.visualstudio.com/
2. Install Python extension
3. Open project folder
4. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → choose `venv\Scripts\python.exe`

#### Debugging
```python
# Add this to your scripts for detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
set PYTHONPATH=%cd%
python -m pdb your_script.py
```

## Production Deployment

### Windows Service
For production, consider running as a Windows service:

1. Install `python-windows-service`:
   ```cmd
   pip install pywin32
   ```

2. Create service script using the CLI commands

3. Use Task Scheduler for automated migrations

### Security Considerations
- Use strong passwords for TimescaleDB
- Consider SSL connections for production
- Restrict network access to database port
- Regular backups using `pg_dump`

## Backup and Recovery

### Backup
```cmd
# Docker backup
docker exec spectrum_timescaledb pg_dump -U postgres spectrum_data > backup.sql

# Native backup
pg_dump -h localhost -U postgres -d spectrum_data -f backup.sql
```

### Restore
```cmd
# Docker restore
docker exec -i spectrum_timescaledb psql -U postgres spectrum_data < backup.sql

# Native restore
psql -h localhost -U postgres -d spectrum_data -f backup.sql
```

## Support

### Getting Help
1. Check this troubleshooting guide
2. Review logs in Command Prompt
3. Check Docker logs: `docker logs spectrum_timescaledb`
4. Enable debug logging in Python scripts
5. Test with sample data first

### Useful Commands
```cmd
# Check what's running on port 5432
netstat -an | findstr :5432

# Check Python packages
pip list | findstr psycopg2

# Test TimescaleDB connection directly
psql -h localhost -U postgres -d spectrum_data

# View Docker container logs
docker logs spectrum_timescaledb --tail 50
```

This setup should work reliably on Windows 10/11 with Python 3.8+ and either Docker Desktop or native PostgreSQL installation.