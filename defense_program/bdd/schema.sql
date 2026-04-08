PRAGMA foreign_keys = ON;

-- V2 reinforced schema:
-- documentary exposure detection and capacity analysis are explicitly separated.

CREATE TABLE IF NOT EXISTS governance_policy_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  version_tag TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('draft', 'active', 'retired')),
  approved_by_role TEXT NOT NULL,
  approved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rule_sets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  policy_version_id INTEGER NOT NULL,
  rule_type TEXT NOT NULL CHECK(rule_type IN ('attribution', 'sensitivity', 'capacity', 'guardrail')),
  version_tag TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_by_role TEXT NOT NULL,
  approved_by_role TEXT,
  approved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(rule_type, version_tag),
  FOREIGN KEY(policy_version_id) REFERENCES governance_policy_versions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS seeds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  query TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'documentary',
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused', 'retired')),
  created_by_role TEXT NOT NULL,
  approved_by_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  domain TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'public_web',
  policy_status TEXT NOT NULL DEFAULT 'allowlisted' CHECK(policy_status IN ('allowlisted', 'watchlisted', 'denylisted')),
  created_by_role TEXT NOT NULL,
  approved_by_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(domain)
);

CREATE TABLE IF NOT EXISTS discovery_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER,
  seed_id INTEGER,
  job_type TEXT NOT NULL CHECK(job_type IN ('discovery', 'fetch_light', 'download_controlled', 'parse', 'extract', 'score', 'reporting', 'cleanup')),
  status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued', 'running', 'succeeded', 'failed', 'dead_letter')),
  retries INTEGER NOT NULL DEFAULT 0,
  max_retries INTEGER NOT NULL DEFAULT 3,
  timeout_seconds INTEGER NOT NULL DEFAULT 300,
  idempotency_key TEXT,
  payload_json TEXT,
  error_message TEXT,
  created_by_role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL,
  FOREIGN KEY(seed_id) REFERENCES seeds(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER,
  discovery_job_id INTEGER,
  discovery_url TEXT NOT NULL,
  final_url TEXT,
  mime_type TEXT,
  size_bytes INTEGER,
  content_hash TEXT,
  captured_at TEXT NOT NULL DEFAULT (datetime('now')),
  quarantine_status TEXT NOT NULL DEFAULT 'pending' CHECK(quarantine_status IN ('pending', 'passed', 'failed')),
  enrichment_status TEXT NOT NULL DEFAULT 'continue_limited' CHECK(enrichment_status IN ('continue_limited', 'stopped_requires_review')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL,
  FOREIGN KEY(discovery_job_id) REFERENCES discovery_jobs(id) ON DELETE SET NULL,
  UNIQUE(content_hash)
);

CREATE TABLE IF NOT EXISTS document_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  evidence_type TEXT NOT NULL CHECK(evidence_type IN ('excerpt', 'metadata', 'header_footer', 'screenshot', 'hash', 'marking')),
  evidence_value TEXT NOT NULL,
  redacted_value TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  institutional_lexicon_score REAL NOT NULL CHECK(institutional_lexicon_score BETWEEN 0 AND 100),
  domain_trust_score REAL NOT NULL CHECK(domain_trust_score BETWEEN 0 AND 100),
  template_signature_score REAL NOT NULL CHECK(template_signature_score BETWEEN 0 AND 100),
  metadata_consistency_score REAL NOT NULL CHECK(metadata_consistency_score BETWEEN 0 AND 100),
  naming_convention_score REAL NOT NULL CHECK(naming_convention_score BETWEEN 0 AND 100),
  corpus_similarity_score REAL NOT NULL CHECK(corpus_similarity_score BETWEEN 0 AND 100),
  diffusion_marking_score REAL NOT NULL CHECK(diffusion_marking_score BETWEEN 0 AND 100),
  operational_detail_score REAL NOT NULL CHECK(operational_detail_score BETWEEN 0 AND 100),
  infrastructure_exposure_score REAL NOT NULL CHECK(infrastructure_exposure_score BETWEEN 0 AND 100),
  personal_data_score REAL NOT NULL CHECK(personal_data_score BETWEEN 0 AND 100),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_assessments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  ruleset_id INTEGER NOT NULL,
  attribution_score REAL NOT NULL CHECK(attribution_score BETWEEN 0 AND 100),
  sensitivity_score REAL NOT NULL CHECK(sensitivity_score BETWEEN 0 AND 100),
  exposure_detection_score REAL NOT NULL CHECK(exposure_detection_score BETWEEN 0 AND 100),
  enrichment_decision TEXT NOT NULL CHECK(enrichment_decision IN ('continue_limited', 'halt_and_escalate')),
  stop_reason_json TEXT NOT NULL,
  matched_markings_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
  FOREIGN KEY(ruleset_id) REFERENCES rule_sets(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS capacity_assessments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope_ref TEXT NOT NULL,
  ruleset_id INTEGER NOT NULL,
  control_coverage_score REAL NOT NULL CHECK(control_coverage_score BETWEEN 0 AND 100),
  detection_readiness_score REAL NOT NULL CHECK(detection_readiness_score BETWEEN 0 AND 100),
  response_readiness_score REAL NOT NULL CHECK(response_readiness_score BETWEEN 0 AND 100),
  continuity_score REAL NOT NULL CHECK(continuity_score BETWEEN 0 AND 100),
  drill_score REAL NOT NULL CHECK(drill_score BETWEEN 0 AND 100),
  capacity_score REAL NOT NULL CHECK(capacity_score BETWEEN 0 AND 100),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(ruleset_id) REFERENCES rule_sets(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS defense_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  document_assessment_id INTEGER NOT NULL,
  capacity_assessment_id INTEGER,
  status TEXT NOT NULL DEFAULT 'pending_human_review'
    CHECK(status IN ('pending_human_review', 'validated', 'false_positive', 'closed')),
  classification TEXT NOT NULL DEFAULT 'sensitive_exposure_candidate',
  created_by_role TEXT NOT NULL,
  assigned_to_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE RESTRICT,
  FOREIGN KEY(document_assessment_id) REFERENCES document_assessments(id) ON DELETE RESTRICT,
  FOREIGN KEY(capacity_assessment_id) REFERENCES capacity_assessments(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS case_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id INTEGER NOT NULL,
  decided_by_role TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK(outcome IN ('validated', 'false_positive', 'needs_follow_up', 'closed')),
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(case_id) REFERENCES defense_cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS case_exports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id INTEGER NOT NULL,
  exported_by_role TEXT NOT NULL,
  package_hash TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(case_id) REFERENCES defense_cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_role TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  details_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS retention_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resource_type TEXT NOT NULL UNIQUE,
  retention_days INTEGER NOT NULL CHECK(retention_days > 0),
  purge_mode TEXT NOT NULL CHECK(purge_mode IN ('soft_delete', 'hard_delete', 'archive')),
  approved_by_role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Runtime persistence for API payloads (memory-compatible shape).
CREATE INDEX IF NOT EXISTS idx_sources_policy_status ON sources(policy_status);
CREATE INDEX IF NOT EXISTS idx_jobs_status_type ON discovery_jobs(status, job_type);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_document_assessments_document ON document_assessments(document_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON defense_cases(status);
CREATE INDEX IF NOT EXISTS idx_case_decisions_case_id ON case_decisions(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id);
