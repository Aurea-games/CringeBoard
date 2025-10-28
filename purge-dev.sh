#!/usr/bin/env bash
set -euo pipefail

# Always operate from the repository root so compose resolves correctly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.dev.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or available in PATH." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Error: docker compose plugin or docker-compose binary is required." >&2
  exit 1
fi

"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down --rmi local --volumes --remove-orphans
