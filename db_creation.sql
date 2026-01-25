CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS soles;

CREATE TABLE soles.papers (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
title text NOT NULL,
authors text[] DEFAULT '{}'::text[] NOT NULL,
journal text,
year integer,
abstract text,
pdf_url text,
ingestion_source text,
ingestion_timestamp timestamptz NOT NULL DEFAULT now(),
embedding vector(1024)
);

-- Ensure schema exists
CREATE SCHEMA IF NOT EXISTS soles;

-- Create extractions table
CREATE TABLE soles.extractions (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

paper_id uuid NOT NULL
REFERENCES soles.papers(id)
ON DELETE CASCADE,

extraction_version text NOT NULL,

metadata_jsonb jsonb,
study_design_jsonb jsonb,
sample_jsonb jsonb,
outcomes_jsonb jsonb,
risk_of_bias_jsonb jsonb,

extraction_timestamp timestamptz NOT NULL DEFAULT now(),

status text NOT NULL
CHECK (status IN ('success', 'partial', 'failed'))
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_extractions_paper_id
ON soles.extractions (paper_id);

CREATE INDEX IF NOT EXISTS idx_extractions_paper_time
ON soles.extractions (paper_id, extraction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_extractions_status
ON soles.extractions (status);

-- Optional: prevent duplicate versions per paper
-- CREATE UNIQUE INDEX IF NOT EXISTS uq_extractions_version_per_paper
-- ON soles.extractions (paper_id, extraction_version);

-- Create evaluations table
CREATE TABLE soles.evaluations (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

extraction_id uuid NOT NULL
REFERENCES soles.extractions(id)
ON DELETE CASCADE,

evaluator_id text NOT NULL,
-- 예: SME_01, clinician, annotator_role_A, model_eval_v1 등

agreement_scores jsonb,
-- 예: field-level accuracy, Cohen's kappa, per-domain agreement

notes text,

evaluation_timestamp timestamptz NOT NULL DEFAULT now()
);

-- extraction 기준 조회
CREATE INDEX IF NOT EXISTS idx_evaluations_extraction_id
ON soles.evaluations (extraction_id);

-- evaluator 기준 분석
CREATE INDEX IF NOT EXISTS idx_evaluations_evaluator_id
ON soles.evaluations (evaluator_id);

-- 시간 순 평가 추적
CREATE INDEX IF NOT EXISTS idx_evaluations_time
ON soles.evaluations (evaluation_timestamp DESC);

CREATE TABLE soles.agents_logs (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

paper_id uuid
REFERENCES soles.papers(id)
ON DELETE SET NULL,

extraction_id uuid
REFERENCES soles.extractions(id)
ON DELETE SET NULL,

agent_name text NOT NULL,

raw_output text,

cleaned_output jsonb,

input text,

node_name text,

prompt_hash text,

model_name text,

timestamp timestamptz NOT NULL DEFAULT now()
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_agents_logs_paper_id
ON soles.agents_logs (paper_id);

CREATE INDEX IF NOT EXISTS idx_agents_logs_extraction_id
ON soles.agents_logs (extraction_id);

CREATE INDEX IF NOT EXISTS idx_agents_logs_agent_name
ON soles.agents_logs (agent_name);

CREATE INDEX IF NOT EXISTS idx_agents_logs_node_name
ON soles.agents_logs (node_name);

CREATE INDEX IF NOT EXISTS idx_agents_logs_time
ON soles.agents_logs (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_agents_logs_prompt_hash
ON soles.agents_logs (prompt_hash);
