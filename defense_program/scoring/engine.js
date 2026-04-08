const DEFAULT_PROFILE = Object.freeze({
  exposureWeight: 0.65,
  capacityWeight: 0.35,
  stalePenaltyPer24h: 1.5,
  criticalThreshold: 80
});

const DEFAULT_DOCUMENT_PROFILE = Object.freeze({
  attributionWeights: {
    institutionalLexiconScore: 0.2,
    domainTrustScore: 0.2,
    templateSignatureScore: 0.15,
    metadataConsistencyScore: 0.15,
    namingConventionScore: 0.1,
    corpusSimilarityScore: 0.2
  },
  sensitivityWeights: {
    diffusionMarkingScore: 0.35,
    operationalDetailScore: 0.25,
    infrastructureExposureScore: 0.2,
    personalDataScore: 0.2
  },
  exposureDetectionWeights: {
    attributionScore: 0.55,
    sensitivityScore: 0.45
  },
  multisignalStrongThreshold: 60,
  multisignalMinimum: 2,
  singleSignalCap: 49,
  stopSensitivityThreshold: 75
});

const DOCUMENT_ATTRIBUTION_FIELDS = [
  'institutionalLexiconScore',
  'domainTrustScore',
  'templateSignatureScore',
  'metadataConsistencyScore',
  'namingConventionScore',
  'corpusSimilarityScore'
];

const DOCUMENT_SENSITIVITY_FIELDS = [
  'diffusionMarkingScore',
  'operationalDetailScore',
  'infrastructureExposureScore',
  'personalDataScore'
];

const SENSITIVE_MARKING_PATTERNS = [
  /\bconfidentiel defense\b/i,
  /\bsecret defense\b/i,
  /\btres secret defense\b/i,
  /\bdiffusion restreinte\b/i,
  /\brestreint\b/i,
  /\bclassified\b/i,
  /\bfor official use only\b/i,
  /\bsensitive\b/i,
  /\bopsec\b/i
];

const EXPOSURE_FIELDS = [
  'attackSurfaceScore',
  'vulnerabilityScore',
  'dependencyRiskScore',
  'intelThreatScore'
];

