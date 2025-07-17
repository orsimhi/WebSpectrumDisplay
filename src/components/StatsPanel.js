import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Assessment,
  Schedule,
  Storage,
  Computer,
} from '@mui/icons-material';
import { format } from 'date-fns';

const StatCard = ({ title, value, icon, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" gap={1} mb={1}>
        {icon}
        <Typography variant="h6" component="div">
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="div" color="primary">
        {value}
      </Typography>
      {subtitle && (
        <Typography variant="body2" color="text.secondary">
          {subtitle}
        </Typography>
      )}
    </CardContent>
  </Card>
);

const StatsPanel = ({ stats, loading = false }) => {
  if (loading) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography>Loading statistics...</Typography>
      </Paper>
    );
  }

  if (!stats) {
    return null;
  }

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const formatDateRange = () => {
    if (!stats.date_range?.earliest || !stats.date_range?.latest) {
      return 'No date range available';
    }
    
    const start = format(new Date(stats.date_range.earliest), 'MMM dd, yyyy');
    const end = format(new Date(stats.date_range.latest), 'MMM dd, yyyy');
    
    return `${start} - ${end}`;
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        <Assessment />
        <Typography variant="h6">Data Overview</Typography>
      </Box>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Scans"
            value={formatNumber(stats.total_scans || 0)}
            icon={<Storage color="primary" />}
            subtitle="Total scan records"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Instances"
            value={stats.unique_instances || 0}
            icon={<Computer color="primary" />}
            subtitle="Unique instance names"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Date Range"
            value={formatDateRange()}
            icon={<Schedule color="primary" />}
            subtitle="Data collection period"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                Top Instances
              </Typography>
              <List dense>
                {stats.common_instances?.slice(0, 3).map((instance, index) => (
                  <React.Fragment key={instance.name}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary={instance.name || 'Unknown'}
                        secondary={`${formatNumber(instance.count)} scans`}
                      />
                    </ListItem>
                    {index < 2 && <Divider />}
                  </React.Fragment>
                )) || (
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText primary="No data available" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default StatsPanel;