import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  Typography,
  Box,
  IconButton,
  Collapse,
  TableSortLabel,
  Tooltip,
} from '@mui/material';
import {
  KeyboardArrowDown,
  KeyboardArrowUp,
  Info,
} from '@mui/icons-material';
import { format } from 'date-fns';

const ScanDataRow = ({ row, onRowClick }) => {
  const [open, setOpen] = useState(false);

  const formatConfigInfo = (config) => {
    if (!config) return 'No config';
    return Object.entries(config)
      .filter(([_, value]) => value !== null && value !== undefined)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');
  };

  return (
    <>
      <TableRow hover onClick={() => onRowClick && onRowClick(row)} sx={{ cursor: 'pointer' }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setOpen(!open);
            }}
          >
            {open ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography variant="body2" fontFamily="monospace">
            {format(new Date(row.scan_time), 'yyyy-MM-dd HH:mm:ss')}
          </Typography>
        </TableCell>
        <TableCell>
          <Tooltip title={row.scan_id}>
            <Typography variant="body2" fontFamily="monospace">
              {row.scan_id.substring(0, 8)}...
            </Typography>
          </Tooltip>
        </TableCell>
        <TableCell>{row.instance_name || 'N/A'}</TableCell>
        <TableCell>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {row.flags && row.flags.length > 0 ? (
              row.flags.slice(0, 3).map((flag, index) => (
                <Chip key={index} label={flag} size="small" variant="outlined" />
              ))
            ) : (
              <Typography variant="caption" color="text.secondary">No flags</Typography>
            )}
            {row.flags && row.flags.length > 3 && (
              <Chip label={`+${row.flags.length - 3} more`} size="small" />
            )}
          </Box>
        </TableCell>
        <TableCell>
          {row.config_info?.name || 'N/A'}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                Detailed Information
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  All Flags:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {row.flags && row.flags.length > 0 ? (
                    row.flags.map((flag, index) => (
                      <Chip key={index} label={flag} size="small" />
                    ))
                  ) : (
                    <Typography variant="caption" color="text.secondary">No flags</Typography>
                  )}
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Powers:
                </Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {row.powers && row.powers.length > 0 ? row.powers.join(', ') : 'No power data'}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Configuration:
                </Typography>
                {row.config_info ? (
                  <Box component="pre" sx={{ fontSize: '0.875rem', fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
                    {JSON.stringify(row.config_info, null, 2)}
                  </Box>
                ) : (
                  <Typography variant="caption" color="text.secondary">No configuration data</Typography>
                )}
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

const ScanDataTable = ({ 
  data, 
  loading, 
  page, 
  rowsPerPage, 
  totalCount, 
  onPageChange, 
  onRowsPerPageChange,
  onSortChange,
  sortBy,
  sortOrder,
  onRowClick 
}) => {
  const handleSortRequest = (property) => {
    const isAsc = sortBy === property && sortOrder === 'asc';
    onSortChange(property, isAsc ? 'desc' : 'asc');
  };

  const createSortHandler = (property) => (event) => {
    handleSortRequest(property);
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 'calc(100vh - 300px)' }}>
        <Table stickyHeader aria-label="scan data table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>
                <TableSortLabel
                  active={sortBy === 'scan_time'}
                  direction={sortBy === 'scan_time' ? sortOrder : 'asc'}
                  onClick={createSortHandler('scan_time')}
                >
                  Scan Time
                </TableSortLabel>
              </TableCell>
              <TableCell>Scan ID</TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortBy === 'instance_name'}
                  direction={sortBy === 'instance_name' ? sortOrder : 'asc'}
                  onClick={createSortHandler('instance_name')}
                >
                  Instance Name
                </TableSortLabel>
              </TableCell>
              <TableCell>Flags</TableCell>
              <TableCell>Config Name</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography>Loading...</Typography>
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography>No data found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, index) => (
                <ScanDataRow key={`${row.scan_id}-${index}`} row={row} onRowClick={onRowClick} />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[10, 20, 50, 100]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => onPageChange(newPage)}
        onRowsPerPageChange={(event) => onRowsPerPageChange(parseInt(event.target.value, 10))}
      />
    </Paper>
  );
};

export default ScanDataTable;