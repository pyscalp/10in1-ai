#!/usr/bin/env bash
set -euo pipefail

# Deploy a single Tools Bundle VM on Nebius Compute.
# Hosts Stirling PDF (8080), Open WebUI (3000), and optional Browser Use (8001).
# The VM has no public IP; the router reaches it over the VPC private network.
#
# Usage:
#   bash nebius/deploy-tools-vm.sh

VM_NAME="${VM_NAME:-nebius10-tools}"
PLATFORM="${PLATFORM:-cpu-d3}"
PRESET="${PRESET:-4vcpu-16gb}"
SUBNET_ID="${SUBNET_ID:-$(nebius vpc subnet list --format jsonpath='{.items[0].metadata.id}')}"
PROJECT_ID="${PROJECT_ID:-$(nebius vpc subnet get --id "$SUBNET_ID" --format jsonpath='{.metadata.parent_id}' 2>/dev/null || echo '')}"
SSH_USER="${SSH_USER:-ubuntu}"

echo "Project ID: $PROJECT_ID"
echo "Subnet ID: $SUBNET_ID"
echo "Deploying $VM_NAME (platform=$PLATFORM, preset=$PRESET, public_ip=false)..."

# Read the docker-compose and start script content to embed in cloud-init.
TOOLS_DIR="$(dirname "$0")/../tools"
COMPOSE_CONTENT=$(cat "$TOOLS_DIR/docker-compose.tools.yml")
START_SCRIPT_CONTENT=$(cat "$TOOLS_DIR/start-tools.sh")

# Cloud-init: install Docker + Docker Compose plugin, write tools files, and start services.
CLOUD_INIT=$(cat <<EOF
#cloud-config
package_update: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release
  - git
  - jq

users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    groups: [docker]

write_files:
  - path: /opt/nebius-tools/docker-compose.tools.yml
    owner: ubuntu:ubuntu
    permissions: '0644'
    content: |
$(echo "$COMPOSE_CONTENT" | sed 's/^/      /')
  - path: /opt/nebius-tools/start-tools.sh
    owner: ubuntu:ubuntu
    permissions: '0755'
    content: |
$(echo "$START_SCRIPT_CONTENT" | sed 's/^/      /')

runcmd:
  - install -m 0755 -d /etc/apt/keyrings
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  - chmod a+r /etc/apt/keyrings/docker.gpg
  - echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
  - apt-get update
  - apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu
  - bash /opt/nebius-tools/start-tools.sh
EOF
)

# Use an existing boot disk or create one from the custom Ubuntu image.
BOOT_DISK_NAME="${VM_NAME}-boot"
BOOT_DISK_ID=$(nebius compute disk list --format jsonpath="{.items[?(@.metadata.name=='$BOOT_DISK_NAME')].metadata.id}" 2>/dev/null || echo "")

if [ -z "$BOOT_DISK_ID" ]; then
  echo "Creating boot disk $BOOT_DISK_NAME ..."
  # Use a custom Ubuntu image ID from your Nebius project.
  # Get one with: nebius compute image list --format json
  UBUNTU_IMAGE_ID="${UBUNTU_IMAGE_ID:-[IMAGE_ID]}"
  nebius compute disk create \
    --name "$BOOT_DISK_NAME" \
    --parent-id "$PROJECT_ID" \
    --type NETWORK_SSD \
    --size-gibibytes 100 \
    --source-image-id "$UBUNTU_IMAGE_ID"

  BOOT_DISK_ID=$(nebius compute disk list --format jsonpath="{.items[?(@.metadata.name=='$BOOT_DISK_NAME')].metadata.id}")
fi

echo "Boot disk ID: $BOOT_DISK_ID"

# Create the VM without a public IP.
nebius compute instance create \
  --name "$VM_NAME" \
  --parent-id "$PROJECT_ID" \
  --resources-platform "$PLATFORM" \
  --resources-preset "$PRESET" \
  --network-interfaces "[{\"name\":\"eth0\",\"subnet_id\":\"$SUBNET_ID\",\"ip_address\":{}}]" \
  --boot-disk-existing-disk-id "$BOOT_DISK_ID" \
  --boot-disk-attach-mode READ_WRITE \
  --cloud-init-user-data "$CLOUD_INIT" \
  --async

echo ""
echo "Waiting for VM to become RUNNING ..."
for _ in $(seq 1 60); do
  STATUS=$(nebius compute instance get-by-name --name "$VM_NAME" --format jsonpath='{.status.state}' 2>/dev/null || echo "PENDING")
  echo "Status: $STATUS"
  if [ "$STATUS" = "RUNNING" ]; then
    break
  fi
  sleep 10
done

PRIVATE_IP=$(nebius compute instance get-by-name --name "$VM_NAME" --format jsonpath='{.status.network_interfaces[0].ip_address.address}' 2>/dev/null | sed 's|/32||' | tr -d '[:space:]' || echo "")
if [ -z "$PRIVATE_IP" ]; then
  echo "ERROR: could not determine private IP for $VM_NAME"
  exit 1
fi

echo ""
echo "VM private IP: $PRIVATE_IP"

# Wait for cloud-init / Docker / services to finish starting.
echo "Waiting 120s for cloud-init, Docker, and services to start ..."
sleep 120

echo ""
echo "Tools Bundle deployed at private IP: $PRIVATE_IP"
echo "  Stirling PDF: http://${PRIVATE_IP}:8080"
echo "  Open WebUI:   http://${PRIVATE_IP}:3000"
echo "  Browser Use:  http://${PRIVATE_IP}:8001 (optional, disabled by default)"
echo ""
echo "Smoke test from router or another Nebius endpoint:"
echo "  curl -s http://${PRIVATE_IP}:8080/api/v1/info"
echo "  curl -s http://${PRIVATE_IP}:3000/api/config"
