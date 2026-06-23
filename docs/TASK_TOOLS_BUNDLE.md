# Task: Deploy Tools Bundle VM

Agent in tmux session `nebius101` must deploy one VM on Nebius that hosts optional AI tools via Docker Compose.

## Goal

Create a single VM named `nebius10-tools` running these services in Docker Compose:

1. **Stirling PDF** — port `8080`
2. **Open WebUI** — port `3000`
3. **Browser Use service** (optional if resources allow) — port `8001`

The router will reach these tools via **private IP** over VPC. Only one public IP is needed, and ideally only the router has a public IP.

## Constraints

- **Public IPv4 quota is limited (3 total).** Prefer to deploy this VM **without public IP**.
- **Budget:** target VM should be cheap enough to keep total monthly burn reasonable. Prefer `cpu-e2` / `cpu-d3`, `4vcpu-16gb` or `2vcpu-4gb` if tests pass. Ask owner if 8vcpu-32gb is needed.
- **Do not commit credentials.** Use env files and .gitignore.
- **Self-contained:** all files in repo under `tools/`, `docker-compose.tools.yml`, `nebius/deploy-tools-vm.sh`.
- **Smoke test:** curl each service endpoint from inside the VM, and verify router can proxy to one of them.

## Step-by-Step

### 1. Create deployment files

Create `tools/docker-compose.tools.yml`:

```yaml
version: "3.9"
services:
  stirling-pdf:
    image: frooodle/s-pdf:latest
    container_name: stirling-pdf
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      - DOCKER_ENABLE_SECURITY=false
      - LANGS=en_en
    networks:
      - tools-net

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:8080"
    environment:
      - PORT=8080
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - open-webui-data:/app/backend/data
    networks:
      - tools-net

  browser-use:
    # Optional, only if Docker image is ready
    image: browseruse/browser-use:latest
    container_name: browser-use
    restart: unless-stopped
    ports:
      - "127.0.0.1:8001:8000"
    networks:
      - tools-net

networks:
  tools-net:
    driver: bridge

volumes:
  open-webui-data:
```

Create wrapper script `tools/start-tools.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose -f docker-compose.tools.yml up -d
```

Create `nebius/deploy-tools-vm.sh` that:

1. Checks Nebius auth.
2. Finds subnet ID.
3. Creates VM `nebius10-tools` via `nebius compute instance create` with cloud-init that installs Docker + Docker Compose.
4. Uses `nebius compute instance ssh` or `scp` to copy `tools/` directory.
5. SSHs in and runs `tools/start-tools.sh`.
6. Prints private IP of the VM.

VM should have no public IP (`--public=false`).

### 2. Choose VM size

Start with cheapest that can run Stirling PDF + Open WebUI:
- Preferred: `cpu-e2` / `2vcpu-4gb` (test first)
- Fallback: `cpu-d3` / `4vcpu-16gb`
- Only use bigger if Open WebUI or Browser Use fails to start.

### 3. Wire router to tools

Update `src/router/config.py`/`deploy-router.sh` to add env vars:

```bash
STIRLING_PDF_URL=http://<TOOLS_VM_PRIVATE_IP>:8080
OPEN_WEBUI_URL=http://<TOOLS_VM_PRIVATE_IP>:3000
BROWSER_USE_URL=http://<TOOLS_VM_PRIVATE_IP>:8001
```

Add new routes in `src/router/routers/`:
- `GET/POST /tools/pdf/status` — proxy health Stirling PDF
- `POST /tools/pdf/convert` — proxy convert job
- `GET /tools/chatui/status` — proxy Open WebUI health

Keep it simple: just proxy/health checks first.

### 4. Redeploy router

Only after tools VM is healthy. If public IP quota masih penuh, hold redeploy and document blocker.

### 5. Smoke tests

From inside tools VM:

```bash
curl -s http://localhost:8080/api/v1/info
curl -s http://localhost:3000/api/v1/config
```

From router or any Nebius endpoint:

```bash
curl -s http://<ROUTER_IP>/tools/pdf/status -H "Authorization: Bearer ..."
```

If Browser Use deployed, test its health endpoint.

### 6. Docs & commit

- Update `docs/AGENT_LOG.md` with results.
- Update `docs/RUNBOOK.md` with tools VM IP and routes.
- Update `README.md` section Optional Tools.
- Commit all new files.

## When Blocked

If any of these happens, stop and ask owner:
- Public IP quota prevents anything.
- Nebius VM creation fails repeatedly.
- Browser Use image won't start or needs GPU.
- Costs look like they will exceed $300/month for this VM alone.

## Success Criteria

- [ ] `nebius10-tools` VM exists and is RUNNING.
- [ ] Stirling PDF reachable on private IP:8080.
- [ ] Open WebUI reachable on private IP:3000.
- [ ] Router has env vars pointing to tools VM.
- [ ] At least one new `/tools/*` route returns healthy response.
- [ ] All changes committed and documented.
