-- Initialize TimescaleDB extension and create initial schema
-- This script runs automatically when the Docker container starts

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Set timezone to UTC for consistency
SET timezone = 'UTC';

-- Create the database user if it doesn't exist
-- (The main user is already created by the container)

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization completed for spectrum_data database';
END $$;