# RF Spectrum Analyzer - Windows Setup Guide

A modern web-based RF spectrum analyzer application built with Flask and TimescaleDB, optimized for Windows development and deployment.

![Windows Compatible](https://img.shields.io/badge/Windows-Compatible-blue)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![TimescaleDB](https://img.shields.io/badge/Database-TimescaleDB-orange)

## 🚀 Quick Start for Windows

### Option 1: One-Click Setup (Recommended)
1. **Install Docker Desktop** from https://docs.docker.com/desktop/install/windows/
2. **Double-click** `setup.bat` - This will automatically:
   - Start TimescaleDB database
   - Build and run the application
   - Open your browser to http://localhost:5000

### Option 2: Development Setup
1. **Double-click** `setup_dev.bat` - This will:
   - Set up Python virtual environment
   - Install all dependencies
   - Configure the database connection
2. **Run** `generate_data.bat` to create sample data
3. **Run** `run_app.bat` to start the application

## 📋 Prerequisites for Windows

### Required Software
- **Windows 10/11** (64-bit recommended)
- **Docker Desktop for Windows** (for containerized deployment)
  - Download: https://docs.docker.com/desktop/install/windows/
  - Enable WSL 2 backend for better performance
- **Python 3.11+** (for local development)
  - Download: https://www.python.org/downloads/windows/
  - ⚠️ **Important**: Check "Add Python to PATH" during installation

### Optional Software
- **Git for Windows** (for cloning the repository)
- **Windows Terminal** (for better command-line experience)
- **Visual Studio Code** (for code editing)

## 🛠️ Installation Methods

### Method 1: Docker Deployment (Easiest)

1. **Download the project** or clone with Git:
   ```bash
   git clone <repository-url>
   cd rf-spectrum-analyzer
   ```

2. **Start Docker Desktop** and wait for it to fully load

3. **Run the setup script**:
   ```batch
   setup.bat
   ```

4. **Wait for completion** - The script will:
   - Download TimescaleDB container
   - Build the application container
   - Start all services
   - Open your browser automatically

5. **Generate sample data** (optional):
   ```batch
   docker exec -it rf-analyzer-app python sample_data_generator.py 200
   ```

### Method 2: Local Development Setup

1. **Install Python 3.11+** with PATH option checked

2. **Run development setup**:
   ```batch
   setup_dev.bat
   ```

3. **Start TimescaleDB** (choose one):
   - **Docker**: The setup script can start it for you
   - **Local PostgreSQL**: Install PostgreSQL + TimescaleDB extension

4. **Generate sample data**:
   ```batch
   generate_data.bat
   ```

5. **Start the application**:
   ```batch
   run_app.bat
   ```

## 🎮 Available Batch Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup.bat` | Complete Docker setup | First time setup, production-like environment |
| `setup_dev.bat` | Development environment | Local development, debugging |
| `run_app.bat` | Start application | After development setup |
| `generate_data.bat` | Create sample data | Testing, demonstration |
| `stop_app.bat` | Stop Docker containers | When done using Docker version |

## 🔧 Configuration for Windows

### Environment Variables
The application automatically sets these for Windows:
- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_ENV`: Development/production mode
- `PYTHONPATH`: Python module path

### File Paths
- **Logs**: `logs/rf_analyzer.log`
- **Database**: Containerized in Docker volumes
- **Config**: `.env` file for development settings

### Windows-Specific Features
- **UTF-8 logging** for proper character encoding
- **Windows path handling** for file operations
- **Batch script automation** for easy operation
- **WSL2 integration** for Docker performance

## 📊 Database Setup

### TimescaleDB with Docker (Recommended)
The application uses TimescaleDB for optimal time-series performance:

```yaml
# Automatically configured in docker-compose.yml
Services:
  - TimescaleDB: Port 5432
  - RF Analyzer: Port 5000
  - Grafana: Port 3000 (optional)
```

### Local PostgreSQL Setup (Advanced)
If you prefer local installation:

1. **Install PostgreSQL 15+** from https://www.postgresql.org/download/windows/
2. **Install TimescaleDB extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ```
3. **Run initialization script**:
   ```batch
   psql -U postgres -d rf_spectrum_db -f init_db.sql
   ```

## 🎯 Using the Application

### Web Interface
- **Main Application**: http://localhost:5000
- **Grafana Dashboard**: http://localhost:3000 (admin/rf-grafana-123)

### Keyboard Shortcuts
- **←/→ Arrow Keys**: Navigate between scans
- **Space**: Play/pause auto-navigation
- **Home/End**: Go to first/last scan
- **Page Up/Down**: Navigate pages
- **M**: Add marker mode
- **R**: Reset zoom

### Features Available
- ✅ **Real-time RF spectrum visualization**
- ✅ **Advanced filtering** (frequency, config, instance, time)
- ✅ **Interactive markers** (click to add)
- ✅ **Analysis tools** (peak detection, signal analysis)
- ✅ **Fast keyboard navigation**
- ✅ **TimescaleDB optimization**

## 🔍 Sample Data

### Generated Data Types
The sample data generator creates realistic RF scenarios:

- **WiFi Surveys**: 2.4 GHz and 5 GHz band analysis
- **Bluetooth Analysis**: Frequency hopping patterns
- **Cellular/LTE**: Various band monitoring
- **FM Radio**: Broadcast band scanning
- **GPS/Amateur**: Specialized frequency monitoring

### Data Volume Options
```batch
generate_data.bat
# Prompts for:
# - 100 scans (quick test) - 30 seconds
# - 500 scans (good dataset) - 2 minutes  
# - 1000 scans (large dataset) - 4 minutes
# - Custom amount
```

## 🚨 Troubleshooting Windows Issues

### Common Problems and Solutions

#### Docker Issues
**Problem**: "Docker command not found"
- **Solution**: Install Docker Desktop and restart Windows
- **Check**: Docker Desktop is running (system tray icon)

**Problem**: "WSL 2 installation is incomplete"
- **Solution**: Enable WSL 2 feature in Windows Features
- **Command**: `wsl --install` in admin PowerShell

#### Python Issues
**Problem**: "Python command not found"
- **Solution**: Reinstall Python with "Add to PATH" checked
- **Alternative**: Use `py` command instead of `python`

**Problem**: "Permission denied" errors
- **Solution**: Run command prompt as Administrator
- **Alternative**: Use PowerShell with execution policy bypass

#### Database Connection Issues
**Problem**: "Cannot connect to database"
- **Solution 1**: Check Docker containers: `docker ps`
- **Solution 2**: Wait longer for database startup
- **Solution 3**: Restart Docker Desktop

#### Port Conflicts
**Problem**: "Port 5000 already in use"
- **Solution**: Kill existing processes or change port in `app.py`
- **Check**: `netstat -ano | findstr :5000`

#### Virtual Environment Issues
**Problem**: Virtual environment activation fails
- **Solution**: Delete `venv` folder and run `setup_dev.bat` again
- **Alternative**: Use `venv\Scripts\activate.bat` manually

### Getting Help
1. **Check logs**: `logs/rf_analyzer.log`
2. **Docker logs**: `docker compose logs -f`
3. **Database status**: `docker exec -it rf-timescaledb pg_isready`
4. **Python environment**: `python --version` and `pip list`

## 🔄 Updates and Maintenance

### Updating the Application
```batch
# Stop current version
stop_app.bat

# Pull latest changes (if using Git)
git pull

# Rebuild and restart
setup.bat
```

### Database Maintenance
```batch
# Backup data
docker exec rf-timescaledb pg_dump -U rf_user rf_spectrum_db > backup.sql

# Clear all data
docker compose down -v
setup.bat
```

### Log Management
- Logs are automatically rotated
- Location: `logs/rf_analyzer.log`
- Clear with: `del logs\*.log`

## 🎓 Development on Windows

### IDE Setup
**Visual Studio Code** (recommended):
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true
}
```

### Debugging
```batch
# Run in debug mode
set FLASK_ENV=development
python app.py
```

### Testing
```batch
# Run with verbose output
python -m pytest -v

