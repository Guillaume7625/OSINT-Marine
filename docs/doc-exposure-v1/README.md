# Document Exposure Detector V1 — Safe Base

This folder contains the first safe, additive base for a V1 focused on **defensive discovery of publicly exposed documents**.

## Scope of this branch

This branch intentionally pushes only items that are low-risk and directly reusable:
- V1 architecture note centered on targeted public discovery
- example rule sets for attribution and sensitivity scoring
- example bootstrap files for approved sources and seeds

## What is intentionally not pushed here

To avoid breaking the current repository, this branch does **not** yet modify the active backend runtime, database models, or frontend routes.

Excluded at this stage:
- DB migrations
- new API routes wired into production app
- workers integrated into runtime
- removal of current assistant features
- OCR or broad web scraping

## Design principles

- public-only
- document-first
- multisignal attribution
- human review required
- auditability by default
- data minimization
- anti-drift guardrails

## Next safe implementation steps

1. Add SQLAlchemy models and Alembic migration for:
   - sources
n   - seeds
   - discovery_runs
   - discovered_urls
   - artifacts
   - documents
   - score_runs
   - cases
   - reviews
   - audit_events
2. Add first two connectors:
   - manual_url
   - sitemap
3. Add light fetch, quarantine, and AV scan
4. Add parsing, scoring, and case creation

## Anti-drift constraints

The V1 must not introduce:
- search by person
- people dashboards
- top emails / top names views
- social or organizational graphs
- timeline of activity by person
- enrichment around a potentially sensitive document beyond minimal proof
