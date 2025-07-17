# TimescaleDB Scan Data Viewer

A modern web application for viewing and analyzing TimescaleDB scan data with pagination, filtering, and real-time statistics.

## Features

- **Responsive Data Table**: View scan data with expandable rows for detailed information
- **Advanced Filtering**: Filter by instance name, date range, flags, and configuration
- **Pagination**: Efficient data loading with customizable page sizes
- **Sorting**: Sort by scan time, instance name, and other fields
- **Statistics Dashboard**: Overview of total scans, instances, and date ranges
- **Real-time Updates**: Refresh data with a single click
- **Modern UI**: Built with Material-UI for a clean, professional interface

## Database Schema

The application expects a TimescaleDB table with the following structure:

```sql
CREATE TABLE your_table_name (
    scan_time TIMESTAMPTZ NOT NULL,
    scan_id UUID NOT NULL,
    flags TEXT[],
    instance_name TEXT,
    powers TEXT[],
    config_info JSONB,
    PRIMARY KEY (scan_time, scan_id)
);
```

The `config_info` JSONB field should contain:
- `name`: Configuration name
- `cf`: Center frequency
- `span`: Frequency span
- `sample_amount`: Number of samples
- `rbw`: Resolution bandwidth
- `vbw`: Video bandwidth
- `ref_level`: Reference level

## Prerequisites

- Python 3.8+
- Node.js 16+
- TimescaleDB (PostgreSQL with TimescaleDB extension)

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd timescale-webapp

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 2. Database Configuration

1. Copy the environment example file:
```bash
cp .env.example .env
```

2. Edit `.env` with your database credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/your_database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=username
DB_PASSWORD=password
TABLE_NAME=your_table_name
```

### 3. Running the Application

#### Start the Backend (FastAPI)

```bash
# Option 1: Using the provided script
python start-backend.py

# Option 2: Direct uvicorn command
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at `http://localhost:8000`

#### Start the Frontend (React)

```bash
# In a new terminal
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Main Endpoints

- `GET /api/scans` - Get paginated scan data with optional filtering
- `GET /api/scans/{scan_id}` - Get specific scan by ID
- `GET /api/stats` - Get database statistics
- `GET /api/instance-names` - Get list of unique instance names

### Query Parameters for `/api/scans`

- `page`: Page number (default: 1)
- `size`: Page size (default: 20, max: 100)
- `instance_name`: Filter by instance name (partial match)
- `start_time`: Filter scans after this time (ISO format)
- `end_time`: Filter scans before this time (ISO format)
- `flags_contains`: Filter by flags containing text
- `config_name`: Filter by configuration name (partial match)
- `sort_by`: Sort field (default: scan_time)
- `sort_order`: Sort order - 'asc' or 'desc' (default: desc)

### Example API Calls

```bash
# Get first 20 scans
curl "http://localhost:8000/api/scans"

# Get scans for specific instance
curl "http://localhost:8000/api/scans?instance_name=radar-01"

# Get scans with date range
curl "http://localhost:8000/api/scans?start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59"

# Get statistics
curl "http://localhost:8000/api/stats"
```

## Usage

### Viewing Data

1. Open the application in your browser (`http://localhost:3000`)
2. View the statistics dashboard at the top
3. Use the data table to browse scan records
4. Click the expand arrow to view detailed information for each scan

### Filtering Data

1. Click the "Filters" panel to expand filter options
2. Set filters for:
   - Instance name (dropdown of available instances)
   - Date range (start and end times)
   - Flags content (text search)
   - Configuration name (text search)
3. Click "Apply" to filter the data
4. Use "Clear" to reset all filters

### Pagination and Sorting

- Use the pagination controls at the bottom of the table
- Change page size from 10 to 100 records per page
- Click column headers to sort by that field
- Toggle between ascending and descending order

## Development

### Backend Development

The FastAPI backend is structured as follows:

- `backend/main.py` - Main FastAPI application and routes
- `backend/database.py` - Database connection and SQLAlchemy models
- `backend/models.py` - Pydantic models for API requests/responses

### Frontend Development

The React frontend uses:

- Material-UI for components and styling
- Axios for API communication
- date-fns for date formatting
- Modern React hooks for state management

Key components:
- `src/App.js` - Main application component
- `src/components/ScanDataTable.js` - Data table with pagination
- `src/components/FilterPanel.js` - Filter controls
- `src/components/StatsPanel.js` - Statistics dashboard
- `src/services/api.js` - API service layer

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify your `.env` file has correct database credentials
   - Ensure TimescaleDB is running and accessible
   - Check that the table name matches your configuration

2. **Frontend Not Loading Data**
   - Ensure the backend is running on port 8000
   - Check browser console for CORS errors
   - Verify API endpoints are accessible

3. **Date Filter Issues**
   - Ensure date formats are in ISO format
   - Check timezone settings in your database

### Performance Tips

- Use appropriate indexes on your TimescaleDB table:
```sql
CREATE INDEX idx_scan_time ON your_table_name (scan_time DESC);
CREATE INDEX idx_instance_name ON your_table_name (instance_name);
CREATE INDEX idx_config_name ON your_table_name ((config_info->>'name'));
```

- Consider time-based partitioning in TimescaleDB for large datasets
- Adjust page sizes based on your data volume and performance requirements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.