# Generate test data
python sample_data_generator.py 50
```

## 🚀 Performance on Windows

### Optimization Tips
1. **Enable WSL 2** for Docker (2x faster)
2. **Use SSD storage** for database performance
3. **Allocate sufficient RAM** to Docker (4GB+)
4. **Disable antivirus scanning** for project folder
5. **Use Windows Terminal** for better command-line performance

### Resource Usage
- **Memory**: ~1GB for full Docker stack
- **Storage**: ~500MB for containers + data
- **CPU**: Minimal when idle, peaks during data generation

## 📈 Monitoring and Logs

### Application Monitoring
- **Main logs**: `logs/rf_analyzer.log`
- **Docker logs**: `docker compose logs`
- **Database logs**: `docker logs rf-timescaledb`

### Performance Monitoring
- **Grafana**: http://localhost:3000
- **Docker stats**: `docker stats`
- **System resources**: Task Manager

---

## 🎉 Ready to Go!

Your RF Spectrum Analyzer is now ready for Windows! 

**Next Steps**:
1. Run `setup.bat` to get started
2. Generate sample data with `generate_data.bat`
3. Open http://localhost:5000 in your browser
4. Explore the RF spectrum data and analysis tools

**Need help?** Check the troubleshooting section above or examine the log files for detailed error information.

---

*Built with ❤️ for Windows RF engineers*