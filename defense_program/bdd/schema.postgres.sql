-- PostgreSQL relational schema for Defense Program API persistence.
-- Goal: dedicated domain tables instead of a single generic JSON bucket.

CREATE TABLE IF NOT EXISTS assessments (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL UNIQUE,
  entity_id TEXT,
  created_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS seeds (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  query TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'documentary',
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'paused', 'retired')),
  created_by_role TEXT,
  approved_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT,
  source_type TEXT NOT NULL DEFAULT 'public_web',
  policy_status TEXT NOT NULL DEFAULT 'allowlisted'
    CHECK (policy_status IN ('allowlisted', 'watchlisted', 'denylisted')),
  created_by_role TEXT,
  approved_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS discovery_jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL DEFAULT 'discovery'
    CHECK (job_type IN ('discovery', 'fetch_light', 'download_controlled', 'parse', 'extract', 'score', 'reporting', 'cleanup')),
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'dead_letter')),
  retries INTEGER NOT NULL DEFAULT 0,
  max_retries INTEGER NOT NULL DEFAULT 3,
  timeout_seconds INTEGER NOT NULL DEFAULT 300,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  discovery_url TEXT,
  final_url TEXT,
  mime_type TEXT,
  size_bytes BIGINT,
  content_hash TEXT,
  redacted_excerpt TEXT,
  enrichment_status TEXT NOT NULL DEFAULT 'CONTINUE_LIMITED'
    CHECK (enrichment_status IN ('CONTINUE_LIMITED', 'STOPPED_REQUIRES_REVIEW')),
  assessment_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS defense_cases (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'
    CHECK (status IN ('PENDING_HUMAN_REVIEW', 'VALIDATED', 'FALSE_POSITIVE', 'CLOSED', 'REQUIRES_FOLLOW_UP')),
  classification TEXT NOT NULL DEFAULT 'UNREVIEWED',
  document_id TEXT,
  exposure_detection_score NUMERIC(5,2),
  sensitivity_score NUMERIC(5,2),
  decided_at TIMESTAMPTZ,
  decided_by_role TEXT,
  decision_history_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  actor_role TEXT,
  action TEXT,
  resource_type TEXT,
  resource_id TEXT,
  details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_assessments_created_at
  ON assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_entity_id
  ON assessments(entity_id);
CREATE INDEX IF NOT EXISTS idx_seeds_status
  ON seeds(status);
CREATE INDEX IF NOT EXISTS idx_sources_policy_status
  ON sources(policy_status);
CREATE INDEX IF NOT EXISTS idx_jobs_status_type
  ON discovery_jobs(status, job_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at
  ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_enrichment_status
  ON documents(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_cases_status
  ON defense_cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_document_id
  ON defense_cases(document_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
  ON audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource
  ON audit_events(resource_type, resource_id);
