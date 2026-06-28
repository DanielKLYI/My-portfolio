CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS textbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    current_stage TEXT,
    total_chapters INTEGER DEFAULT 0,
    processed_chapters INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS pipeline_stage_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    textbook_id UUID NOT NULL REFERENCES textbooks(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    output JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(textbook_id, stage)
);

CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    textbook_id UUID NOT NULL REFERENCES textbooks(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_markdown TEXT,
    page_start INTEGER,
    page_end INTEGER,
    extracted_json JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    embedding_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(textbook_id, chapter_number)
);

CREATE INDEX IF NOT EXISTS chapters_embedding_idx
    ON chapters USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chapters_textbook_idx ON chapters(textbook_id);
CREATE INDEX IF NOT EXISTS stage_runs_textbook_idx ON pipeline_stage_runs(textbook_id, stage);
