import React, { useState, useEffect, useCallback } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Typography,
  Box,
  Alert,
  Snackbar,
  AppBar,
  Toolbar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh,
  Timeline,
} from '@mui/icons-material';

import ScanDataTable from './components/ScanDataTable';
import FilterPanel from './components/FilterPanel';
import StatsPanel from './components/StatsPanel';
import { scanDataAPI } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
});

const App = () => {
  // State management
  const [data, setData] = useState([]);
  const [stats, setStats] = useState(null);
  const [instanceNames, setInstanceNames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  
  // Sorting state
  const [sortBy, setSortBy] = useState('scan_time');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Filter state
  const [filters, setFilters] = useState({
    instance_name: '',
    start_time: null,
    end_time: null,
    flags_contains: '',
    config_name: '',
  });

  const [appliedFilters, setAppliedFilters] = useState(filters);

  // Fetch data function
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        page: page + 1, // API uses 1-based pagination
        size: rowsPerPage,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...Object.fromEntries(
          Object.entries(appliedFilters).filter(([_, value]) => 
            value !== null && value !== undefined && value !== ''
          )
        ),
      };

      const result = await scanDataAPI.getScans(params);
      setData(result.items || []);
      setTotalCount(result.total || 0);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch scan data. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, sortBy, sortOrder, appliedFilters]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const statsResult = await scanDataAPI.getStats();
      setStats(statsResult);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  // Fetch instance names
  const fetchInstanceNames = useCallback(async () => {
    try {
      const names = await scanDataAPI.getInstanceNames();
      setInstanceNames(names || []);
    } catch (err) {
      console.error('Error fetching instance names:', err);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Load stats and instance names on mount
  useEffect(() => {
    fetchStats();
    fetchInstanceNames();
  }, [fetchStats, fetchInstanceNames]);

  // Event handlers
  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (newRowsPerPage) => {
    setRowsPerPage(newRowsPerPage);
    setPage(0); // Reset to first page
  };

  const handleSortChange = (field, order) => {
    setSortBy(field);
    setSortOrder(order);
    setPage(0); // Reset to first page
  };

  const handleApplyFilters = (newFilters) => {
    setAppliedFilters(newFilters);
    setPage(0); // Reset to first page
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      instance_name: '',
      start_time: null,
      end_time: null,
      flags_contains: '',
      config_name: '',
    };
    setFilters(clearedFilters);
    setAppliedFilters(clearedFilters);
    setPage(0);
  };

  const handleRowClick = (row) => {
    console.log('Row clicked:', row);
    // You can implement navigation to a detail view here
  };

  const handleRefresh = () => {
    fetchData();
    fetchStats();
    fetchInstanceNames();
  };

  const handleCloseError = () => {
    setError(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Timeline sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            TimescaleDB Scan Data Viewer
          </Typography>
          <Tooltip title="Refresh Data">
            <IconButton color="inherit" onClick={handleRefresh} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth={false} sx={{ mt: 2, mb: 2 }}>
        {/* Statistics Panel */}
        <StatsPanel stats={stats} loading={loading} />
        
        {/* Filter Panel */}
        <FilterPanel
          filters={filters}
          onFiltersChange={setFilters}
          onApplyFilters={handleApplyFilters}
          onClearFilters={handleClearFilters}
          instanceNames={instanceNames}
          loading={loading}
        />
        
        {/* Data Table */}
        <ScanDataTable
          data={data}
          loading={loading}
          page={page}
          rowsPerPage={rowsPerPage}
          totalCount={totalCount}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
          onSortChange={handleSortChange}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onRowClick={handleRowClick}
        />
        
        {/* Results Summary */}
        <Box mt={2}>
          <Typography variant="body2" color="text.secondary" align="center">
            Showing {data.length} of {totalCount} total scans
            {appliedFilters && Object.values(appliedFilters).some(v => v) && ' (filtered)'}
          </Typography>
        </Box>
      </Container>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
};

export default App;