import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  TextField,
  MenuItem,
  Button,
  Chip,
  Typography,
  Grid,
  InputAdornment,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Search,
  Clear,
  FilterList,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const FilterPanel = ({ 
  filters, 
  onFiltersChange, 
  onApplyFilters, 
  onClearFilters,
  instanceNames = [],
  loading = false 
}) => {
  const [expanded, setExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (field, value) => {
    const newFilters = { ...localFilters, [field]: value };
    setLocalFilters(newFilters);
  };

  const handleApply = () => {
    onApplyFilters(localFilters);
  };

  const handleClear = () => {
    const clearedFilters = {
      instance_name: '',
      start_time: null,
      end_time: null,
      flags_contains: '',
      config_name: '',
    };
    setLocalFilters(clearedFilters);
    onClearFilters();
  };

  const hasActiveFilters = Object.values(localFilters).some(value => 
    value !== null && value !== undefined && value !== ''
  );

  const getActiveFilterChips = () => {
    const chips = [];
    
    if (localFilters.instance_name) {
      chips.push(
        <Chip
          key="instance"
          label={`Instance: ${localFilters.instance_name}`}
          onDelete={() => handleFilterChange('instance_name', '')}
          size="small"
        />
      );
    }
    
    if (localFilters.start_time) {
      chips.push(
        <Chip
          key="start_time"
          label={`From: ${new Date(localFilters.start_time).toLocaleDateString()}`}
          onDelete={() => handleFilterChange('start_time', null)}
          size="small"
        />
      );
    }
    
    if (localFilters.end_time) {
      chips.push(
        <Chip
          key="end_time"
          label={`To: ${new Date(localFilters.end_time).toLocaleDateString()}`}
          onDelete={() => handleFilterChange('end_time', null)}
          size="small"
        />
      );
    }
    
    if (localFilters.flags_contains) {
      chips.push(
        <Chip
          key="flags"
          label={`Flags: ${localFilters.flags_contains}`}
          onDelete={() => handleFilterChange('flags_contains', '')}
          size="small"
        />
      );
    }
    
    if (localFilters.config_name) {
      chips.push(
        <Chip
          key="config"
          label={`Config: ${localFilters.config_name}`}
          onDelete={() => handleFilterChange('config_name', '')}
          size="small"
        />
      );
    }
    
    return chips;
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <FilterList />
            <Typography variant="h6">Filters</Typography>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              size="small"
            >
              {expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>
          
          <Box display="flex" gap={1}>
            <Button
              variant="contained"
              onClick={handleApply}
              disabled={loading}
              startIcon={<Search />}
            >
              Apply
            </Button>
            <Button
              variant="outlined"
              onClick={handleClear}
              disabled={loading}
              startIcon={<Clear />}
            >
              Clear
            </Button>
          </Box>
        </Box>

        {/* Active Filters Chips */}
        {hasActiveFilters && (
          <Box display="flex" flexWrap="wrap" gap={0.5} mb={1}>
            {getActiveFilterChips()}
          </Box>
        )}

        <Collapse in={expanded}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                fullWidth
                label="Instance Name"
                value={localFilters.instance_name || ''}
                onChange={(e) => handleFilterChange('instance_name', e.target.value)}
                size="small"
              >
                <MenuItem value="">All Instances</MenuItem>
                {instanceNames.map((name) => (
                  <MenuItem key={name} value={name}>
                    {name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

                         <Grid item xs={12} sm={6} md={3}>
               <DateTimePicker
                 label="Start Time"
                 value={localFilters.start_time}
                 onChange={(newValue) => handleFilterChange('start_time', newValue)}
                 slotProps={{
                   textField: {
                     size: 'small',
                     fullWidth: true
                   }
                 }}
               />
             </Grid>

             <Grid item xs={12} sm={6} md={3}>
               <DateTimePicker
                 label="End Time"
                 value={localFilters.end_time}
                 onChange={(newValue) => handleFilterChange('end_time', newValue)}
                 slotProps={{
                   textField: {
                     size: 'small',
                     fullWidth: true
                   }
                 }}
               />
             </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Flags Contains"
                value={localFilters.flags_contains || ''}
                onChange={(e) => handleFilterChange('flags_contains', e.target.value)}
                size="small"
                placeholder="Search in flags..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Config Name"
                value={localFilters.config_name || ''}
                onChange={(e) => handleFilterChange('config_name', e.target.value)}
                size="small"
                placeholder="Search config name..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>
        </Collapse>
      </Paper>
    </LocalizationProvider>
  );
};

export default FilterPanel;