-- Database initialization script for European Soccer Analytics
-- This script runs when the PostgreSQL container is first created

-- Create the database if it doesn't exist (though Docker Compose handles this)
-- CREATE DATABASE soccer_analytics;

-- Enable some useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add any initial data or configuration here if needed
-- For now, we'll let the application handle table creation via SQLAlchemy

-- You can add seed data here in the future, such as:
-- INSERT INTO leagues (external_id, name, code, area_name) VALUES
-- (2021, 'Premier League', 'PL', 'England'),
-- (2014, 'Primera División', 'PD', 'Spain');

-- Print a message to confirm the script ran
SELECT 'Database initialization completed' AS status; 