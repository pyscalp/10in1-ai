#!/usr/bin/env bash
set -euo pipefail

# Local smoke test for the Workbench Router.
# Starts the router in the background, runs a few curl checks, then stops it.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${ROUTER_AUTH_TOKEN:-change-me}"

PYTHON="$ROOT_DIR/.venv/bin/python"
UVICORN="$ROOT_DIR/.venv/bin/uvicorn"

# Start a tiny OpenAI-compatible mock LLM so the RAG step can complete locally.
echo "==> Starting mock LLM server on http://localhost:8001 ..."
"$PYTHON" "$ROOT_DIR/scripts/mock_llm_server.py" &
MOCK_LLM_PID=$!

echo "==> Starting router on $BASE_URL ..."
"$UVICORN" main:app --app-dir "$ROOT_DIR/src/router" --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

_cleanup() {
    echo "==> Stopping router (pid $UVICORN_PID) ..."
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
    echo "==> Stopping mock LLM server (pid $MOCK_LLM_PID) ..."
    kill "$MOCK_LLM_PID" 2>/dev/null || true
    wait "$MOCK_LLM_PID" 2>/dev/null || true
}
trap _cleanup EXIT

# Wait for the router to be ready.
for i in $(seq 1 30); do
    if curl -s "$BASE_URL/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "==> Health check"
curl -s "$BASE_URL/health" | python3 -m json.tool

echo "==> Root endpoint"
curl -s "$BASE_URL/" | python3 -m json.tool

echo "==> Pipeline ingest (example.com)"
curl -s -X POST "$BASE_URL/pipeline/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://example.com","chunk_size":20,"overlap":5}' | python3 -m json.tool

echo "==> Pipeline ask"
curl -s -X POST "$BASE_URL/pipeline/ask" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question":"What is this page about?","top_k":3}' | python3 -m json.tool

echo "==> Smoke test complete"
