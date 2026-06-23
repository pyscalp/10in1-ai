# Nebius 10-in-1 AI Workbench — Deployment Plan

> Target: Nebius Serverless AI Builders Challenge (deadline 15 Jul 2026).  
> Status: **core stack deployed and RAG pipeline working**. See [`RUNBOOK.md`](./RUNBOOK.md) for live resource IDs, endpoints, credentials, and curl commands.

---

## 1. Design Principles

1. **Nebius Serverless AI Endpoint must host the LLM inference** — this is the core challenge primitive.
2. **The Workbench Router also runs on a Nebius Serverless AI Endpoint** — it is the public-facing API that orchestrates the tools.
3. **Stateful or heavy browser workloads live outside Serverless AI Endpoints** — they need persistent disk, long-lived browsers, or Docker sockets.
4. **Demo path is minimal-viable, not full-10-tool-live** — a working RAG pipeline beats a broken 10-tool architecture.
5. **Everything must be reproducible from this repo** — Dockerfiles, compose files, env templates, and deploy scripts.

---

## 2. Final Architecture

```text
                         ┌─────────────────────────────────────┐
                         │  User / Open WebUI / curl / demo    │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────────┐
                    │  Workbench Router                         │
                    │  Nebius Serverless AI Endpoint (CPU)      │
                    │  /pipeline/ingest  +  /pipeline/ask       │
                    └──────────────┬────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   ┌─────────────┐        ┌─────────────────┐       ┌──────────────┐
   │ Crawl4AI    │        │ Nebius LLM      │       │ Stirling PDF │
   │ (optional   │        │ Serverless AI   │       │ (optional    │
   │  microsvc)  │        │ Endpoint (GPU)  │       │  microsvc)   │
   └─────────────┘        └─────────────────┘       └──────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────────────────┐
                    │  Nebius Managed PostgreSQL (pgvector)     │
                    │  chunks table + vector index              │
                    └───────────────────────────────────────────┘
```

### What runs where

| Component | Platform | Why |
|-----------|----------|-----|
| **Workbench Router** | Nebius Serverless AI Endpoint (CPU) | Public API, stateless, challenge requirement |
| **LLM (vLLM)** | Nebius Serverless AI Endpoint (GPU) | Challenge requirement, OpenAI-compatible |
| **Managed PostgreSQL** | Nebius Managed DB | Persistent pgvector, backups, managed |
| **Crawl4AI** | Optional second Endpoint or VM | Needs browser; keep out of router image |
| **Stirling PDF** | Optional second Endpoint or VM | Heavy Java image; keep out of router image |
| **Open WebUI** | Optional Endpoint or VM | Chat UI; can also run locally for demo |
| **Langflow / Dify** | **Skip for demo** | Too heavy for serverless, demo can reference architecture |
| **Browser Use / Maxun** | **Skip for demo** | Browser + GPU/scheduler, out of scope for reproducible demo |
| **OpenHands** | **Skip for demo** | Docker-in-Docker, security risk, not demo-critical |
| **Coolify** | **Skip for demo** | PaaS that needs its own VM; mention as future ops layer |

### Demo scope

The reproducible demo will prove:

1. `POST /pipeline/ingest {url}` → crawl → chunk → embed → store in Nebius Postgres.
2. `POST /pipeline/ask {question}` → retrieve chunks → call Nebius LLM → return answer.

Everything else is documented as **architecture vision** and optional extensions.

---

## 3. Service / Component List

### 3.1 Workbench Router

| Item | Value |
|------|-------|
| Name | `nebius10-router` |
| Platform | Nebius Serverless AI Endpoint |
| Preset | `2vcpu-4gb` CPU (start here; scale if embedding latency too high) |
| Image | Custom Docker image built from `Dockerfile.router` |
| Port | `8000` |
| Auth | Nebius endpoint token + `ROUTER_AUTH_TOKEN` |

**Responsibilities:**
- Expose `/pipeline/ingest` and `/pipeline/ask`.
- Embed text with `sentence-transformers/all-MiniLM-L6-v2`.
- Read/write chunks to Nebius Managed PostgreSQL.
- Proxy chat requests to Nebius LLM Endpoint.

### 3.2 Nebius LLM Endpoint

