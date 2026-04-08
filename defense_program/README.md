# Defense Program V1

Implementation V2 renforcee d'un programme defensif qui separe strictement:
- la **detection d'exposition documentaire**;
- l'**analyse capacitaire** (optionnelle, explicite, separee);
- le **workflow de revue humaine** avec anti-derives.

## Arborescence

- `docs/conception-v1.md`: base de realisation technique complete.
- `bdd/schema.sql`: schema SQL V2 renforce.
- `bdd/schema.postgres.sql`: schema PostgreSQL relationnel applique par migration.
- `scoring/engine.js`: scoring deterministe (attribution/sensibilite/exposition + capacite).
- `api/server.js`: API HTTP avec RBAC minimal, audit, garde-fous anti-derive.
- `config/*.json`: gouvernance et rulesets versionnes.
- `tests/`: tests unitaires et integration.

## Lancer l'API

```bash
cd defense_program
npm start
```

L'API écoute par défaut sur `http://127.0.0.1:7070`.

Mode de stockage:
- `STORE_BACKEND=memory` (defaut)
- `STORE_BACKEND=postgres` avec `DATABASE_URL`

## Initialiser PostgreSQL

```bash
cd defense_program
DATABASE_URL="postgresql://user:password@localhost:5432/defense_program" npm run db:migrate
```

Puis lancer l'API:

```bash
cd defense_program
STORE_BACKEND=postgres DATABASE_URL="postgresql://user:password@localhost:5432/defense_program" npm start
```

## Vérifier le scoring

```bash
cd defense_program
npm test
```

## Exemple de requête

```bash
curl -X POST http://127.0.0.1:7070/api/v1/documents/assess \
  -H 'Content-Type: application/json' \
  -d '{
    "discoveryUrl": "https://example.org/doc",
    "finalUrl": "https://example.org/doc-final",
    "excerpt": "Contact: op@example.org",
    "extractedText": "Diffusion restreinte",
    "signals": {
      "institutionalLexiconScore": 88,
      "domainTrustScore": 90,
      "templateSignatureScore": 84,
      "metadataConsistencyScore": 82,
      "namingConventionScore": 80,
      "corpusSimilarityScore": 86,
      "diffusionMarkingScore": 95,
      "operationalDetailScore": 75,
      "infrastructureExposureScore": 70,
      "personalDataScore": 30
    }
  }'
```

## Notes

- L'API supporte maintenant `memory` et `postgres`.
- Le schema SQL est applique via `npm run db:migrate` en mode postgres.
- Les garde-fous MVP actifs:
  - blocage des filtres person-centric;
  - arret d'enrichissement sur sensibilite elevee/marquages sensibles;
  - RBAC minimal (`x-role`);
  - audit trail consultable.
