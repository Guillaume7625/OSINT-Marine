# Architecture V1 — Targeted Public Document Discovery

## Objective

Build a simple, auditable MVP that discovers **publicly accessible documents** from approved sources, downloads them in quarantine, extracts minimal evidence, scores them, and routes them to human review.

## Core flow

```text
approved source + seed
  -> discovery connector
  -> discovered URL
  -> light fetch
  -> controlled download in quarantine
  -> AV scan
  -> parse text and metadata
  -> extract explicit signals
  -> attribution score + sensitivity score
  -> create case if thresholds are reached
  -> stop enrichment if sensitivity appears high
```

## Components

### API/UI
- FastAPI backend
- internal analyst UI
- source/seed management
- case queue
- review and export actions

### Workers
- discovery worker
- fetch/download worker
- parse/score worker
- cleanup worker

### Storage
- PostgreSQL for source of truth and audit trail
- S3-compatible storage for quarantine, evidence, and exports
- Redis only as a simple broker for background jobs

## Mandatory controls

### Discovery controls
- approved sources only
- no login
- no brute force
- no guessing of hidden paths
- no mass crawling
- bounded pagination and rate limits

### Download controls
- stream download only
- size limits
- redirect limits
- MIME checks
- quarantine first
- AV scan before parsing

### Parsing controls
- parser runs without network egress
- minimal extraction only
- preview must be redacted by default
- OCR disabled by default in MVP

### Decision controls
- no automatic final qualification
- every case reviewed by a human
- every evidence access logged
- every export logged

## Anti-drift guardrails

The MVP is document-centric and must remain structurally unable to become a people-monitoring tool.

Therefore the MVP excludes:
- global name search
- person-centric dashboards
- email rankings
- contact graphs
- activity timelines by person
- speculative enrichment once a document appears sensitive

## First connectors to implement

1. `manual_url`
2. `sitemap`

## Second wave connectors

1. `public_site_listing`
2. `search_api`
3. `public_repository`

## Explicitly out of scope for MVP

- broad internet scraping
- dynamic browser automation by default
- OCR at scale
- entity graphing
- capacity reconstruction
- operational correlation
