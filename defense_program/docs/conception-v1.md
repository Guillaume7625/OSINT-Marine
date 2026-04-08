# 1. Objectif V1

Construire un MVP defensif de detection d'exposition documentaire publique pour contexte Marine/Defense, avec:
- pivot `document-first`;
- separation stricte `detection d'exposition` vs `analyse capacitaire`;
- revue humaine obligatoire;
- anti-derives natives (pas de surveillance individuelle).

# 2. Hypotheses et arbitrages

## Faits
- Le MVP actuel est un monolithe Node.js en memoire pour accelerer la realisation.
- Le schema SQL cible une persistance relationnelle exploitable.
- Les scores sont deterministes et explicables.

## Hypotheses
- Validation juridique/institutionnelle effectuee hors outil.
- Equipe MVP restreinte: `governance_admin`, `reviewer`, `analyst`, `exporter`.
- Volume initial modere (pas de collecte massive).

## Arbitrages
- Retenu au MVP: moteur de regles explicites, RBAC simple par header, audit trail natif.
- Ecarte au MVP: moteur ML opaque, graphes sociaux complexes.
- Discute mais retenu: stockage memoire pour API de reference; SQL fourni comme cible industrielle.

# 3. Stack retenue

| Composant | Choix V1 | Pourquoi | Ce que ca remplace | Risque reduit | Risque introduit |
|---|---|---|---|---|---|
| API | Node.js HTTP natif | Simplicite immediate | Framework lourd | Dette initiale | Moins de middlewares prets a l'emploi |
| Scoring | Regles JS deterministes | Explicabilite | Boite noire ML | Surqualification opaque | Calibration manuelle necessaire |
| Donnees | Schema SQL relationnel | Auditabilite, contraintes | Store ad hoc non contraint | Incoherences de donnees | Migration a industrialiser |
| Config metier | JSON versionne | Gouvernance claire | Regles codees en dur | Drift silencieux | Discipline de versionning requise |
| Tests | Node test runner | Leger et rapide | Setup test complexe | Regressions non detectees | Couverture encore partielle |

# 4. Architecture technique

## Vue d'ensemble
- `api/server.js`: orchestration HTTP, RBAC, anti-derives.
- `scoring/engine.js`: scores attribution/sensibilite + exposition/capacite.
- `config/*.json`: gouvernance, rulesets, marquages sensibles.
- `bdd/schema.sql`: cible persistante V2 renforcee.

## Flux principal
1. Discovery job cible (seed + source allowlistee).
2. Evaluation documentaire (`/api/v1/documents/assess`).
3. Scoring dual:
   - `attributionScore`
   - `sensitivityScore`
4. Decision enrichissement:
   - `halt_and_escalate` si marquage sensible ou seuil sensibilite depasse;
   - sinon `continue_limited`.
5. Decision humaine tracee si un analyste decide d'ouvrir un cas.

## Controle de separation
- Le moteur ne calcule pas de capacite sans input explicite.
- La sortie indique `capacity.status = not_provided` si aucun input capacitaire.

## Garde-fous anti-derive
- Separation exposition/capacite conservee.
- Audit des actions sensibles conserve.
- Export limite aux roles autorises.

# 5. Arborescence projet

```text
defense_program/
  api/
    server.js
  bdd/
    schema.sql
  config/
    governance.v1.json
    scoring-rules.v1.json
    sensitivity-markings.v1.json
  docs/
    conception-v1.md
  scoring/
    engine.js
  tests/
    api.test.js
    engine.test.js
  README.md
  package.json
```

# 6. Schema de donnees

Tables principales:
- `governance_policy_versions`, `rule_sets`
- `seeds`, `sources`
- `discovery_jobs`
- `documents`, `document_evidence`, `document_signals`
- `document_assessments` (attribution/sensibilite/exposition)
- `capacity_assessments` (strictement separe)
- `defense_cases`, `case_decisions`, `case_exports`
- `audit_events`, `retention_policies`

Contraintes clefs:
- checks stricts sur bornes de scores;
- statuts de workflow encadres;
- index pour audit et file de cas;
- FK pour tracabilite de bout en bout.

# 7. APIs

Endpoints MVP exposes:
- `GET /api/v1/health`
- `GET /api/v1/readiness`
- `POST /api/v1/assessments` (exposition/capacite explicites)
- `GET /api/v1/assessments`, `GET /api/v1/assessments/:id`
- `POST /api/v1/documents/assess`
- `POST /api/v1/seeds`, `GET /api/v1/seeds`
- `POST /api/v1/sources`, `GET /api/v1/sources`
- `POST /api/v1/jobs/discovery`, `GET /api/v1/jobs`
- `POST /api/v1/cases`, `GET /api/v1/cases`, `GET /api/v1/cases/:id`
- `POST /api/v1/cases/:id/decisions`
- `POST /api/v1/cases/:id/export`
- `GET /api/v1/audit/events`

RBAC minimal:
- `governance_admin`: creation seeds/sources
- `reviewer`: decisions de cas
- `exporter`: export dossier
- `analyst`: consultation/assessment sans privileges sensibles

# 8. Jobs et orchestration

