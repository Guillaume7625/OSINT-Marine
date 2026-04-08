const test = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');

const { createDefenseStore, createRequestHandler } = require('../api/server');

function invoke(handler, { method, url, body, headers = {} }) {
  return new Promise((resolve, reject) => {
    const req = new EventEmitter();
    req.method = method;
    req.url = url;
    req.headers = headers;

    let resolved = false;

    const res = {
      statusCode: null,
      headers: {},
      body: '',
      writeHead(statusCode, headers) {
        this.statusCode = statusCode;
        this.headers = headers;
      },
      end(chunk = '') {
        if (resolved) {
          return;
        }

        this.body += chunk;
        resolved = true;
        resolve(this);
      }
    };

    process.nextTick(() => {
      if (body !== undefined) {
        req.emit('data', Buffer.from(body));
      }
      req.emit('end');
    });

    Promise.resolve(handler(req, res)).catch(reject);
  });
}

test('health endpoint responds with ok', async () => {
  const store = createDefenseStore();
  const handler = createRequestHandler(store);
  const response = await invoke(handler, {
    method: 'GET',
    url: '/api/v1/health'
  });

  const body = JSON.parse(response.body);

  assert.equal(response.statusCode, 200);
  assert.equal(body.status, 'ok');
  assert.equal(body.service, 'defense-assessment-api');
});

test('assessment lifecycle works end to end', async () => {
  const store = createDefenseStore();
  const handler = createRequestHandler(store);

  const createResponse = await invoke(handler, {
    method: 'POST',
    url: '/api/v1/assessments',
    body: JSON.stringify({
      entityId: 42,
      exposure: {
        attackSurfaceScore: 76,
        vulnerabilityScore: 82,
        dependencyRiskScore: 65,
        intelThreatScore: 71,
        dataFreshnessHours: 30
      },
      capacity: {
        controlCoverageScore: 62,
        detectionReadinessScore: 70,
        responseReadinessScore: 58,
        continuityScore: 75,
        drillScore: 54,
        dataFreshnessHours: 20
      }
    })
  });

  const created = JSON.parse(createResponse.body);

  assert.equal(createResponse.statusCode, 201);
  assert.ok(created.assessmentId);
  assert.equal(created.entityId, 42);
  assert.equal(created.result.exposureScore, 75);
  assert.equal(created.result.capacityScore, 63.8);
  assert.equal(created.result.residualRiskScore, 61.42);

  const readResponse = await invoke(handler, {
    method: 'GET',
    url: `/api/v1/assessments/${created.assessmentId}`
  });
  const fetched = JSON.parse(readResponse.body);

  assert.equal(readResponse.statusCode, 200);
  assert.equal(fetched.assessmentId, created.assessmentId);
  assert.equal(fetched.result.residualRiskScore, created.result.residualRiskScore);

  const listResponse = await invoke(handler, {
    method: 'GET',
    url: '/api/v1/assessments'
  });
  const listBody = JSON.parse(listResponse.body);

  assert.equal(listResponse.statusCode, 200);
  assert.equal(listBody.items.length, 1);
  assert.equal(listBody.items[0].assessmentId, created.assessmentId);
});

test('halts enrichment and creates a case when sensitivity is high', async () => {
  const store = createDefenseStore();
  const handler = createRequestHandler(store);

  const response = await invoke(handler, {
    method: 'POST',
    url: '/api/v1/documents/assess',
    body: JSON.stringify({
      discoveryUrl: 'https://example.org/doc',
      finalUrl: 'https://example.org/doc-final',
      excerpt: 'Contact: op@example.org',
      extractedText: 'Confidentiel defense - details',
      signals: {
        institutionalLexiconScore: 90,
        domainTrustScore: 85,
        templateSignatureScore: 80,
        metadataConsistencyScore: 75,
        namingConventionScore: 88,
        corpusSimilarityScore: 82,
        diffusionMarkingScore: 95,
        operationalDetailScore: 77,
        infrastructureExposureScore: 72,
        personalDataScore: 35
      }
    })
  });

  const body = JSON.parse(response.body);

  assert.equal(response.statusCode, 201);
  assert.equal(body.assessment.enrichmentDecision, 'halt_and_escalate');
  assert.equal(body.document.enrichmentStatus, 'STOPPED_REQUIRES_REVIEW');
  assert.ok(body.generatedCase);
  assert.equal(body.generatedCase.status, 'PENDING_HUMAN_REVIEW');
  assert.match(body.document.redactedExcerpt, /\*\*\*@example\.org/);
});

test('blocks person-centric filters on cases endpoint', async () => {
  const store = createDefenseStore();
  const handler = createRequestHandler(store);

  const response = await invoke(handler, {
    method: 'GET',
    url: '/api/v1/cases?person=Jean'
  });

  const body = JSON.parse(response.body);

  assert.equal(response.statusCode, 400);
  assert.match(body.error, /Person-centric filtering is disabled/);
});

test('enforces RBAC for governance and review/export actions', async () => {
  const store = createDefenseStore();
  const handler = createRequestHandler(store);

  const deniedSeedCreate = await invoke(handler, {
    method: 'POST',
    url: '/api/v1/seeds',
    body: JSON.stringify({
      name: 'Marine docs',
      query: 'site:defense.gouv.fr marine fichiertype:pdf'
    }),
    headers: {
      'x-role': 'analyst'
    }
  });
  assert.equal(deniedSeedCreate.statusCode, 403);

  const allowedSeedCreate = await invoke(handler, {
    method: 'POST',
    url: '/api/v1/seeds',
    body: JSON.stringify({
      name: 'Marine docs',
      query: 'site:defense.gouv.fr marine fichiertype:pdf'
    }),
    headers: {
      'x-role': 'governance_admin'
    }
  });
  assert.equal(allowedSeedCreate.statusCode, 201);

  const createdCaseResponse = await invoke(handler, {
    method: 'POST',
    url: '/api/v1/cases',
    body: JSON.stringify({
      classification: 'SENSITIVE_EXPOSURE_CANDIDATE'
    })
  });
  const createdCase = JSON.parse(createdCaseResponse.body);
  assert.equal(createdCaseResponse.statusCode, 201);

  const deniedDecision = await invoke(handler, {
    method: 'POST',
    url: `/api/v1/cases/${createdCase.id}/decisions`,
    body: JSON.stringify({
      outcome: 'VALIDATED',
      reason: 'review complete'
    }),
    headers: {
      'x-role': 'analyst'
    }
  });
  assert.equal(deniedDecision.statusCode, 403);

  const allowedDecision = await invoke(handler, {
    method: 'POST',
    url: `/api/v1/cases/${createdCase.id}/decisions`,
    body: JSON.stringify({
      outcome: 'VALIDATED',
      reason: 'review complete'
    }),
    headers: {
      'x-role': 'reviewer'
    }
  });
  assert.equal(allowedDecision.statusCode, 200);

  const deniedExport = await invoke(handler, {
    method: 'POST',
    url: `/api/v1/cases/${createdCase.id}/export`,
    headers: {
      'x-role': 'reviewer'
    }
  });
  assert.equal(deniedExport.statusCode, 403);

  const allowedExport = await invoke(handler, {
    method: 'POST',
    url: `/api/v1/cases/${createdCase.id}/export`,
    headers: {
      'x-role': 'exporter'
    }
  });
  assert.equal(allowedExport.statusCode, 200);
});
