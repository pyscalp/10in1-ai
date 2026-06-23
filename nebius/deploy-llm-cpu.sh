#!/usr/bin/env bash
set -euo pipefail

# Deploy a CPU-based LLM endpoint on Nebius Serverless AI using llama-cpp-python.
# Usage: export AUTH_TOKEN=$(openssl rand -hex 32) && bash nebius/deploy-llm-cpu.sh

: "${AUTH_TOKEN:?Set AUTH_TOKEN env variable first.}"

REGISTRY="${NEBIUS_REGISTRY:-<YOUR_REGISTRY>}"
ENDPOINT_NAME="${ENDPOINT_NAME:-nebius10-llm}"
SUBNET_ID="${SUBNET_ID:-$(nebius vpc subnet list --format jsonpath='{.items[0].metadata.id}')}"

echo "Subnet ID: $SUBNET_ID"
echo "Deploying CPU LLM endpoint (llama-cpp-python) ..."

nebius ai endpoint create \
  --name "$ENDPOINT_NAME" \
  --image "${REGISTRY}/nebius10-llm:cpu" \
  --container-port 8000 \
  --platform cpu-d3 \
  --preset 4vcpu-16gb \
  --auth token \
  --token "$AUTH_TOKEN" \
  --subnet-id "$SUBNET_ID"

echo "Waiting for endpoint to become Running (this may take 3-5 minutes) ..."

for _ in $(seq 1 60); do
  sleep 10
  STATUS=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.state}' 2>/dev/null || echo "PENDING")
  echo "Status: $STATUS"
  if [ "$STATUS" = "RUNNING" ]; then
    break
  fi
done

ENDPOINT_FQDN=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.private_endpoints[0]}')
echo ""
echo "LLM private endpoint: $ENDPOINT_FQDN"
echo "Add this to your .env:"
echo "  NEBIUS_LLM_URL=http://${ENDPOINT_FQDN}/v1"
echo "  NEBIUS_LLM_MODEL=qwen2.5-0.5b-instruct-q4_k_m.gguf"
echo "  NEBIUS_LLM_TOKEN=${AUTH_TOKEN}"