| Job | Declenchement | Retries | Timeout | Idempotence | Echec |
|---|---|---|---|---|---|
| `discovery` | API manuelle | 3 | 300s | clef d'idempotence | statut `dead_letter` |
| `fetch_light` | apres discovery | 3 | 120s | URL+hash | audit + retry |
| `download_controlled` | si prefiltre ok | 2 | 180s | hash cible | quarantaine fail |
| `parse` | quarantaine passee | 2 | 180s | hash+parser version | cas d'erreur trace |
| `extract` | parse succes | 2 | 120s | hash+extract version | fallback texte brut |
| `score` | extraction dispo | 1 | 60s | signals signature | blocage si signal unique fort |
| `reporting` | planifie | 1 | 120s | fenetre temporelle | alerte ops |
| `cleanup` | planifie | 0 | 120s | batch id | audit purge |

# 9. Moteur de scoring

Design concret implemente:
- `computeAttributionScore`:
  - multisignal obligatoire;
  - `singleSignalCap` applique si convergence insuffisante.
- `computeSensitivityScore`:
  - regles explicites et ponderees.
- `computeDocumentExposureAssessment`:
  - produit `exposureDetectionScore`;
  - decide `halt_and_escalate` vs `continue_limited`.
- `computeDefenseAssessment`:
  - garde la separation avec capacite optionnelle seulement.

## Ce qui est volontairement exclu du MVP
- inférence capacitaire a partir des seuls documents;
- modele IA opaque pour classification;
- corrélations automatiques personnes-unites;
- auto-creation de cas.

# 10. Interface analyste

UX ciblee anti-derive:
- vues prioritaires `documents`, `cas`, `scores`, `preuves`, `statuts`;
- pas de page personnes;
- pas de recherche nominale globale;
- extraits affiches tels quels pour l'exercice.

Ecrans minimum:
- liste cas;
- detail cas avec motifs et preuves minimales;
- decision reviewer;
- export restreint.

# 11. Journalisation et observabilite

- Logs JSON structures (role, action, resource, ids).
- `audit_events` pour toute action sensible.
- IDs correles: `jobId`, `caseId`, `assessmentId`.
- Health checks: `/health`, `/readiness`.
- Indicateurs de derive:
  - nombre d'arrets d'enrichissement;
  - ratio faux positifs par ruleset.

# 12. Securite

Mesures MVP:
- arret d'enrichissement automatique sur signaux sensibles;
- evidence minimale uniquement;
- conservation du contenu brut pour l'exercice;
- RBAC minimal mais strict;
- journalisation des exports.

## Garde-fous anti-derive
- audit des creations, decisions et exports;
- separation stricte entre detection documentaire et calcul capacitaire.

# 13. Gouvernance minimale

Responsabilites V1:
- graines: `governance_admin`
- taxonomies: `governance_admin`
- corpus de reference: `governance_admin`
- allowlist/denylist: `governance_admin`
- validation rulesets: `governance_admin`
- arbitrage faux positifs: `reviewer`
- export dossier: `exporter`
- acces preuves completes: `reviewer` et `exporter`

Versionning:
- ruleset versionne par `version_tag`;
- approbation explicite avant activation.

# 14. Plan de tests

- Unitaires scoring:
  - multisignal cap,
  - seuil sensibilite,
  - separation capacite absente/presente.
- Integration API:
  - lifecycle assessment,
  - RBAC,
  - absence d'auto-creation de cas,
  - conservation de l'audit trail.
- Non-regression:
  - tests endpoints historiques.
- Securite basique:
  - controles methodes/roles,
  - audit trail des actions sensibles.

# 15. Plan de deploiement

- Lancement local:
  - `npm start`
  - `npm test`
- Persistance PostgreSQL:
  - `DATABASE_URL=... npm run db:migrate`
  - `STORE_BACKEND=postgres DATABASE_URL=... npm start`
- Evolution cible:
  - ajouter migrations versionnees (Alembic/Liquibase/Flyway equivalent) au-dela du bootstrap SQL;
  - ajouter scheduler leger pour jobs recurrents;
  - ajouter sauvegarde DB + runbook restauration.

Runbook minimal:
- suspendre une source: mettre `policy_status=denylisted`;
- suspendre un ruleset: `status=retired`;
- rollback: revenir au ruleset precedent versionne.

# 16. MVP par lots de livraison

1. Lot 1 (fait):
   - scoring explicable,
   - API assessment,
   - tests de base.
2. Lot 2 (fait):
   - anti-derive API,
   - stop enrichment,
   - RBAC minimal,
   - audit trail.
3. Lot 3 (a realiser):
   - persistance SQL effective,
   - worker scheduler reel,
   - UI analyste serveur.

# 17. Criteres d'acceptation

| Critere | Verification |
|---|---|
| Separation exposition/capacite | Test `capacity.status = not_provided` sans input capacitaire |
| Stop enrichment actif | Document sensible => `halt_and_escalate` dans l'evaluation |
| Filtres API | `/cases?person=...` reste autorise |
| RBAC gouvernance | Creation seed/source refusee hors `governance_admin` |
| RBAC revue/export | Decision reservee `reviewer`, export reserve `exporter` |
| Auditabilite | Actions critiques visibles via `/api/v1/audit/events` |
| Explicabilite scoring | `breakdown` present dans les reponses de scoring |

# 18. Limites et suites

Limites:
- stockage memoire (non persistant);
- pas de scheduler de production;
- UI non implementee dans ce depot.

Suites recommandees:
1. brancher PostgreSQL + migrations;
2. implementer workers reels (`discovery`, `parse`, `cleanup`);
3. ajouter UI Jinja/HTMX interne avec memes garde-fous;
4. ajouter mesure de calibration des rulesets via retour reviewer.
