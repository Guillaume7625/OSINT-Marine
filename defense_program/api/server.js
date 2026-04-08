const http = require('http');
const { randomUUID } = require('crypto');
const { createPostgresStore } = require('../db/postgres-store');
const {
  computeAssessment,
  normalizeAssessmentInput,
  computeDocumentExposureAssessment,
  maskPersonalData
} = require('../scoring/engine');

const DEFAULT_PORT = Number.parseInt(process.env.PORT || '7070', 10) || 7070;
const DEFAULT_HOST = process.env.HOST || '0.0.0.0';
const DEFAULT_STORE_BACKEND = process.env.STORE_BACKEND || 'memory';

const PERSON_CENTRIC_QUERY_KEYS = [
  'person',
  'personName',
  'person_name',
  'individual',
  'name',
  'email',
  'employee'
];

const GOVERNANCE_ADMIN_ROLE = 'governance_admin';
const REVIEWER_ROLE = 'reviewer';
const EXPORTER_ROLE = 'exporter';

function createDefenseStore() {
  const records = {
    assessments: new Map(),
    seeds: new Map(),
    sources: new Map(),
    jobs: new Map(),
    documents: new Map(),
    cases: new Map(),
    auditEvents: new Map()
  };

  function appendRecord(bucket, record) {
    records[bucket].set(record.id, record);
    return record;
  }

  function listBucket(bucket) {
    return Array.from(records[bucket].values()).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  return {
    createAssessment(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('assessments', payload);
    },
    getAssessment(id) {
      return records.assessments.get(id) || null;
    },
    listAssessments() {
      return listBucket('assessments');
    },
    createSeed(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('seeds', payload);
    },
    listSeeds() {
      return listBucket('seeds');
    },
    createSource(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('sources', payload);
    },
    listSources() {
      return listBucket('sources');
    },
    createJob(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('jobs', payload);
    },
    listJobs() {
      return listBucket('jobs');
    },
    createDocument(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('documents', payload);
    },
    listDocuments() {
      return listBucket('documents');
    },
    createCase(record) {
      const payload = { ...record, id: record.id || randomUUID() };
      return appendRecord('cases', payload);
    },
    getCase(id) {
      return records.cases.get(id) || null;
    },
    updateCase(id, updater) {
      const previous = records.cases.get(id);
      if (!previous) {
        return null;
      }

      const next = updater(previous);
      records.cases.set(id, next);
      return next;
    },
    listCases() {
      return listBucket('cases');
    },
    logAudit(event) {
      const payload = { ...event, id: event.id || randomUUID() };
      return appendRecord('auditEvents', payload);
    },
    listAuditEvents() {
      return listBucket('auditEvents');
    }
  };
}

function createAssessmentStore() {
  const store = createDefenseStore();

  const compatibility = {
    set(record) {
      return store.createAssessment({
        id: record.assessmentId || record.id,
        ...record
      });
    },
    get(id) {
      return store.getAssessment(id);
    },
    list() {
      return store.listAssessments();
    }
  };

  return {
    ...store,
    ...compatibility
  };
}

async function createConfiguredStore(options = {}) {
  const backend = options.backend || process.env.STORE_BACKEND || DEFAULT_STORE_BACKEND;

  if (backend === 'memory') {
    return {
      backend,
      store: createDefenseStore()
    };
  }

  if (backend === 'postgres') {
    const store = await createPostgresStore({
      connectionString: options.connectionString || process.env.DATABASE_URL,
      schemaPath: options.schemaPath
    });
    await store.init();
    return {
      backend,
      store
    };
  }

  throw new Error(`Unsupported STORE_BACKEND: ${backend}`);
}

function sendJson(res, statusCode, payload, extraHeaders = {}) {
  const body = JSON.stringify(payload, null, 2);

  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    ...extraHeaders
  });
  res.end(body);
}

function sendMethodNotAllowed(res, allow) {
  sendJson(
    res,
    405,
    {
      error: 'Method not allowed'
    },
    {
      Allow: allow.join(', ')
    }
  );
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';

    req.on('data', (chunk) => {
      data += chunk;

      if (data.length > 1_000_000) {
        reject(new Error('Request body too large.'));
        req.destroy();
      }
    });

    req.on('end', () => {
      if (!data) {
        resolve({});
        return;
      }

      try {
        resolve(JSON.parse(data));
      } catch (error) {
        reject(new Error('Invalid JSON body.'));
      }
    });

    req.on('error', reject);
  });
}

