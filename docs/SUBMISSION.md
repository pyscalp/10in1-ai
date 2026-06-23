# Submission Materials — Nebius Serverless AI Builders Challenge

## Project Name

**Nebius 10-in-1 AI Workbench**

## One-sentence description

A reproducible, serverless RAG workbench that wires 10 open-source AI tools into one pipeline on Nebius AI Cloud.

## Short summary (100 words or less)

Nebius 10-in-1 AI Workbench is a serverless RAG pipeline built on Nebius AI Cloud. It uses a FastAPI router to orchestrate Crawl4AI, managed PostgreSQL pgvector, and a Nebius Serverless AI LLM endpoint. Users ingest any public URL, the content is chunked and embedded, and questions are answered with grounding in retrieved context. The workbench also bundles Stirling PDF, Open WebUI, and adapters for Langflow, Dify, Browser Use, Maxun, OpenHands, Coolify, and Supabase. Everything is containerized, infra-as-code, and reproducible with the deploy scripts in the repository.

## Feature description

The Workbench Router exposes two core endpoints:

- `POST /pipeline/ingest` — crawl a URL, chunk the content, embed it, and store vectors in managed PostgreSQL pgvector.
- `POST /pipeline/ask` — retrieve the most relevant chunks and ask a vLLM endpoint for an answer grounded in the retrieved context.

Key components:

- **Crawl4AI microservice** — dedicated Playwright/Chromium crawler deployed as a separate Nebius Serverless AI Endpoint.
- **FastAPI router** — lightweight orchestrator with Pydantic settings and Bearer-token auth.
- **Managed PostgreSQL pgvector** — vector search and metadata storage.
- **Nebius Serverless AI Endpoint (vLLM)** — OpenAI-compatible LLM backend.
- **Nebius Container Registry** — stores router and Crawl4AI images.

The repository also includes local docker-compose support, deploy scripts, and a full execution log.

## Why Nebius

- **Serverless AI Endpoints** — router, Crawl4AI, and LLM run as managed endpoints with automatic networking and scaling; no Kubernetes cluster to operate.
- **Managed PostgreSQL** — pgvector is available out of the box, eliminating self-hosted vector database ops.
- **Container Registry** — images are built locally and pushed to Nebius Container Registry for deployment.
- **Cost control** — endpoints can be stopped/deleted between tests; CPU presets keep the demo stack affordable.

## Demo video outline

1. **Intro (15s)** — show the repo, README, and architecture diagram.
2. **Live deployment (45s)** — run `deploy-crawl4ai.sh` and `deploy-router.sh`, show endpoints becoming `RUNNING` in Nebius console/CLI.
3. **Smoke test (60s)** —
   - `curl /health`
   - `curl /pipeline/ingest` with `https://docs.nebius.com/llms.txt`
   - `curl /pipeline/ask` with "What AI services does Nebius offer?"
4. **Architecture walkthrough (30s)** — highlight Crawl4AI microservice, router, pgvector, and LLM endpoint.
5. **Closing (15s)** — mention reproducibility, open-source stack, and cost-awareness.

## Links

- Repository: `https://github.com/pyscalp/10in1-ai`
- Live router endpoint: `http://<YOUR_ROUTER_IP>:8000`
- Execution log: `docs/AGENT_LOG.md`
