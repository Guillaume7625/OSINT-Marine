#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f infra/.env ]; then
  cp infra/.env.example infra/.env
fi

if [ ! -f .env ]; then
  cp .env.example .env
fi

python3 .devcontainer/sync_secrets.py

python3 -m pip install --upgrade pip
python3 -m pip install -e "backend[dev]"
npm --prefix frontend install

if docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is available in this dev container."
else
  echo "Docker Compose is not available yet."
  echo "In Codespaces, 'make up' depends on Docker access via docker-outside-of-docker."
  echo "If this persists, rebuild the container or use the non-Docker run path from README."
fi

echo "Codespaces bootstrap complete."
echo "Run 'make up' to start frontend, backend, postgres/pgvector, and redis."
