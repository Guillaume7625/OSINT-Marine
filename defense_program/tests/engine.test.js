const test = require('node:test');
const assert = require('node:assert/strict');

const {
  computeAssessment,
  computeExposureScore,
  computeCapacityScore,
  normalizeAssessmentInput,
  computeAttributionScore,
  computeDocumentExposureAssessment,
  computeDefenseAssessment
} = require('../scoring/engine');

test('computes exposure, capacity and residual risk separately', () => {
  const exposure = {
    attackSurfaceScore: 80,
    vulnerabilityScore: 70,
    dependencyRiskScore: 60,
    intelThreatScore: 90,
    dataFreshnessHours: 48
  };
  const capacity = {
    controlCoverageScore: 60,
    detectionReadinessScore: 55,
    responseReadinessScore: 50,
    continuityScore: 70,
    drillScore: 65,
    dataFreshnessHours: 24
  };

  assert.equal(computeExposureScore(exposure), 78);
  assert.equal(computeCapacityScore(capacity), 58.5);

  const assessment = computeAssessment(exposure, capacity);

  assert.equal(assessment.exposureScore, 78);
  assert.equal(assessment.capacityScore, 58.5);
  assert.equal(assessment.residualRiskScore, 65.22);
  assert.equal(assessment.isCritical, false);
  assert.equal(assessment.riskBand, 'moderate');
  assert.equal(assessment.breakdown.exposure.baseScore, 75);
  assert.equal(assessment.breakdown.exposure.freshnessPenalty, 3);
  assert.equal(assessment.breakdown.capacity.baseScore, 60);
  assert.equal(assessment.breakdown.capacity.freshnessPenalty, 1.5);
});

test('normalizes raw assessment payloads', () => {
  const normalized = normalizeAssessmentInput(
    {
      attackSurfaceScore: '80',
      vulnerabilityScore: '70',
      dependencyRiskScore: '60',
      intelThreatScore: '90',
      dataFreshnessHours: '48'
    },
    {
      controlCoverageScore: '60',
      detectionReadinessScore: '55',
      responseReadinessScore: '50',
      continuityScore: '70',
      drillScore: '65',
      dataFreshnessHours: '24'
    },
    {
      exposureWeight: 65,
      capacityWeight: 35,
      stalePenaltyPer24h: '1.5',
      criticalThreshold: '80'
    }
  );

  assert.equal(normalized.exposure.attackSurfaceScore, 80);
  assert.equal(normalized.capacity.responseReadinessScore, 50);
  assert.equal(normalized.profile.exposureWeight, 0.65);
  assert.equal(normalized.profile.capacityWeight, 0.35);
});

test('flags critical risk when the residual score crosses the threshold', () => {
  const assessment = computeAssessment(
    {
      attackSurfaceScore: 92,
      vulnerabilityScore: 96,
      dependencyRiskScore: 88,
      intelThreatScore: 94,
      dataFreshnessHours: 0
    },
    {
      controlCoverageScore: 28,
      detectionReadinessScore: 24,
      responseReadinessScore: 30,
      continuityScore: 26,
      drillScore: 20,
      dataFreshnessHours: 0
    },
    {
      criticalThreshold: 70
    }
  );

  assert.equal(assessment.isCritical, true);
  assert.equal(assessment.riskBand, 'critical');
  assert.ok(assessment.residualRiskScore >= 70);
});

test('applies multisignal cap and stop-enrichment for sensitive documents', () => {
  const onlyOneSignalStrong = computeAttributionScore({
    institutionalLexiconScore: 95,
    domainTrustScore: 10,
    templateSignatureScore: 10,
    metadataConsistencyScore: 10,
    namingConventionScore: 10,
    corpusSimilarityScore: 10,
    diffusionMarkingScore: 0,
    operationalDetailScore: 0,
    infrastructureExposureScore: 0,
    personalDataScore: 0
  });

  assert.equal(onlyOneSignalStrong.multisignalCapApplied, true);
  assert.ok(onlyOneSignalStrong.score <= 49);

  const document = computeDocumentExposureAssessment({
    signals: {
      institutionalLexiconScore: 88,
      domainTrustScore: 92,
      templateSignatureScore: 81,
      metadataConsistencyScore: 86,
      namingConventionScore: 83,
      corpusSimilarityScore: 84,
      diffusionMarkingScore: 95,
      operationalDetailScore: 78,
      infrastructureExposureScore: 72,
      personalDataScore: 30
    },
    extractedText: 'Diffusion restreinte - document de travail'
  });

  assert.equal(document.shouldStopEnrichment, true);
  assert.equal(document.enrichmentDecision, 'halt_and_escalate');
  assert.ok(document.matchedMarkings.length >= 1);
});

test('keeps exposure detection and capacity analysis separate', () => {
  const withoutCapacity = computeDefenseAssessment({
    signals: {
      institutionalLexiconScore: 70,
      domainTrustScore: 70,
      templateSignatureScore: 70,
      metadataConsistencyScore: 70,
      namingConventionScore: 70,
      corpusSimilarityScore: 70,
      diffusionMarkingScore: 20,
      operationalDetailScore: 20,
      infrastructureExposureScore: 20,
      personalDataScore: 20
    }
  });

  assert.equal(withoutCapacity.capacity.status, 'not_provided');
  assert.equal(withoutCapacity.detection.enrichmentDecision, 'continue_limited');

  const withCapacity = computeDefenseAssessment({
    signals: {
      institutionalLexiconScore: 80,
      domainTrustScore: 80,
      templateSignatureScore: 80,
      metadataConsistencyScore: 80,
      namingConventionScore: 80,
      corpusSimilarityScore: 80,
      diffusionMarkingScore: 30,
      operationalDetailScore: 30,
      infrastructureExposureScore: 30,
      personalDataScore: 30
    },
    capacity: {
      controlCoverageScore: 60,
      detectionReadinessScore: 60,
      responseReadinessScore: 60,
      continuityScore: 60,
      drillScore: 60,
      dataFreshnessHours: 0
    }
  });

  assert.equal(withCapacity.capacity.status, 'provided');
  assert.ok(typeof withCapacity.capacity.capacityScore === 'number');
});
