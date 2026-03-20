# Extension Guide

This guide explains how to extend the Cycle Outlook app safely.

## Project Structure
- `app/` core logic
- `templates/` Flask HTML pages
- `static/` CSS
- `tests/` unit tests (no Outlook COM)
- `config.yaml` local settings
- `rules_seed.json` seed rules loaded when the database is empty
- `data/` runtime data (SQLite + logs + summaries)

## Extension Points

### 1) Rules Engine
Files:
- `app/rules_engine.py`
- `app/storage.py`

How it works:
- Hard rules are stored in SQLite and are evaluated first.
- If no rule matches, GENIAL can run (if enabled).
- If GENIAL is disabled or fails, heuristics apply.

Add a new rule type:
1. Update `RulesEngine.match_rules` to interpret the new rule type.
2. Update `rules_seed.json` with example patterns.
3. Add unit tests in `tests/test_rules_engine.py`.

### 2) GENIAL Adapter
Files:
- `app/genial_client.py`
- `templates/genial.html`

How it works:
- `request_template` is Jinja2 with `instructions_utilisateur`, `from`, `to_cc`, `subject`, `received_time_iso`, `body_excerpt`.
- `response_mapping_json` maps JSON paths to `category`, `confidence`, `reasons`.
- Host/port must be in allowlist.

Add a new mapping field:
1. Extend `_map_response` to extract additional fields.
2. Update `GenialResult` and the UI to display it.
3. Add tests in `tests/test_genial_mapping.py`.

### 3) Summaries
Files:
- `app/summarizer.py`
- `templates/resume.html`

Add a new section:
1. Extend `generate_summary` to compute the section.
2. Add a test in `tests/test_summarizer.py`.

### 4) Outlook Integration
File:
- `app/outlook_client.py`

Rules:
- All COM access must run inside `OutlookWorker`.
- Keep COM work in the worker thread only.

### 5) Web UI
File:
- `app/webapp.py`

Add a new route:
1. Add a Flask route in `create_app`.
2. Create a template in `templates/`.
3. Add any security checks using `token_required`.

## Conventions
- Categories are fixed: `CRISES`, `DECISIONS`, `A_LIRE`.
- Do not store full email bodies.
- Always include `explain` for each classification.
- Prefer ASCII in new files unless non-ASCII is required.
- Use `Storage.append_log` for audit-ready logs.

## Testing
Run unit tests (no Outlook required):
```bash
python -m pytest
```

## Common Changes Checklist
- Add or update tests
- Update README
- Keep COM isolated
- Preserve lock behavior
