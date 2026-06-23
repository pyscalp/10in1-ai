# Agent Task Masterlist — Nebius 10-in-1 AI Workbench
# 
# Agent dcode in tmux session `nebius101` should work through these tasks in order.
# Owner (ajat) wants agent to execute everything; assistant (Hermes) only monitors.
# If stuck >10 minutes or need credentials, ask the owner via the tmux session,
# but prefer self-contained fixes first.

## Context
- Repo: /home/ubuntu/nebius-10in1-ai-workbench
- Docs: docs/RUNBOOK.md, docs/DEPLOYMENT_PLAN.md
- Router public endpoint: <YOUR_ROUTER_IP>:8000
- LLM private endpoint: <llm-private-ip>:8000
- Managed Postgres: nebius10-db, running
- Credentials are local: .router_auth_token, .llm_auth_token, .db_pass

## Order of Work (Highest Priority First)

### 1. Finish Crawl4AI microservice deployment (IN PROGRESS)
- Complete Dockerfile.crawl4ai + requirements-crawl4ai.txt + src/crawl4ai_service if not done.
- Build image, push to container registry <YOUR_REGISTRY>.
- Deploy using nebius/deploy-crawl4ai.sh (private IP is fine; router will use it).
- Once deployed, update router env CRAWL4AI_URL and redeploy router if needed.
- Verify: ingest a JS-heavy URL and confirm crawl4ai path is used (not HTTP fallback).

### 2. Clean & shrink router image
- Remove Playwright/bloat from Dockerfile.router.
- Use multi-stage build to shrink image size below 1.5 GB.
- Rebuild as nebius10-router:slim-v4 and redeploy router.
- Run smoke test `/health` + `/pipeline/ingest` + `/pipeline/ask` after redeploy.

### 3. Deploy Stirling PDF microservice
- Use frooodle/s-pdf:latest image; deploy as separate endpoint (2vcpu-4gb or 4vcpu-16gb).
- Set STIRLING_PDF_URL in router env.
- Add /tools/pdf endpoint or use direct proxy.
- Verify with a test PDF conversion.

### 4. (Optional/Architecture) Open WebUI or one more tool
- Pick one of: Open WebUI, Maxun, Browser Use hook, or a simple Langflow/Dify stub.
- Deploy only if resource/time allows; otherwise update docs and mark as future work.

### 5. GPU vLLM endpoint
- When GPU quota/scheduling available, run nebius/deploy-vllm.sh with Qwen3-0.6B.
- Update router env NEBIUS_LLM_URL to GPU endpoint private IP.
- Benchmark latency vs CPU endpoint and record results.

### 6. Documentation & reproducibility
- Update README.md with: architecture diagram, quickstart, env setup, curl examples.
- Update docs/RUNBOOK.md with any new endpoint IPs, resource IDs, and fixes.
- Update docs/DEPLOYMENT_PLAN.md if scope changes.
- Add `make smoke-test` or similar script.
- Commit all changes to git (DO NOT commit credential files).

### 7. Final polish for Nebius submission
- Record or script a 60-second demo: ingest URL → ask question → show answer.
- Write a short BLOG.md or SUBMISSION.md explaining what was built and why it matters.
- Ensure `nebius ai endpoint list` shows all endpoints healthy.

## Rules
- Do NOT delete or restart working endpoints unless you first verify the replacement works.
- Keep credential files (.router_auth_token, .llm_auth_token, .db_pass) out of git.
- Prefer private Nebius endpoints between services; public only for router/user access.
- If a task is blocked by Nebius quota/GPU unavailability, skip it, document the blocker, and move on.
- Save progress in git commits every time a milestone is reached.

## When Done
Message in the session: "DONE — all tasks complete or documented blockers." Then stop.
