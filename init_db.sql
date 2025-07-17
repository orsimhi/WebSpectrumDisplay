-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the main RF scan data table
CREATE TABLE rf_scans (
    scan_time TIMESTAMPTZ NOT NULL,
    scan_id UUID NOT NULL,
    flags TEXT[] DEFAULT '{}',
    instance_name TEXT,
    powers FLOAT[] NOT NULL,
    config_info JSONB NOT NULL,
    PRIMARY KEY (scan_time, scan_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('rf_scans', 'scan_time');

-- Create indexes for efficient querying
CREATE INDEX idx_rf_scans_scan_time ON rf_scans (scan_time DESC);
CREATE INDEX idx_rf_scans_scan_id ON rf_scans (scan_id);
CREATE INDEX idx_rf_scans_instance_name ON rf_scans (instance_name);

-- Create GIN index for JSONB config_info for efficient JSON queries
CREATE INDEX idx_rf_scans_config_info ON rf_scans USING GIN (config_info);

-- Create specific indexes for common config_info queries
CREATE INDEX idx_rf_scans_config_cf ON rf_scans ((config_info->>'cf'));
CREATE INDEX idx_rf_scans_config_name ON rf_scans ((config_info->>'name'));

-- Create analysis presets table for markers and analysis tools
CREATE TABLE analysis_presets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    preset_config JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create markers table for scan analysis
CREATE TABLE scan_markers (
    id SERIAL PRIMARY KEY,
    scan_time TIMESTAMPTZ NOT NULL,
    scan_id UUID NOT NULL,
    marker_name TEXT NOT NULL,
    frequency_mhz FLOAT NOT NULL,
    power_dbm FLOAT NOT NULL,
    marker_type TEXT DEFAULT 'manual', -- manual, peak, valley, etc.
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (scan_time, scan_id) REFERENCES rf_scans(scan_time, scan_id) ON DELETE CASCADE
);

CREATE INDEX idx_scan_markers_scan ON scan_markers (scan_time, scan_id);
CREATE INDEX idx_scan_markers_frequency ON scan_markers (frequency_mhz);

-- Insert some default analysis presets
INSERT INTO analysis_presets (name, description, preset_config) VALUES
('Peak Detection', 'Automatic peak detection with configurable threshold', 
 '{"type": "peak_detection", "threshold_dbm": -60, "min_distance_mhz": 1.0, "prominence": 10}'),
('Signal Analysis', 'Basic signal analysis with power statistics',
 '{"type": "signal_analysis", "frequency_bands": [{"start": 2400, "end": 2500, "name": "ISM_2.4G"}]}'),
('Interference Detection', 'Detect potential interference sources',
 '{"type": "interference", "baseline_window": 100, "threshold_factor": 3}');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_analysis_presets_updated_at BEFORE UPDATE
    ON analysis_presets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();