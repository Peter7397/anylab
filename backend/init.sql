-- Initialize OneLab Database
-- This script runs when the PostgreSQL container starts for the first time

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a test table to verify pgvector is working
CREATE TABLE IF NOT EXISTS test_vectors (
    id SERIAL PRIMARY KEY,
    embedding vector(384)
);

-- Skip test vector insertion - will be done via Django migrations

-- Clean up test table
DROP TABLE test_vectors;

-- Create extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
-- SET timezone = 'UTC';

-- Create additional databases if needed
-- CREATE DATABASE onelab_test;

-- Grant permissions
-- GRANT ALL PRIVILEGES ON DATABASE onelab_db TO postgres;
-- GRANT ALL PRIVILEGES ON DATABASE onelab_test TO postgres; 