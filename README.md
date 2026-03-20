# Local-First Claude Assistant MVP

Production-minded modular monolith for a ChatGPT-like local assistant with:
- FastAPI backend (Python 3.12)
- Next.js frontend (TypeScript)
- PostgreSQL + pgvector
- Redis
- Anthropic Claude provider via a clean provider abstraction

## What Is Implemented

- Persisted conversations/messages with provider/model/routing/tokens/latency metadata
- Anthropic adapter isolated in `backend/app/providers/anthropic_provider.py`
- Provider abstraction in `backend/app/providers/base.py` and `backend/app/providers/factory.py`
- Deterministic prompt layering in `backend/app/services/prompt_builder.py`
- Routing policy (`manual` / `policy` / `locked`) in `backend/app/services/routing_policy.py`
- Context manager that keeps history, summary memory, and retrieval context separated
- Tool loop with:
  - `search_documents`
  - `get_conversation_summary`
  - `list_uploaded_files`
  - clean stubs for `web_search`, `python_exec`
- File upload + extraction (`.txt`, `.md`, `.pdf`) + chunking + pgvector retrieval + citations
- SSE streaming endpoint and progressive frontend rendering
- Developer settings API for prompt/routing defaults
- Alembic migrations and Docker Compose scaffolding

## Anthropic Model Defaults

All model routing is environment-configurable. Current defaults:
- Fast tier: `claude-haiku-4-5`
- Default tier: `claude-sonnet-4-6`
- Complex tier: `claude-opus-4-6`

Configured through:
- `ANTHROPIC_MODEL_FAST`
- `ANTHROPIC_MODEL_DEFAULT`
- `ANTHROPIC_MODEL_COMPLEX`

## RAG Embeddings Backend

- Backend: `sentence-transformers`
- Default model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector dimension: `384` (stored in pgvector)

Environment variables:
- `EMBEDDING_BACKEND=sentence-transformers`
- `EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
- `EMBEDDING_DIMENSION=384`
- `EMBEDDING_BATCH_SIZE=32`

The first run downloads the model from Hugging Face.

## Schema Management Strategy

Alembic is the canonical schema path.

- Startup auto-runs `alembic upgrade head` when `AUTO_MIGRATE_ON_STARTUP=true` (default).
- If startup migration fails, the backend startup fails (fail-fast behavior).
- If `AUTO_MIGRATE_ON_STARTUP=false`, run migrations manually:

```bash
cd backend
alembic upgrade head
```

## Run In GitHub Codespaces

1. Open this repository in a new GitHub Codespace.
2. Before creating the Codespace, add repository (or organization) Codespaces secrets:
   - `ANTHROPIC_API_KEY` (required for real Claude calls)
3. Wait for the post-create step (`.devcontainer/post-create.sh`) to finish. It:
   - copies `.env.example` -> `.env` and `infra/.env.example` -> `infra/.env` if missing
   - syncs `ANTHROPIC_API_KEY` from the Codespaces environment into those env files when provided
   - installs backend and frontend dependencies
4. Start the full stack:

```bash
docker compose version
make up
```

5. In Codespaces **Ports**:
   - open port `3000` for the frontend
   - open port `8000` for the backend API

If `docker compose version` fails, the full Compose path is not available in that Codespace session yet. In that case:
- rebuild/reopen the Codespace so devcontainer features are reapplied, or
- use the "Run Without Docker (Optional)" path for partial app checks (without the full Postgres/pgvector/Redis compose topology).

Quick check that Anthropic secret is not placeholder:

```bash
python3 - <<'PY'
from pathlib import Path
val = ""
for line in Path("infra/.env").read_text().splitlines():
    if line.startswith("ANTHROPIC_API_KEY="):
        val = line.split("=", 1)[1].strip()
        break
print("configured" if val and val != "your_anthropic_api_key" else "placeholder")
PY
```

## Run (Docker Compose)

1. `cp infra/.env.example infra/.env`
2. Fill at least:
   - `ANTHROPIC_API_KEY`
3. Start:

```bash
make up
```

Endpoints:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Run Without Docker (Optional)

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Minimal Manual Check

1. Create/select a conversation in the UI
2. Upload one `.txt`, `.md`, or `.pdf`
3. Ask a question grounded in uploaded content
4. Verify streamed response + citations
5. Switch routing mode to `manual` and set a model override
6. Update prompt layers in dev settings

## Nominal RAG Path Validation (Real DB)

The script below validates the backend nominal path:
`upload -> chunk -> embed -> persist -> retrieve`

Prerequisites:
1. PostgreSQL with `pgvector` is running and reachable by `DATABASE_URL`
2. Backend schema is migrated (`alembic upgrade head` or startup auto-migration)

Run:

```bash
cd backend
python3 scripts/validate_rag_nominal.py \
  --text "RAG validation text about migration policy and model routing." \
  --query "migration policy routing"
```

Expected success signal:
- Exit code `0`
- JSON output with `chunks_created > 0`, `persisted_chunks > 0`, and `retrieval_hit_count > 0`

## Validation Notes (Current Environment)

This repository includes tests for provider normalization, prompt precedence, routing decisions, tool loop, RAG retrieval formatting, API health, SSE streaming smoke, and upload API integration.

Observed in this environment:
- `python3 -m pytest` passed (`10 passed`).
- Real embedding backend check passed (`SentenceTransformerEmbeddingModel`, vector length `384`).
- Nominal RAG validation script was added but not executed end-to-end here because no reachable PostgreSQL/pgvector instance was available.
- Docker runtime validation could not run because `docker` is not installed.
- Local PostgreSQL runtime validation could not run because no reachable server was available on `localhost:5432`.
- Real Anthropic runtime chat validation was not possible because `ANTHROPIC_API_KEY` is placeholder/missing.

Codespaces-targeted static validation completed:
- `.devcontainer/devcontainer.json` is present and parseable.
- `.devcontainer/post-create.sh` shell syntax is valid.
- `.devcontainer/sync_secrets.py` runs and handles missing placeholder secrets safely.
- Existing backend tests still pass.

Still requires execution inside an actual Codespace to fully prove:
- port forwarding behavior/UI reachability on forwarded `3000` and `8000`
- Docker-in-Codespaces startup for the full compose stack on the target account/runtime
- real Anthropic call + streamed response with a valid Codespaces secret

## Phase 2 Candidates

- Add OpenAI/Gemini/Mistral/OpenAI-compatible providers
- Improve retrieval ranking and hybrid search
- Better long-horizon memory summarization worker
- Harden tool sandboxing/permissions
- Multi-user auth and workspace isolation
