#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Starting Tools Bundle (Stirling PDF + Open WebUI + optional Browser Use)..."
docker compose -f docker-compose.tools.yml up -d

echo ""
echo "Services starting. Check status with:"
echo "  docker compose -f docker-compose.tools.yml ps"
echo "  docker compose -f docker-compose.tools.yml logs -f"
