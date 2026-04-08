const fs = require('fs');
const path = require('path');
const { randomUUID } = require('crypto');

function nowIso() {
  return new Date().toISOString();
}

function normalizeRecordId(payload = {}) {
  return payload.id || payload.assessmentId || randomUUID();
}

function normalizePayload(payload = {}, id) {
  return {
    ...payload,
    id,
    createdAt: payload.createdAt || nowIso()
  };
}

async function createPostgresStore({ connectionString, schemaPath } = {}) {
  if (!connectionString) {
    throw new Error('Postgres store requires DATABASE_URL.');
  }

  // Lazy require so memory mode does not depend on pg installation.
  // eslint-disable-next-line global-require
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString
  });

  const effectiveSchemaPath = schemaPath || path.resolve(__dirname, '../bdd/schema.postgres.sql');

  async function initSchema() {
    const sql = fs.readFileSync(effectiveSchemaPath, 'utf8');
    await pool.query(sql);
  }

  async function upsertAssessment(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(
      {
        ...payload,
        assessmentId: payload.assessmentId || id
      },
      id
    );

    const sql = `
      INSERT INTO assessments (
        id,
        assessment_id,
        entity_id,
        created_by_role,
        created_at,
        input_json,
        result_json,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5::timestamptz, $6::jsonb, $7::jsonb, $8::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        assessment_id = EXCLUDED.assessment_id,
        entity_id = EXCLUDED.entity_id,
        created_by_role = EXCLUDED.created_by_role,
        input_json = EXCLUDED.input_json,
        result_json = EXCLUDED.result_json,
        payload_json = EXCLUDED.payload_json,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.assessmentId,
      normalized.entityId ?? null,
      normalized.createdByRole ?? null,
      normalized.createdAt,
      JSON.stringify(normalized.input || {}),
      JSON.stringify(normalized.result || {}),
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function getAssessment(id) {
    const sql = `
      SELECT payload_json
      FROM assessments
      WHERE id = $1
      LIMIT 1
    `;
    const result = await pool.query(sql, [id]);
    return result.rows.length ? result.rows[0].payload_json : null;
  }

  async function listAssessments() {
    const sql = `
      SELECT payload_json
      FROM assessments
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function upsertSeed(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(payload, id);
    const sql = `
      INSERT INTO seeds (
        id,
        name,
        query,
        category,
        status,
        created_by_role,
        approved_by_role,
        created_at,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8::timestamptz, $9::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        query = EXCLUDED.query,
        category = EXCLUDED.category,
        status = EXCLUDED.status,
        created_by_role = EXCLUDED.created_by_role,
        approved_by_role = EXCLUDED.approved_by_role,
        payload_json = EXCLUDED.payload_json,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.name,
      normalized.query,
      normalized.category || 'documentary',
      normalized.status || 'active',
      normalized.createdByRole ?? null,
      normalized.approvedByRole ?? null,
      normalized.createdAt,
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function listSeeds() {
    const sql = `
      SELECT payload_json
      FROM seeds
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function upsertSource(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(payload, id);
    const sql = `
      INSERT INTO sources (
        id,
        name,
        domain,
        source_type,
        policy_status,
        created_by_role,
        approved_by_role,
        created_at,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8::timestamptz, $9::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        domain = EXCLUDED.domain,
        source_type = EXCLUDED.source_type,
        policy_status = EXCLUDED.policy_status,
        created_by_role = EXCLUDED.created_by_role,
        approved_by_role = EXCLUDED.approved_by_role,
        payload_json = EXCLUDED.payload_json,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.name,
      normalized.domain,
      normalized.sourceType || 'public_web',
      normalized.policyStatus || 'allowlisted',
      normalized.createdByRole ?? null,
      normalized.approvedByRole ?? null,
      normalized.createdAt,
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function listSources() {
    const sql = `
      SELECT payload_json
      FROM sources
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function upsertJob(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(payload, id);
    const sql = `
      INSERT INTO discovery_jobs (
        id,
        job_type,
        status,
        retries,
        max_retries,
        timeout_seconds,
        payload_json,
        created_by_role,
        created_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9::timestamptz)
      ON CONFLICT (id) DO UPDATE SET
        job_type = EXCLUDED.job_type,
        status = EXCLUDED.status,
        retries = EXCLUDED.retries,
        max_retries = EXCLUDED.max_retries,
        timeout_seconds = EXCLUDED.timeout_seconds,
        payload_json = EXCLUDED.payload_json,
        created_by_role = EXCLUDED.created_by_role,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.type || normalized.jobType || 'discovery',
      normalized.status || 'queued',
      normalized.retries ?? 0,
      normalized.maxRetries ?? 3,
      normalized.timeoutSeconds ?? 300,
      JSON.stringify(normalized),
      normalized.createdByRole ?? null,
      normalized.createdAt
    ]);
    return result.rows[0].payload_json;
  }

  async function listJobs() {
    const sql = `
      SELECT payload_json
      FROM discovery_jobs
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function upsertDocument(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(payload, id);
    const sql = `
      INSERT INTO documents (
        id,
        source_id,
        discovery_url,
        final_url,
        mime_type,
        size_bytes,
        content_hash,
        redacted_excerpt,
        enrichment_status,
        assessment_json,
        created_by_role,
        created_at,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12::timestamptz, $13::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        source_id = EXCLUDED.source_id,
        discovery_url = EXCLUDED.discovery_url,
        final_url = EXCLUDED.final_url,
        mime_type = EXCLUDED.mime_type,
        size_bytes = EXCLUDED.size_bytes,
        content_hash = EXCLUDED.content_hash,
        redacted_excerpt = EXCLUDED.redacted_excerpt,
        enrichment_status = EXCLUDED.enrichment_status,
        assessment_json = EXCLUDED.assessment_json,
        created_by_role = EXCLUDED.created_by_role,
        payload_json = EXCLUDED.payload_json,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.sourceId ?? null,
      normalized.discoveryUrl ?? null,
      normalized.finalUrl ?? null,
      normalized.mimeType ?? null,
      normalized.sizeBytes ?? null,
      normalized.hash ?? null,
      normalized.redactedExcerpt ?? null,
      normalized.enrichmentStatus ?? 'CONTINUE_LIMITED',
      JSON.stringify(normalized.assessment || {}),
      normalized.createdByRole ?? null,
      normalized.createdAt,
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function listDocuments() {
    const sql = `
      SELECT payload_json
      FROM documents
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function upsertCase(payload) {
    const id = normalizeRecordId(payload);
    const normalized = normalizePayload(payload, id);
    const sql = `
      INSERT INTO defense_cases (
        id,
        status,
        classification,
        document_id,
        exposure_detection_score,
        sensitivity_score,
        decided_at,
        decided_by_role,
        decision_history_json,
        created_by_role,
        created_at,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7::timestamptz, $8, $9::jsonb, $10, $11::timestamptz, $12::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        status = EXCLUDED.status,
        classification = EXCLUDED.classification,
        document_id = EXCLUDED.document_id,
        exposure_detection_score = EXCLUDED.exposure_detection_score,
        sensitivity_score = EXCLUDED.sensitivity_score,
        decided_at = EXCLUDED.decided_at,
        decided_by_role = EXCLUDED.decided_by_role,
        decision_history_json = EXCLUDED.decision_history_json,
        created_by_role = EXCLUDED.created_by_role,
        payload_json = EXCLUDED.payload_json,
        updated_at = NOW()
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.status || 'PENDING_HUMAN_REVIEW',
      normalized.classification || 'UNREVIEWED',
      normalized.documentId ?? null,
      normalized.exposureDetectionScore ?? null,
      normalized.sensitivityScore ?? null,
      normalized.decidedAt || null,
      normalized.decidedByRole ?? null,
      JSON.stringify(normalized.decisionHistory || []),
      normalized.createdByRole ?? null,
      normalized.createdAt,
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function getCase(id) {
    const sql = `
      SELECT payload_json
      FROM defense_cases
      WHERE id = $1
      LIMIT 1
    `;
    const result = await pool.query(sql, [id]);
    return result.rows.length ? result.rows[0].payload_json : null;
  }

  async function listCases() {
    const sql = `
      SELECT payload_json
      FROM defense_cases
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  async function logAudit(event) {
    const id = normalizeRecordId(event);
    const normalized = normalizePayload(event, id);
    const sql = `
      INSERT INTO audit_events (
        id,
        actor_role,
        action,
        resource_type,
        resource_id,
        details_json,
        created_at,
        payload_json
      )
      VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::timestamptz, $8::jsonb)
      ON CONFLICT (id) DO UPDATE SET
        actor_role = EXCLUDED.actor_role,
        action = EXCLUDED.action,
        resource_type = EXCLUDED.resource_type,
        resource_id = EXCLUDED.resource_id,
        details_json = EXCLUDED.details_json,
        payload_json = EXCLUDED.payload_json
      RETURNING payload_json
    `;
    const result = await pool.query(sql, [
      normalized.id,
      normalized.actorRole ?? null,
      normalized.action ?? null,
      normalized.resourceType ?? null,
      normalized.resourceId ?? null,
      JSON.stringify(normalized.details || {}),
      normalized.createdAt,
      JSON.stringify(normalized)
    ]);
    return result.rows[0].payload_json;
  }

  async function listAuditEvents() {
    const sql = `
      SELECT payload_json
      FROM audit_events
      ORDER BY created_at DESC
    `;
    const result = await pool.query(sql);
    return result.rows.map((row) => row.payload_json);
  }

  return {
    async init() {
      await initSchema();
    },
    async close() {
      await pool.end();
    },
    async createAssessment(record) {
      return upsertAssessment(record);
    },
    async getAssessment(id) {
      return getAssessment(id);
    },
    async listAssessments() {
      return listAssessments();
    },
    async createSeed(record) {
      return upsertSeed(record);
    },
    async listSeeds() {
      return listSeeds();
    },
    async createSource(record) {
      return upsertSource(record);
    },
    async listSources() {
      return listSources();
    },
    async createJob(record) {
      return upsertJob(record);
    },
    async listJobs() {
      return listJobs();
    },
    async createDocument(record) {
      return upsertDocument(record);
    },
    async listDocuments() {
      return listDocuments();
    },
    async createCase(record) {
      return upsertCase(record);
    },
    async getCase(id) {
      return getCase(id);
    },
    async updateCase(id, updater) {
      const existing = await getCase(id);
      if (!existing) {
        return null;
      }

      const updated = updater(existing);
      return upsertCase({
        ...updated,
        id
      });
    },
    async listCases() {
      return listCases();
    },
    async logAudit(event) {
      return logAudit(event);
    },
    async listAuditEvents() {
      return listAuditEvents();
    }
  };
}

module.exports = {
  createPostgresStore
};