function getRole(req) {
  const roleHeader = req.headers['x-role'];
  if (typeof roleHeader !== 'string' || !roleHeader.trim()) {
    return 'analyst';
  }

  return roleHeader.trim().toLowerCase();
}

function requireRole(req, expectedRole) {
  return getRole(req) === expectedRole;
}

function assertNoPersonCentricFilters(searchParams) {
  for (const key of PERSON_CENTRIC_QUERY_KEYS) {
    if (searchParams.has(key)) {
      throw new Error(`Person-centric filtering is disabled at MVP level: ${key}`);
    }
  }
}

async function createJob(store, actorRole, type, payload = {}) {
  const now = new Date().toISOString();
  const job = await store.createJob({
    type,
    status: 'queued',
    payload,
    createdByRole: actorRole,
    createdAt: now
  });

  await store.logAudit({
    createdAt: now,
    actorRole,
    action: 'job.created',
    resourceType: 'job',
    resourceId: job.id,
    details: {
      type,
      status: 'queued'
    }
  });

  return job;
}

function createRequestHandler(store = createDefenseStore(), options = {}) {
  const storeBackend = options.storeBackend || 'memory';

  return async function handleDefenseRequest(req, res) {
    const url = new URL(req.url || '/', 'http://localhost');
    const { pathname, searchParams } = url;
    const segments = pathname.split('/').filter(Boolean);
    const role = getRole(req);

    if (req.method === 'GET' && pathname === '/api/v1/health') {
      sendJson(res, 200, {
        status: 'ok',
        service: 'defense-assessment-api',
        store: storeBackend
      });
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/readiness') {
      sendJson(res, 200, {
        status: 'ready',
        checks: [
          { name: 'store', status: 'ok', backend: storeBackend },
          { name: 'guardrails', status: 'ok' }
        ]
      });
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/assessments') {
      sendJson(res, 200, {
        items: await store.listAssessments()
      });
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/assessments') {
      try {
        const body = await readJsonBody(req);
        const normalized = normalizeAssessmentInput(body.exposure, body.capacity, body.profile || {});
        const result = computeAssessment(body.exposure, body.capacity, body.profile || {});
        const now = new Date().toISOString();
        const assessmentId = randomUUID();
        const record = await store.createAssessment({
          id: assessmentId,
          assessmentId,
          entityId: body.entityId ?? null,
          createdAt: now,
          createdByRole: role,
          input: normalized,
          result
        });

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'assessment.created',
          resourceType: 'assessment',
          resourceId: assessmentId,
          details: {
            exposureScore: result.exposureScore,
            capacityScore: result.capacityScore,
            residualRiskScore: result.residualRiskScore
          }
        });

        sendJson(
          res,
          201,
          record,
          {
            Location: `/api/v1/assessments/${assessmentId}`
          }
        );
        return;
      } catch (error) {
        sendJson(res, 400, { error: error.message });
        return;
      }
    }

    if (req.method === 'GET' && segments.length === 4 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'assessments') {
      const assessmentId = segments[3];
      const record = await store.getAssessment(assessmentId);

      if (!record) {
        sendJson(res, 404, { error: 'Assessment not found' });
        return;
      }

      sendJson(res, 200, record);
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/seeds') {
      if (!requireRole(req, GOVERNANCE_ADMIN_ROLE)) {
        sendJson(res, 403, { error: 'Only governance_admin can create seeds.' });
        return;
      }

      try {
        const body = await readJsonBody(req);
        const now = new Date().toISOString();
        const seed = await store.createSeed({
          createdAt: now,
          createdByRole: role,
          name: body.name,
          query: body.query,
          category: body.category || 'documentary',
          status: body.status || 'active'
        });

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'seed.created',
          resourceType: 'seed',
          resourceId: seed.id,
          details: {
            name: seed.name,
            category: seed.category
          }
        });

        sendJson(res, 201, seed, {
          Location: `/api/v1/seeds/${seed.id}`
        });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/seeds') {
      try {
        assertNoPersonCentricFilters(searchParams);
        sendJson(res, 200, { items: await store.listSeeds() });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/sources') {
      if (!requireRole(req, GOVERNANCE_ADMIN_ROLE)) {
        sendJson(res, 403, { error: 'Only governance_admin can create sources.' });
        return;
      }

      try {
        const body = await readJsonBody(req);
        const now = new Date().toISOString();
        const source = await store.createSource({
          createdAt: now,
          createdByRole: role,
          name: body.name,
          domain: body.domain,
          sourceType: body.sourceType || 'public_web',
          policyStatus: body.policyStatus || 'allowlisted'
        });

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'source.created',
          resourceType: 'source',
          resourceId: source.id,
          details: {
            name: source.name,
            policyStatus: source.policyStatus
          }
        });

        sendJson(res, 201, source, {
          Location: `/api/v1/sources/${source.id}`
        });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/sources') {
      try {
        assertNoPersonCentricFilters(searchParams);
        sendJson(res, 200, { items: await store.listSources() });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/jobs/discovery') {
      try {
        const body = await readJsonBody(req);
        const job = await createJob(store, role, 'discovery', {
          seedIds: Array.isArray(body.seedIds) ? body.seedIds : [],
          sourceIds: Array.isArray(body.sourceIds) ? body.sourceIds : []
        });
        sendJson(res, 202, job);
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/jobs') {
      sendJson(res, 200, { items: await store.listJobs() });
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/documents/assess') {
      try {
        const body = await readJsonBody(req);
        const now = new Date().toISOString();
        const result = computeDocumentExposureAssessment(
          {
            signals: body.signals || {},
            extractedText: body.extractedText || ''
          },
          body.documentProfile || {}
        );

        const redactedExcerpt = maskPersonalData(body.excerpt || '');

        const document = await store.createDocument({
          createdAt: now,
          createdByRole: role,
          discoveryUrl: body.discoveryUrl || null,
          finalUrl: body.finalUrl || null,
          sourceId: body.sourceId || null,
          mimeType: body.mimeType || null,
          sizeBytes: body.sizeBytes || null,
          hash: body.hash || null,
          redactedExcerpt,
          enrichmentStatus: result.shouldStopEnrichment ? 'STOPPED_REQUIRES_REVIEW' : 'CONTINUE_LIMITED',
          assessment: result
        });

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'document.assessed',
          resourceType: 'document',
          resourceId: document.id,
          details: {
            enrichmentDecision: result.enrichmentDecision,
            exposureDetectionScore: result.exposureDetectionScore,
            sensitivityScore: result.sensitivityScore
          }
        });

        let generatedCase = null;
        if (result.shouldStopEnrichment) {
          generatedCase = await store.createCase({
            createdAt: now,
            createdByRole: role,
            status: 'PENDING_HUMAN_REVIEW',
            documentId: document.id,
            classification: 'SENSITIVE_EXPOSURE_CANDIDATE',
            exposureDetectionScore: result.exposureDetectionScore,
            sensitivityScore: result.sensitivityScore,
            decisionHistory: []
          });

          await store.logAudit({
            createdAt: now,
            actorRole: role,
            action: 'case.auto_created',
            resourceType: 'case',
            resourceId: generatedCase.id,
            details: {
              documentId: document.id,
              reason: result.stopReason
            }
          });
        }

        sendJson(res, 201, {
          document,
          assessment: result,
          generatedCase
        });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'POST' && pathname === '/api/v1/cases') {
      try {
        const body = await readJsonBody(req);
        const now = new Date().toISOString();
        const created = await store.createCase({
          createdAt: now,
          createdByRole: role,
          status: body.status || 'PENDING_HUMAN_REVIEW',
          documentId: body.documentId || null,
          classification: body.classification || 'UNREVIEWED',
          exposureDetectionScore: body.exposureDetectionScore || null,
          sensitivityScore: body.sensitivityScore || null,
          decisionHistory: []
        });

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'case.created',
          resourceType: 'case',
          resourceId: created.id,
          details: {
            status: created.status
          }
        });

        sendJson(res, 201, created, {
          Location: `/api/v1/cases/${created.id}`
        });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/cases') {
      try {
        assertNoPersonCentricFilters(searchParams);
        sendJson(res, 200, { items: await store.listCases() });
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'GET' && segments.length === 4 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases') {
      const found = await store.getCase(segments[3]);
      if (!found) {
        sendJson(res, 404, { error: 'Case not found' });
        return;
      }

      sendJson(res, 200, found);
      return;
    }

    if (req.method === 'POST' && segments.length === 5 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[4] === 'decisions') {
      if (!requireRole(req, REVIEWER_ROLE)) {
        sendJson(res, 403, { error: 'Only reviewer can submit a decision.' });
        return;
      }

      const caseId = segments[3];
      const found = await store.getCase(caseId);
      if (!found) {
        sendJson(res, 404, { error: 'Case not found' });
        return;
      }

      try {
        const body = await readJsonBody(req);
        const now = new Date().toISOString();
        const decision = {
          at: now,
          byRole: role,
          outcome: body.outcome || 'REQUIRES_FOLLOW_UP',
          reason: body.reason || 'No reason provided.'
        };

        const updated = await store.updateCase(caseId, (previous) => ({
          ...previous,
          status: decision.outcome,
          decidedAt: now,
          decidedByRole: role,
          decisionHistory: [...(previous.decisionHistory || []), decision]
        }));

        await store.logAudit({
          createdAt: now,
          actorRole: role,
          action: 'case.decision',
          resourceType: 'case',
          resourceId: caseId,
          details: decision
        });

        sendJson(res, 200, updated);
      } catch (error) {
        sendJson(res, 400, { error: error.message });
      }
      return;
    }

    if (req.method === 'POST' && segments.length === 5 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[4] === 'export') {
      if (!requireRole(req, EXPORTER_ROLE)) {
        sendJson(res, 403, { error: 'Only exporter can export a case.' });
        return;
      }

      const caseId = segments[3];
      const found = await store.getCase(caseId);
      if (!found) {
        sendJson(res, 404, { error: 'Case not found' });
        return;
      }

      const now = new Date().toISOString();
      const payload = {
        exportId: randomUUID(),
        exportedAt: now,
        exportedByRole: role,
        caseId,
        caseStatus: found.status,
        evidencePolicy: 'minimal_needed_evidence_only',
        package: {
          classification: found.classification,
          exposureDetectionScore: found.exposureDetectionScore,
          sensitivityScore: found.sensitivityScore,
          decisionHistory: found.decisionHistory || []
        }
      };

      await store.logAudit({
        createdAt: now,
        actorRole: role,
        action: 'case.export',
        resourceType: 'case',
        resourceId: caseId,
        details: {
          exportId: payload.exportId
        }
      });

      sendJson(res, 200, payload);
      return;
    }

    if (req.method === 'GET' && pathname === '/api/v1/audit/events') {
      sendJson(res, 200, { items: await store.listAuditEvents() });
      return;
    }

    if (segments.length >= 3 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'assessments') {
      sendMethodNotAllowed(res, ['GET', 'POST']);
      return;
    }

    if (segments.length >= 3 && segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases') {
      sendMethodNotAllowed(res, ['GET', 'POST']);
      return;
    }

    sendJson(res, 404, { error: 'Route not found' });
  };
}

function createDefenseServer({ store = createDefenseStore() } = {}) {
  const storeBackend = store.__backend || 'memory';
  return http.createServer(createRequestHandler(store, { storeBackend }));
}

if (require.main === module) {
  (async () => {
    const configured = await createConfiguredStore();
    const storeWithMeta = {
      ...configured.store,
      __backend: configured.backend
    };
    const server = createDefenseServer({ store: storeWithMeta });

    server.listen(DEFAULT_PORT, DEFAULT_HOST, () => {
      // eslint-disable-next-line no-console
      console.log(`Defense API listening on http://${DEFAULT_HOST}:${DEFAULT_PORT} (store=${configured.backend})`);
    });
  })().catch((error) => {
    // eslint-disable-next-line no-console
    console.error(error);
    process.exitCode = 1;
  });
}

module.exports = {
  PERSON_CENTRIC_QUERY_KEYS,
  createAssessmentStore,
  createDefenseStore,
  createConfiguredStore,
  createRequestHandler,
  createDefenseServer,
  sendJson,
  readJsonBody,
  getRole,
  assertNoPersonCentricFilters
};