const CAPACITY_FIELDS = [
  'controlCoverageScore',
  'detectionReadinessScore',
  'responseReadinessScore',
  'continuityScore',
  'drillScore'
];

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function roundTo(value, decimals = 2) {
  return Number(Number(value).toFixed(decimals));
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function normalizeWeights(weights, label) {
  assertPlainObject(weights, label);

  const entries = Object.entries(weights);
  if (!entries.length) {
    throw new TypeError(`${label} must not be empty.`);
  }

  const normalized = {};
  let total = 0;

  for (const [key, value] of entries) {
    const numeric = toFiniteNumber(value, `${label}.${key}`);
    if (numeric < 0) {
      throw new TypeError(`${label}.${key} must be non-negative.`);
    }

    total += numeric;
    normalized[key] = numeric;
  }

  if (total <= 0) {
    throw new TypeError(`${label} must sum to a positive value.`);
  }

  for (const key of Object.keys(normalized)) {
    normalized[key] = roundTo(normalized[key] / total, 4);
  }

  return normalized;
}

function weightedAverage(valuesByField, weights) {
  let total = 0;

  for (const [field, weight] of Object.entries(weights)) {
    total += (valuesByField[field] ?? 0) * weight;
  }

  return roundTo(total, 2);
}

function assertPlainObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object.`);
  }
}

function toFiniteNumber(value, label) {
  if (value === '' || value === null || value === undefined) {
    throw new TypeError(`${label} must be a finite number.`);
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    throw new TypeError(`${label} must be a finite number.`);
  }

  return numeric;
}

function normalizeScore(value, label) {
  return roundTo(clamp(toFiniteNumber(value, label)), 2);
}

function normalizeFreshnessHours(value, label) {
  return roundTo(Math.max(0, toFiniteNumber(value ?? 0, label)), 2);
}

function normalizeProfile(profile = {}) {
  assertPlainObject(profile, 'profile');

  let exposureWeight = toFiniteNumber(profile.exposureWeight ?? DEFAULT_PROFILE.exposureWeight, 'profile.exposureWeight');
  let capacityWeight = toFiniteNumber(profile.capacityWeight ?? DEFAULT_PROFILE.capacityWeight, 'profile.capacityWeight');
  const stalePenaltyPer24h = Math.max(
    0,
    toFiniteNumber(profile.stalePenaltyPer24h ?? DEFAULT_PROFILE.stalePenaltyPer24h, 'profile.stalePenaltyPer24h')
  );
  const criticalThreshold = clamp(
    toFiniteNumber(profile.criticalThreshold ?? DEFAULT_PROFILE.criticalThreshold, 'profile.criticalThreshold')
  );

  if (exposureWeight < 0 || capacityWeight < 0) {
    throw new TypeError('profile weights must be non-negative.');
  }

  const totalWeight = exposureWeight + capacityWeight;
  if (totalWeight <= 0) {
    throw new TypeError('profile weights must sum to a positive value.');
  }

  exposureWeight = exposureWeight / totalWeight;
  capacityWeight = capacityWeight / totalWeight;

  return {
    exposureWeight: roundTo(exposureWeight, 4),
    capacityWeight: roundTo(capacityWeight, 4),
    stalePenaltyPer24h: roundTo(stalePenaltyPer24h, 2),
    criticalThreshold: roundTo(criticalThreshold, 2)
  };
}

function normalizeExposureInput(exposure) {
  assertPlainObject(exposure, 'exposure');

  return {
    attackSurfaceScore: normalizeScore(exposure.attackSurfaceScore, 'exposure.attackSurfaceScore'),
    vulnerabilityScore: normalizeScore(exposure.vulnerabilityScore, 'exposure.vulnerabilityScore'),
    dependencyRiskScore: normalizeScore(exposure.dependencyRiskScore, 'exposure.dependencyRiskScore'),
    intelThreatScore: normalizeScore(exposure.intelThreatScore, 'exposure.intelThreatScore'),
    dataFreshnessHours: normalizeFreshnessHours(exposure.dataFreshnessHours, 'exposure.dataFreshnessHours')
  };
}

function normalizeCapacityInput(capacity) {
  assertPlainObject(capacity, 'capacity');

  return {
    controlCoverageScore: normalizeScore(capacity.controlCoverageScore, 'capacity.controlCoverageScore'),
    detectionReadinessScore: normalizeScore(capacity.detectionReadinessScore, 'capacity.detectionReadinessScore'),
    responseReadinessScore: normalizeScore(capacity.responseReadinessScore, 'capacity.responseReadinessScore'),
    continuityScore: normalizeScore(capacity.continuityScore, 'capacity.continuityScore'),
    drillScore: normalizeScore(capacity.drillScore, 'capacity.drillScore'),
    dataFreshnessHours: normalizeFreshnessHours(capacity.dataFreshnessHours, 'capacity.dataFreshnessHours')
  };
}

function normalizeAssessmentInput(exposure, capacity, profile = {}) {
  return {
    exposure: normalizeExposureInput(exposure),
    capacity: normalizeCapacityInput(capacity),
    profile: normalizeProfile(profile)
  };
}

function normalizeDocumentSignals(signals) {
  assertPlainObject(signals, 'signals');

  const normalized = {
    sensitiveMarkings: Array.isArray(signals.sensitiveMarkings)
      ? signals.sensitiveMarkings.filter((value) => typeof value === 'string' && value.trim())
      : []
  };

  for (const field of DOCUMENT_ATTRIBUTION_FIELDS) {
    normalized[field] = normalizeScore(signals[field] ?? 0, `signals.${field}`);
  }

  for (const field of DOCUMENT_SENSITIVITY_FIELDS) {
    normalized[field] = normalizeScore(signals[field] ?? 0, `signals.${field}`);
  }

  return normalized;
}

function detectSensitiveMarkings(text = '') {
  if (typeof text !== 'string' || text.length === 0) {
    return [];
  }

  const lowered = text.toLowerCase();
  const matches = [];

  for (const pattern of SENSITIVE_MARKING_PATTERNS) {
    if (pattern.test(lowered)) {
      matches.push(pattern.source.replace(/\\b/g, ''));
    }
  }

  return Array.from(new Set(matches));
}

function maskPersonalData(text = '') {
  if (typeof text !== 'string' || text.length === 0) {
    return '';
  }

  const maskedEmails = text.replace(
    /([A-Z0-9._%+-]{1,2})[A-Z0-9._%+-]*@([A-Z0-9.-]+\.[A-Z]{2,})/gi,
    '$1***@$2'
  );

  return maskedEmails.replace(/\b(Mr|Mrs|Ms|M|Mme)\s+[A-Z][a-zA-Z-]+/g, '$1 [MASKED]');
}

function normalizeDocumentProfile(profile = {}) {
  assertPlainObject(profile, 'documentProfile');

  const attributionWeights = normalizeWeights(
    profile.attributionWeights ?? DEFAULT_DOCUMENT_PROFILE.attributionWeights,
    'documentProfile.attributionWeights'
  );
  const sensitivityWeights = normalizeWeights(
    profile.sensitivityWeights ?? DEFAULT_DOCUMENT_PROFILE.sensitivityWeights,
    'documentProfile.sensitivityWeights'
  );
  const exposureDetectionWeights = normalizeWeights(
    profile.exposureDetectionWeights ?? DEFAULT_DOCUMENT_PROFILE.exposureDetectionWeights,
    'documentProfile.exposureDetectionWeights'
  );

  return {
    attributionWeights,
    sensitivityWeights,
    exposureDetectionWeights,
    multisignalStrongThreshold: normalizeScore(
      profile.multisignalStrongThreshold ?? DEFAULT_DOCUMENT_PROFILE.multisignalStrongThreshold,
      'documentProfile.multisignalStrongThreshold'
    ),
    multisignalMinimum: Math.max(
      1,
      Math.floor(toFiniteNumber(profile.multisignalMinimum ?? DEFAULT_DOCUMENT_PROFILE.multisignalMinimum, 'documentProfile.multisignalMinimum'))
    ),
    singleSignalCap: normalizeScore(profile.singleSignalCap ?? DEFAULT_DOCUMENT_PROFILE.singleSignalCap, 'documentProfile.singleSignalCap'),
    stopSensitivityThreshold: normalizeScore(
      profile.stopSensitivityThreshold ?? DEFAULT_DOCUMENT_PROFILE.stopSensitivityThreshold,
      'documentProfile.stopSensitivityThreshold'
    )
  };
}

function computeAttributionScore(signals, documentProfile = {}) {
  const normalizedSignals = normalizeDocumentSignals(signals);
  const profile = normalizeDocumentProfile(documentProfile);
  const attributionSignals = {};

  for (const field of DOCUMENT_ATTRIBUTION_FIELDS) {
    attributionSignals[field] = normalizedSignals[field];
  }

  const rawScore = weightedAverage(attributionSignals, profile.attributionWeights);
  const strongSignalsCount = DOCUMENT_ATTRIBUTION_FIELDS.filter(
    (field) => attributionSignals[field] >= profile.multisignalStrongThreshold
  ).length;

  const multisignalCapApplied = strongSignalsCount < profile.multisignalMinimum;
  const score = multisignalCapApplied ? Math.min(rawScore, profile.singleSignalCap) : rawScore;

  return {
    score: roundTo(score, 2),
    rawScore,
    strongSignalsCount,
    multisignalCapApplied,
    components: attributionSignals
  };
}

function computeSensitivityScore(signals, documentProfile = {}) {
  const normalizedSignals = normalizeDocumentSignals(signals);
  const profile = normalizeDocumentProfile(documentProfile);
  const sensitivitySignals = {};

  for (const field of DOCUMENT_SENSITIVITY_FIELDS) {
    sensitivitySignals[field] = normalizedSignals[field];
  }

  return {
    score: weightedAverage(sensitivitySignals, profile.sensitivityWeights),
    components: sensitivitySignals
  };
}

function computeDocumentExposureAssessment(documentInput, documentProfile = {}) {
  assertPlainObject(documentInput, 'documentInput');

  const profile = normalizeDocumentProfile(documentProfile);
  const signals = normalizeDocumentSignals(documentInput.signals ?? documentInput);
  const attribution = computeAttributionScore(signals, profile);
  const sensitivity = computeSensitivityScore(signals, profile);
  const parsedMarkings = detectSensitiveMarkings(documentInput.extractedText ?? '');
  const matchedMarkings = Array.from(new Set([...signals.sensitiveMarkings, ...parsedMarkings]));

  const exposureDetectionScore = roundTo(
    clamp(
      attribution.score * profile.exposureDetectionWeights.attributionScore +
      sensitivity.score * profile.exposureDetectionWeights.sensitivityScore
    ),
    2
  );

  const stopReason = [];
  if (matchedMarkings.length > 0) {
    stopReason.push('sensitive_marking_detected');
  }
  if (sensitivity.score >= profile.stopSensitivityThreshold) {
    stopReason.push('sensitivity_threshold_exceeded');
  }

  const shouldStopEnrichment = stopReason.length > 0;

  return {
    attributionScore: attribution.score,
    sensitivityScore: sensitivity.score,
    exposureDetectionScore,
    shouldStopEnrichment,
    enrichmentDecision: shouldStopEnrichment ? 'halt_and_escalate' : 'continue_limited',
    matchedMarkings,
    breakdown: {
      attribution,
      sensitivity,
      profile
    },
    stopReason
  };
}

function computeFreshnessPenalty(dataFreshnessHours, stalePenaltyPer24h) {
  return roundTo(Math.floor(Math.max(0, dataFreshnessHours) / 24) * stalePenaltyPer24h, 2);
}

function evaluateExposureNormalized(exposure, profile) {
  const components = {
    attackSurfaceScore: exposure.attackSurfaceScore,
    vulnerabilityScore: exposure.vulnerabilityScore,
    dependencyRiskScore: exposure.dependencyRiskScore,
    intelThreatScore: exposure.intelThreatScore
  };

  const baseScore = roundTo(average(EXPOSURE_FIELDS.map((field) => components[field])), 2);
  const freshnessPenalty = computeFreshnessPenalty(exposure.dataFreshnessHours, profile.stalePenaltyPer24h);
  const score = roundTo(clamp(baseScore + freshnessPenalty), 2);

  return {
    components,
    baseScore,
    freshnessPenalty,
    score
  };
}

function evaluateCapacityNormalized(capacity, profile) {
  const components = {
    controlCoverageScore: capacity.controlCoverageScore,
    detectionReadinessScore: capacity.detectionReadinessScore,
    responseReadinessScore: capacity.responseReadinessScore,
    continuityScore: capacity.continuityScore,
    drillScore: capacity.drillScore
  };

  const baseScore = roundTo(average(CAPACITY_FIELDS.map((field) => components[field])), 2);
  const freshnessPenalty = computeFreshnessPenalty(capacity.dataFreshnessHours, profile.stalePenaltyPer24h);
  const score = roundTo(clamp(baseScore - freshnessPenalty), 2);

  return {
    components,
    baseScore,
    freshnessPenalty,
    score
  };
}

function evaluateExposure(exposure, profile = {}) {
  const normalizedExposure = normalizeExposureInput(exposure);
  const resolvedProfile = normalizeProfile(profile);
  return evaluateExposureNormalized(normalizedExposure, resolvedProfile);
}

function evaluateCapacity(capacity, profile = {}) {
  const normalizedCapacity = normalizeCapacityInput(capacity);
  const resolvedProfile = normalizeProfile(profile);
  return evaluateCapacityNormalized(normalizedCapacity, resolvedProfile);
}

function computeExposureScore(exposure, profile = {}) {
  return evaluateExposure(exposure, profile).score;
}

function computeCapacityScore(capacity, profile = {}) {
  return evaluateCapacity(capacity, profile).score;
}

function computeRiskBand(residualRiskScore, criticalThreshold) {
  if (residualRiskScore >= criticalThreshold) {
    return 'critical';
  }

  if (residualRiskScore >= 70) {
    return 'high';
  }

  if (residualRiskScore >= 40) {
    return 'moderate';
  }

  return 'low';
}

function computeAssessment(exposure, capacity, profile = {}) {
  const normalized = normalizeAssessmentInput(exposure, capacity, profile);
  const exposureEvaluation = evaluateExposureNormalized(normalized.exposure, normalized.profile);
  const capacityEvaluation = evaluateCapacityNormalized(normalized.capacity, normalized.profile);
  const exposureTerm = roundTo(normalized.profile.exposureWeight * exposureEvaluation.score, 2);
  const capacityTerm = roundTo(normalized.profile.capacityWeight * (100 - capacityEvaluation.score), 2);

  const residualRiskScore = roundTo(
    clamp(exposureTerm + capacityTerm),
    2
  );

  const riskBand = computeRiskBand(residualRiskScore, normalized.profile.criticalThreshold);

  return {
    exposureScore: exposureEvaluation.score,
    capacityScore: capacityEvaluation.score,
    residualRiskScore,
    riskBand,
    isCritical: residualRiskScore >= normalized.profile.criticalThreshold,
    breakdown: {
      exposure: exposureEvaluation,
      capacity: capacityEvaluation,
      profile: normalized.profile,
      aggregation: {
        exposureTerm,
        capacityTerm,
        formula: 'residual = exposureWeight * exposureScore + capacityWeight * (100 - capacityScore)'
      }
    }
  };
}

function computeDefenseAssessment(input = {}) {
  assertPlainObject(input, 'input');

  const detection = computeDocumentExposureAssessment(
    {
      signals: input.signals ?? input.documentSignals ?? {},
      extractedText: input.extractedText ?? ''
    },
    input.documentProfile ?? {}
  );

  if (!input.capacity) {
    return {
      detection,
      capacity: {
        status: 'not_provided',
        message: 'Capacity analysis is intentionally separate and requires explicit inputs.'
      }
    };
  }

  const capacityAssessment = computeAssessment(
    input.exposure ?? {
      attackSurfaceScore: detection.exposureDetectionScore,
      vulnerabilityScore: detection.exposureDetectionScore,
      dependencyRiskScore: detection.exposureDetectionScore,
      intelThreatScore: detection.exposureDetectionScore,
      dataFreshnessHours: 0
    },
    input.capacity,
    input.capacityProfile ?? {}
  );

  return {
    detection,
    capacity: {
      status: 'provided',
      ...capacityAssessment
    }
  };
}

module.exports = {
  DEFAULT_PROFILE,
  DEFAULT_DOCUMENT_PROFILE,
  clamp,
  roundTo,
  average,
  normalizeWeights,
  weightedAverage,
  normalizeProfile,
  normalizeDocumentProfile,
  normalizeExposureInput,
  normalizeCapacityInput,
  normalizeAssessmentInput,
  normalizeDocumentSignals,
  detectSensitiveMarkings,
  maskPersonalData,
  computeFreshnessPenalty,
  evaluateExposure,
  evaluateCapacity,
  computeExposureScore,
  computeCapacityScore,
  computeAttributionScore,
  computeSensitivityScore,
  computeDocumentExposureAssessment,
  computeRiskBand,
  computeAssessment,
  computeDefenseAssessment
};
