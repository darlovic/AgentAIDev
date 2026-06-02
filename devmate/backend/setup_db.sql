-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for storing code chunks with embeddings
CREATE TABLE IF NOT EXISTS code_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768),  -- phi4-mini embedding dimension
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for similarity search
CREATE INDEX ON code_chunks USING ivfflat (embedding vector_cosine_ops);

-- Verify extension is loaded
SELECT * FROM pg_extension WHERE extname = 'vector';
