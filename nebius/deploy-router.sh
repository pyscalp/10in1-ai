#!/usr/bin/env bash
set -euo pipefail

# Deploy the Workbench Router on Nebius Serverless AI.
# Usage:
#   docker build -t <your-hub>/nebius10-router:latest -f Dockerfile.router .
#   docker push <your-hub>/nebius10-router:latest
#   bash nebius/deploy-router.sh <your-hub>/nebius10-router:latest

IMAGE="${1:?Pass the router Docker image as the first argument.}"
: "${ROUTER_AUTH_TOKEN:?Set ROUTER_AUTH_TOKEN env variable first.}"

ENDPOINT_NAME="${ENDPOINT_NAME:-nebius10-router}"
SUBNET_ID="${SUBNET_ID:-$(nebius vpc subnet list --format jsonpath='{.items[0].metadata.id}')}"

echo "Subnet ID: $SUBNET_ID"
echo "Deploying router from image $IMAGE ..."

nebius ai endpoint create \
  --name "$ENDPOINT_NAME" \
  --image "$IMAGE" \
  --platform "${ROUTER_PLATFORM:-cpu-d3}" \
  --preset "${ROUTER_PRESET:-4vcpu-16gb}" \
  --public \
  --container-port 8000 \
  --auth token \
  --token "$ROUTER_AUTH_TOKEN" \
  --env "APP_ENV=production" \
  --env "LOG_LEVEL=info" \
  --env "ROUTER_AUTH_TOKEN=${ROUTER_AUTH_TOKEN}" \
  --env "NEBIUS_LLM_URL=${NEBIUS_LLM_URL:-}" \
  --env "NEBIUS_LLM_MODEL=${NEBIUS_LLM_MODEL:-Qwen/Qwen3-0.6B}" \
  --env "NEBIUS_LLM_TOKEN=${NEBIUS_LLM_TOKEN:-}" \
  --env "SUPABASE_URL=${SUPABASE_URL:-}" \
  --env "SUPABASE_KEY=${SUPABASE_KEY:-}" \
  --env "SUPABASE_DB_URL=${SUPABASE_DB_URL:-}" \
  --env "DATABASE_URL=${DATABASE_URL:-}" \
  --env "STIRLING_PDF_URL=${STIRLING_PDF_URL:-}" \
  --env "LANGFLOW_URL=${LANGFLOW_URL:-}" \
  --env "DIFY_URL=${DIFY_URL:-}" \
  --env "DIFY_API_KEY=${DIFY_API_KEY:-}" \
  --env "OPEN_WEBUI_URL=${OPEN_WEBUI_URL:-}" \
  --env "BROWSER_USE_URL=${BROWSER_USE_URL:-}" \
  --env "MAXUN_URL=${MAXUN_URL:-}" \
  --env "OPENHANDS_URL=${OPENHANDS_URL:-}" \
  --env "OPENHANDS_API_KEY=${OPENHANDS_API_KEY:-}" \
  --env "COOLIFY_URL=${COOLIFY_URL:-}" \
  --env "COOLIFY_API_TOKEN=${COOLIFY_API_TOKEN:-}" \
  --env "COOLIFY_WEBHOOK_UUID=${COOLIFY_WEBHOOK_UUID:-}" \
  --env "CRAWL4AI_URL=${CRAWL4AI_URL:-}" \
  --env "TOOLS_STIRLING_PDF_URL=${TOOLS_STIRLING_PDF_URL:-}" \
  --env "TOOLS_OPEN_WEBUI_URL=${TOOLS_OPEN_WEBUI_URL:-}" \
  --env "TOOLS_BROWSER_USE_URL=${TOOLS_BROWSER_USE_URL:-}" \
  --subnet-id "$SUBNET_ID"

echo "Waiting for router endpoint to become Running ..."

for _ in $(seq 1 40); do
  sleep 10
  STATUS=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.state}' 2>/dev/null || echo "PENDING")
  echo "Status: $STATUS"
  if [ "$STATUS" = "RUNNING" ]; then
    break
  fi
done

ENDPOINT_IP=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.public_endpoints[0]}')
echo ""
echo "Router endpoint IP: $ENDPOINT_IP"
echo ""
echo "Test it:"
echo "  curl -H \"Authorization: Bearer ${ROUTER_AUTH_TOKEN}\" http://${ENDPOINT_IP}/health"
