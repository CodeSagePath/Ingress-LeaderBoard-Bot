-- Database Initialization Script for Development
-- This script runs automatically when the database container starts
-- It creates necessary extensions and sets up the development database

-- Set database encoding
SET client_encoding = 'UTF8';

-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create development database user (if it doesn't exist)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
      CREATE ROLE app_user WITH LOGIN PASSWORD 'dev_password';
   END IF;
END
$$;

-- Grant necessary permissions
GRANT CREATE ON DATABASE ingress_leaderboard_dev TO app_user;
GRANT CONNECT ON DATABASE ingress_leaderboard_dev TO app_user;

-- Create development schema
CREATE SCHEMA IF NOT EXISTS development;
GRANT ALL ON SCHEMA development TO app_user;

-- Set up logging for development
ALTER DATABASE ingress_leaderboard_dev SET log_statement = 'all';
ALTER DATABASE ingress_leaderboard_dev SET log_min_duration_statement = 0;

-- Create sample data for testing (optional)
-- This will be run by the application during its first startup
-- through Alembic migrations

COMMENT ON DATABASE ingress_leaderboard_dev IS 'Development database for Ingress Leaderboard Bot';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Development database initialized successfully';
    RAISE NOTICE 'Database: ingress_leaderboard_dev';
    RAISE NOTICE 'User: postgres';
    RAISE NOTICE 'Development user created: app_user';
END $$;