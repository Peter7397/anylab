#!/bin/bash
set -eo pipefail

# Initialize PostgreSQL with vector extension and optimizations
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        -- Create vector extension
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Verify extension was created
        IF NOT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'vector'
        ) THEN
            RAISE EXCEPTION 'Failed to create vector extension';
        END IF;

        -- Optimize for vector operations
        ALTER SYSTEM SET maintenance_work_mem = '1GB';
        ALTER SYSTEM SET max_parallel_workers_per_gather = '4';
        ALTER SYSTEM SET random_page_cost = '1.1';
        ALTER SYSTEM SET effective_cache_size = '4GB';
        ALTER SYSTEM SET work_mem = '64MB';
        
        -- Create indexes if they don't exist
        IF NOT EXISTS (
            SELECT 1 FROM pg_class WHERE relname = 'vector_embeddings_idx'
        ) THEN
            CREATE INDEX vector_embeddings_idx ON documents USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Error during initialization: %', SQLERRM;
            RAISE;
    END;
    \$\$;

    -- Reload configuration
    SELECT pg_reload_conf();
EOSQL 