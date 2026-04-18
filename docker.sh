#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available in PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start Docker Desktop and try again."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Docker Compose was not found. Install Docker Compose v2 or v1."
  exit 1
fi

usage() {
  cat <<'USAGE'
Usage: ./docker.sh <command>

Commands:
  up       Build and start all services in background
  down     Stop and remove services
  logs     Follow service logs
  rebuild  Rebuild images with no cache and start services
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

case "$1" in
  up)
    "${COMPOSE_CMD[@]}" up -d --build
    ;;
  down)
    "${COMPOSE_CMD[@]}" down --remove-orphans
    ;;
  logs)
    "${COMPOSE_CMD[@]}" logs -f --tail=200
    ;;
  rebuild)
    "${COMPOSE_CMD[@]}" build --no-cache
    "${COMPOSE_CMD[@]}" up -d
    ;;
  *)
    usage
    exit 1
    ;;
esac
