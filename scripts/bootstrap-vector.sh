#!/bin/sh
set -e
sleep 3
psql "postgresql://postgres:postgres@postgres:5432/rag-mba" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "pgvector extension created successfully."
