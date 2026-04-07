-- Create the omdr_bci database and role if they don't exist.
-- Run this once as a Postgres superuser before applying 001_base_schema.sql.
--
-- Usage (Windows PowerShell):
--   psql -U postgres -f schemas/000_create_database.sql
-- then:
--   psql -U kai -d omdr_bci -f schemas/001_base_schema.sql
--   psql -U kai -d omdr_bci -f schemas/002_reference_data.sql

-- Create the `kai` role for application-level access to omdr_bci.
-- Uses the same credentials as the consonance memory database for consistency
-- with the existing pg_bridge.py pattern.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kai') THEN
        CREATE ROLE kai WITH LOGIN PASSWORD 'resonance';
    END IF;
END
$$;

-- Create the database if it doesn't exist.
-- CREATE DATABASE cannot run inside a transaction block, so this is a
-- no-op \gexec pattern that checks first.
SELECT 'CREATE DATABASE omdr_bci OWNER kai ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'omdr_bci')\gexec

-- Grant baseline privileges
GRANT ALL PRIVILEGES ON DATABASE omdr_bci TO kai;