| Item | Value |
|------|-------|
| Name | `nebius10-llm` |
| Platform | Nebius Serverless AI Endpoint |
| Preset | `1gpu-8vcpu-32gb` (L40s) |
| Image | `vllm/vllm-openai:v0.18.0-cu130` |
| Model | `Qwen/Qwen3-0.6B` (small, cheap, fast) |
| Port | `8000` |
| Auth | Nebius endpoint token |

**Responsibilities:**
- Serve OpenAI-compatible `/v1/chat/completions`.
- Generate RAG answers from router-provided context.

### 3.3 Managed PostgreSQL

| Item | Value |
|------|-------|
| Service | Nebius Managed PostgreSQL |
| Extensions | `vector`, `pgcrypto` |
| Database | `workbench` |
| User | `workbench` (dedicated, least privilege) |
| Network | Same VPC / subnet as endpoints |

**Responsibilities:**
- Store `chunks` table with `embedding vector(384)`.
- Serve similarity search via `pgvector`.

### 3.4 Optional Crawl4AI Microservice

| Item | Value |
|------|-------|
| Name | `nebius10-crawl4ai` |
| Platform | Nebius Serverless AI Endpoint or small VM |
| Preset | `2vcpu-4gb` CPU |
| Image | Custom image with Playwright Chromium installed |
| Port | `8000` |

**Responsibilities:**
- Accept URL, return markdown.
- Keep browser out of the router image.

### 3.5 Optional Stirling PDF Microservice

| Item | Value |
|------|-------|
| Name | `nebius10-stirling` |
| Platform | Nebius Serverless AI Endpoint or small VM |
| Preset | `2vcpu-4gb` CPU |
| Image | `frooodle/s-pdf:latest` |
| Port | `8080` |

**Responsibilities:**
- Convert PDF to text/image when needed.

---

## 4. Environment Variables per Service

### 4.1 Router Endpoint

```bash
# App
APP_NAME=Nebius10in1Workbench
APP_ENV=production
LOG_LEVEL=info
PORT=8000

# Router self-auth
ROUTER_AUTH_TOKEN=<strong-random-token>

# Nebius LLM Endpoint
NEBIUS_LLM_URL=http://<nebius10-llm-ip>/v1
NEBIUS_LLM_MODEL=Qwen/Qwen3-0.6B
NEBIUS_LLM_TOKEN=<nebius-endpoint-token>

# Nebius Managed PostgreSQL
SUPABASE_DB_URL=postgresql://workbench:<password>@<postgres-host>:5432/workbench
# SUPABASE_URL and SUPABASE_KEY can be left empty when SUPABASE_DB_URL is set.

# Optional tool microservices (leave empty if not deployed)
STIRLING_PDF_URL=http://<nebius10-stirling-ip>:8080
LANGFLOW_URL=
DIFY_URL=
DIFY_API_KEY=
OPEN_WEBUI_URL=
MAXUN_URL=
OPENHANDS_URL=
OPENHANDS_API_KEY=
COOLIFY_URL=
COOLIFY_API_TOKEN=
COOLIFY_WEBHOOK_UUID=
```

### 4.2 LLM Endpoint

Set via `deploy-vllm.sh` arguments, not env vars:

```bash
MODEL_ID=Qwen/Qwen3-0.6B
ENDPOINT_NAME=nebius10-llm
AUTH_TOKEN=<strong-random-token>
```

### 4.3 Managed PostgreSQL

Connection string given by Nebius console:

```bash
postgresql://workbench:<password>@<host>:5432/workbench
```

### 4.4 Local Development

```bash
NEBIUS_LLM_URL=http://localhost:8001/v1
NEBIUS_LLM_MODEL=Qwen/Qwen3-0.6B
NEBIUS_LLM_TOKEN=
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

---

## 5. Docker / Build Artifacts

### 5.1 `Dockerfile.router` (existing, needs cleanup)

Current issues:
- Installs Playwright Chromium inside router image → bloat + cold start.
- Bundles all tool adapters but most tools won't run inside the router container.

Required changes:
1. Remove Playwright install from router image.
2. Keep only router + embedding model + psycopg2.
3. Add multi-stage build to reduce image size.
4. Document that crawl/PDF are external services.

Target image size: **< 2 GB** (embedding model is the largest part).

### 5.2 New `Dockerfile.crawl4ai` (optional)

```dockerfile
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-crawl4ai.txt /app/
RUN pip install --no-cache-dir -r requirements-crawl4ai.txt
RUN python -m playwright install chromium
COPY src/crawl4ai_service /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.3 `docker-compose.yml` (local only)

