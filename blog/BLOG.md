# Building a 10-in-1 Open-Source AI Workbench on Nebius Serverless AI

For the **Nebius Serverless AI Builders Challenge**, I wanted to solve a problem I keep hitting: there are dozens of great open-source AI tools, but wiring them into one reproducible pipeline usually means writing a lot of glue code. This project turns ten of them into a single serverless workbench on Nebius AI Cloud.

## What it is

**Nebius 10-in-1 AI Workbench** is a FastAPI router that exposes:

- **Crawl4AI** for LLM-ready web crawling
- **Stirling PDF** for PDF conversion, OCR, and editing
- **Open WebUI** as a self-hosted chat interface
- **Supabase / PostgreSQL + pgvector** for vector storage
- Adapters for **Langflow, Dify, Browser Use, Maxun, OpenHands, and Coolify**

The core demo is a RAG pipeline: send a URL to `/pipeline/ingest`, ask a question via `/pipeline/ask`, and get an answer grounded in retrieved context.

## Live architecture

```text
User/curl/Open WebUI
        │
        ▼
Workbench Router  ──►  Crawl4AI microservice
(Nebius Serverless)    (fetch + markdown)
        │                        │
        ▼                        ▼
   LLM endpoint  ◄─────  PostgreSQL pgvector
(Nebius Serverless)      (chunks + embeddings)
```

- Router, LLM inference, and Crawl4AI each run as **Nebius Serverless AI Endpoints**.
- Embeddings use `sentence-transformers/all-MiniLM-L6-v2`.
- The LLM (currently `Qwen2.5-0.5B-Instruct` via llama.cpp) is behind an OpenAI-compatible API.
- A separate **Tools VM** hosts Stirling PDF and Open WebUI, reached through the router at `/tools/*`.

## Why Nebius

- **Serverless AI Endpoints** remove the need to operate Kubernetes; endpoints scale and route automatically.
- **Managed PostgreSQL with pgvector** gives a production vector store without self-hosting.
- **Container Registry** lets me build images locally and push them for deployment.
- CPU presets keep the demo stack cheap enough to leave running during judging, while GPU endpoints can be added when larger models are needed.

## What is running right now

| Component | Status |
|-----------|--------|
| Router endpoint `<YOUR_ROUTER_IP>:8000` | **Running** |
| LLM endpoint (private) | **Running** |
| Crawl4AI microservice (private) | **Running** |
| Tools VM (Stirling PDF + Open WebUI) | **Running** |
| Managed PostgreSQL `nebius10-db` | **Running** |

A live `/pipeline/ask` call on `https://docs.nebius.com/llms.txt` currently returns a grounded answer about Nebius AI services in a few seconds.

## Try it

```bash
export ROUTER_IP=<YOUR_ROUTER_IP>:8000

curl -X POST http://${ROUTER_IP}/pipeline/ingest \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://docs.nebius.com/llms.txt","source":"nebius-llms"}'

curl -X POST http://${ROUTER_IP}/pipeline/ask \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"question":"What AI services does Nebius offer?","top_k":2}'
```

## Reproducibility

Everything needed to rebuild the stack is in the public repository:

- Dockerfiles for the router, Crawl4AI, and LLM images
- `docker-compose.yml` for local development
- Nebius deploy scripts under `nebius/`
- `supabase_schema.sql` for the pgvector schema
- `docs/RUNBOOK.md` with live endpoint IDs, IPs, and debug commands
- MIT license

Credentials are read from environment variables; no secrets are committed.

## Next steps

- Finish adapters for Langflow, Dify, Browser Use, Maxun, OpenHands, and Coolify so each tool can be reached from the router.
- Add a Nebius Serverless AI Job to batch-crawl and embed an entire site.
- Swap the CPU LLM endpoint for a GPU-backed vLLM endpoint once quota allows, enabling larger models and longer context.

If you are building with open-source AI tools, I hope this saves you from writing the same glue code over and over.

---

Project repo: `https://github.com/pyscalp/10in1-ai`
