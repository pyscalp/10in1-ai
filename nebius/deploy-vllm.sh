#!/usr/bin/env bash
set -euo pipefail

# Deploy a small vLLM endpoint on Nebius Serverless AI.
# Usage: export AUTH_TOKEN=$(openssl rand -hex 32) && bash nebius/deploy-vllm.sh

: "${AUTH_TOKEN:?Set AUTH_TOKEN env variable first.}"

MODEL_ID="${MODEL_ID:-Qwen/Qwen3-0.6B}"
ENDPOINT_NAME="${ENDPOINT_NAME:-nebius10-llm}"
SUBNET_ID="${SUBNET_ID:-$(nebius vpc subnet list --format jsonpath='{.items[0].metadata.id}')}"

echo "Subnet ID: $SUBNET_ID"
echo "Deploying vLLM endpoint with model $MODEL_ID ..."

nebius ai endpoint create \
  --name "$ENDPOINT_NAME" \
  --image vllm/vllm-openai:v0.18.0-cu130 \
  --container-command "python3 -m vllm.entrypoints.openai.api_server" \
  --args "--model ${MODEL_ID} --host 0.0.0.0 --port 8000" \
  --platform gpu-l40s-a \
  --preset 1gpu-8vcpu-32gb \
  --container-port 8000 \
  --auth token \
  --token "$AUTH_TOKEN" \
  --shm-size 16Gi \
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
echo "  NEBIUS_LLM_MODEL=${MODEL_ID}"
echo "  NEBIUS_LLM_TOKEN=${AUTH_TOKEN}"
