#!/usr/bin/env bash
set -euo pipefail

# Deploy the Crawl4AI microservice on Nebius Serverless AI.
# Usage:
#   docker build -t <your-hub>/nebius10-crawl4ai:v1 -f Dockerfile.crawl4ai .
#   docker push <your-hub>/nebius10-crawl4ai:v1
#   bash nebius/deploy-crawl4ai.sh <your-hub>/nebius10-crawl4ai:v1

IMAGE="${1:?Pass the crawl4ai Docker image as the first argument.}"
ENDPOINT_NAME="${ENDPOINT_NAME:-nebius10-crawl4ai}"
SUBNET_ID="${SUBNET_ID:-$(nebius vpc subnet list --format jsonpath='{.items[0].metadata.id}')}"

# Crawl4AI is browser-heavy; give it a bit more memory for Chromium.
PRESET="${PRESET:-4vcpu-16gb}"

# Public IPv4 quota is tight; deploy privately and let the router reach it
# over the VPC private endpoint.
PUBLIC_IP="${PUBLIC_IP:-false}"

echo "Subnet ID: $SUBNET_ID"
echo "Deploying Crawl4AI from image $IMAGE (public_ip=$PUBLIC_IP) ..."

nebius ai endpoint create \
  --name "$ENDPOINT_NAME" \
  --image "$IMAGE" \
  --platform cpu-d3 \
  --preset "$PRESET" \
  --public="$PUBLIC_IP" \
  --container-port 8000 \
  --env "PORT=8000" \
  --subnet-id "$SUBNET_ID"

echo "Waiting for Crawl4AI endpoint to become Running ..."

for _ in $(seq 1 40); do
  sleep 10
  STATUS=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.state}' 2>/dev/null || echo "PENDING")
  echo "Status: $STATUS"
  if [ "$STATUS" = "RUNNING" ]; then
    break
  fi
done

if [ "$PUBLIC_IP" = "true" ]; then
  ENDPOINT_IP=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.public_endpoints[0]}')
else
  ENDPOINT_IP=$(nebius ai endpoint get-by-name --name "$ENDPOINT_NAME" --format jsonpath='{.status.private_endpoints[0]}')
fi

echo ""
echo "Crawl4AI endpoint IP: $ENDPOINT_IP"
echo ""
echo "Test it:"
echo "  curl -X POST http://${ENDPOINT_IP}/crawl -H 'Content-Type: application/json' -d '{\"url\":\"https://docs.nebius.com\"}'"
