-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create example table structure
-- Note: Replace 'scans' with your actual table name
CREATE TABLE IF NOT EXISTS scans (
    scan_time TIMESTAMPTZ NOT NULL,
    scan_id UUID NOT NULL,
    flags TEXT[],
    instance_name TEXT,
    powers TEXT[],
    config_info JSONB,
    PRIMARY KEY (scan_time, scan_id)
);

-- Convert to hypertable for TimescaleDB
SELECT create_hypertable('scans', 'scan_time', if_not_exists => TRUE);

-- Create useful indexes
CREATE INDEX IF NOT EXISTS idx_scan_time ON scans (scan_time DESC);
CREATE INDEX IF NOT EXISTS idx_instance_name ON scans (instance_name);
CREATE INDEX IF NOT EXISTS idx_config_name ON scans ((config_info->>'name'));

-- Insert some sample data (optional)
-- Uncomment the following to add sample data for testing

/*
INSERT INTO scans (scan_time, scan_id, flags, instance_name, powers, config_info) VALUES
    (NOW() - INTERVAL '1 hour', gen_random_uuid(), ARRAY['flag1', 'flag2'], 'radar-01', ARRAY['10', '20', '30'], '{"name": "config1", "cf": 2400.0, "span": 100.0, "sample_amount": 1000, "rbw": 1.0, "vbw": 1.0, "ref_level": -30.0}'),
    (NOW() - INTERVAL '2 hours', gen_random_uuid(), ARRAY['flag3'], 'radar-02', ARRAY['15', '25'], '{"name": "config2", "cf": 5800.0, "span": 200.0, "sample_amount": 2000, "rbw": 2.0, "vbw": 2.0, "ref_level": -25.0}'),
    (NOW() - INTERVAL '3 hours', gen_random_uuid(), ARRAY['flag1', 'flag4'], 'radar-01', ARRAY['5', '12', '18'], '{"name": "config1", "cf": 2400.0, "span": 100.0, "sample_amount": 1000, "rbw": 1.0, "vbw": 1.0, "ref_level": -30.0}')
ON CONFLICT DO NOTHING;
*/