Keep for local dev:
- `postgres` (pgvector)
- `stirling-pdf`
- Optional `open-webui`, `langflow`, `maxun` under `profiles: [full]`

Remove or mark as non-production.

---

## 6. Deploy Scripts

### 6.1 `nebius/deploy-vllm.sh`

Already exists. Verify before run:
- `nebius` CLI authenticated.
- Subnet exists in target folder.
- `--platform` and `--preset` still valid in current CLI version.

### 6.2 `nebius/deploy-router.sh`

Already exists. Required updates:
- Remove unused tool env vars from default deploy, or document them as optional.
- Add `SUPABASE_DB_URL` as required env.
- Ensure Docker image is pushed to a registry Nebius can pull from.

### 6.3 New `nebius/deploy-postgres.sh` (optional)

If CLI supports managed DB creation, script it. Otherwise document manual steps.

### 6.4 New `nebius/deploy-crawl4ai.sh` (optional)

Deploy Crawl4AI as separate endpoint.

---

## 7. Cost / Resource Estimation

Assumptions: demo runs for ~2 weeks, light traffic.

| Component | Resource | Est. Cost (USD) |
|-----------|----------|-----------------|
| LLM Endpoint | `1gpu-8vcpu-32gb` L40s | ~$1.5–3/hour while active; serverless billing per request |
| Router Endpoint | `2vcpu-4gb` CPU | ~$0.05–0.10/hour |
| Managed PostgreSQL | Small instance + storage | ~$0.05–0.15/hour |
| Crawl4AI (optional) | `2vcpu-4gb` CPU | ~$0.05–0.10/hour |
| Stirling PDF (optional) | `2vcpu-4gb` CPU | ~$0.05–0.10/hour |
| Egress / requests | Minimal | <$10 |

**Total demo burn: roughly $50–200 for 2 weeks**, depending on LLM call volume and idle behavior.  
With $5000 credit, plenty of headroom for iteration.

**Cost optimization tips:**
- Use smallest GPU preset that loads Qwen3-0.6B.
- Scale router to `1vcpu-2gb` if latency acceptable.
- Keep optional services off unless recording demo.
- Use local mock LLM for CI/unit tests.

---

## 8. Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Nebius CLI syntax changed | Deploy fails | Test with `--dry-run`, read latest docs before run |
| Router image too large | Cold start >5 min | Strip Playwright, use multi-stage build |
| LLM endpoint won't start | Demo dead | Verify model ID and vLLM image compatibility |
| Managed DB network access | Router can't connect | Put all resources in same VPC/subnet |
| Playwright still unstable | Crawl fails | Keep HTTP fallback in pipeline |
| Embedding model slow on CPU | High latency | Use smaller model or warm endpoint |

---

## 9. Next Steps (in order)

1. **Clean `Dockerfile.router`** — remove Playwright, multi-stage build.
2. **Update `.env.example`** — reflect production env vars.
3. **Update `nebius/deploy-router.sh`** — make `SUPABASE_DB_URL` required, drop unused defaults.
4. **Create `docs/PRODUCTION_ENV.md`** — step-by-step env setup.
5. **Test local build** — `docker build -f Dockerfile.router .` must succeed.
6. **Manual Nebius auth + create managed Postgres** — after lu fix auth.
7. **Deploy LLM endpoint** — run `nebius/deploy-vllm.sh`.
8. **Deploy router endpoint** — run `nebius/deploy-router.sh`.
9. **End-to-end smoke test** — ingest public URL, ask question.
10. **Record demo + finalize README/blog**.

---

## 10. Summary

- **Core on Nebius Serverless AI Endpoint:** Router + LLM.
- **Managed service:** PostgreSQL with pgvector.
- **Optional extensions:** Crawl4AI, Stirling PDF, Open WebUI as separate endpoints/VMs.
- **Skipped for demo:** Langflow, Dify, Browser Use, Maxun, OpenHands, Coolify — documented as architecture vision.
- **Demo proof:** `/pipeline/ingest` + `/pipeline/ask` end-to-end on Nebius.
