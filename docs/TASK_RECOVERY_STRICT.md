# Task: Recovery + Tools Bundle — Strict Autonomy

Agent in tmux session `nebius101` must recover the workbench router and finish the Tools Bundle deployment. This is the **ONLY** task document to follow. Ignore older `AGENT_TASKS.md` / `TASK_TOOLS_BUNDLE.md` ordering unless they do not conflict with this file.

## ⚠️ HARD GUARDRAILS (NON-NEGOTIABLE)

1. **DO NOT touch `[VM_NAME]` ([INSTANCE_ID]), `[VM_NAME]`, `[VM_NAME]`, or any other VM/instance/endpoint that is NOT named with the `nebius10-*` prefix.**  
   Exception: you may **release the public IPv4 allocation currently attached to `[VM_NAME]`** because that VM is already STOPPED and its IP is needed for the router.

2. **Allowed `nebius10-*` resources only:**  
   `nebius10-router`, `nebius10-llm`, `nebius10-crawl4ai`, `nebius10-tools`, `nebius10-db` (managed DB), `nebius10-registry`.  
   You may create, update, delete, and redeploy **ONLY** these. If you need to delete `nebius10-router` to redeploy it, you must first capture its current public IP and env vars.

3. **Every Nebius CLI command you execute must be logged immediately** in `docs/AGENT_LOG.md` under a new section `# Task 5 — Recovery & Tools Bundle (Strict)` with command + outcome.

4. **No credentials in git.** Keep `.router_auth_token`, `.llm_auth_token`, `.db_pass` out of commits.

5. **If blocked for >10 minutes or you are uncertain about deleting a resource, STOP and ask owner.** Do not guess.

---

## Current State (verified)

- `[VM_NAME]` → RUNNING → **DO NOT TOUCH**
- `nebius10-router` endpoint → **MISSING** (was deleted by the previous run). Public access is down.
- `nebius10-llm` → RUNNING, private `<llm-private-ip>:8000`
- `nebius10-crawl4ai` → RUNNING, private `<crawl4ai-private-ip>:8000`
- `nebius10-tools` VM → RUNNING, private `<tools-private-ip>` (created by previous run; Docker/services status unknown)
- `[VM_NAME]` → STOPPED, but its public IP `<VM_PUBLIC_IP>` is still allocated.
- Container registry has router images including `nebius10-router:slim-v6` (pushed by previous run).

---

## Step 1 — Audit & free a public IP

1. List all compute instances and AI endpoints. Log to `docs/AGENT_LOG.md`.
2. List public IPv4 allocations. Confirm the one attached to `[VM_NAME]` is `<VM_PUBLIC_IP>`.
3. Release that allocation:
   ```bash
   nebius --profile nebius101 vpc allocation delete --id <ALLOCATION_ID> --yes
   ```
4. Confirm quota is now at most 2/3 used.

---

## Step 2 — Redeploy `nebius10-router`

1. Inspect current `nebius/deploy-router.sh`, `src/router/config.py`, and `src/router/main.py`. Use existing router image `<YOUR_REGISTRY>/nebius10-router:slim-v6` unless it fails to start.
2. Ensure env vars include:
   ```bash
   NEBIUS_LLM_URL=http://<llm-private-ip>:8000/v1/chat/completions
   CRAWL4AI_URL=http://<crawl4ai-private-ip>:8000
   DATABASE_URL=postgresql://workbench:<DB_PASS>@<DB_HOST>:5432/workbench
   ROUTER_AUTH_TOKEN=<read from .router_auth_token>
   TOOLS_STIRLING_PDF_URL=http://<tools-private-ip>:8080
   TOOLS_OPEN_WEBUI_URL=http://<tools-private-ip>:3000
   TOOLS_BROWSER_USE_URL=http://<tools-private-ip>:8001
   ```
3. Run `nebius/deploy-router.sh` to recreate the endpoint. It should use the freed public IP.
4. Wait for endpoint `RUNNING`, capture new public IP, and update `docs/RUNBOOK.md`.
5. Run core smoke tests from outside (your local shell or another VM):
   ```bash
   curl -s http://<NEW_ROUTER_IP>:8000/health
   curl -s -X POST http://<NEW_ROUTER_IP>:8000/pipeline/ingest -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"url":"https://docs.nebius.com/llms.txt","source":"nebius-llms"}'
   curl -s -X POST http://<NEW_ROUTER_IP>:8000/pipeline/ask -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"question":"What AI services does Nebius offer?","top_k":2}'
   ```
6. Log all results to `docs/AGENT_LOG.md`.

---

## Step 3 — Verify / finish `nebius10-tools` VM setup

1. SSH into `nebius10-tools` via private IP using `nebius compute instance ssh` or an SSH key you configured.  
   **Do NOT create a new tools VM unless this one is confirmed broken beyond repair.**
2. Check if Docker + Docker Compose are installed and if `tools/docker-compose.tools.yml` exists in the VM.
3. If missing, copy `tools/` from repo to the VM.
4. Run `tools/start-tools.sh` and wait for containers healthy:
   - Stirling PDF on `127.0.0.1:8080`
   - Open WebUI on `127.0.0.1:3000`
   - Browser Use on `127.0.0.1:8001` (optional; remove from compose or from router env if it fails)
5. From inside the VM, test:
   ```bash
   curl -s http://127.0.0.1:8080/api/v1/info
   curl -s http://127.0.0.1:3000/api/config
   ```
6. If tools VM is too small (cpu-d3 / 4vcpu-16gb or cpu-e2 / 2vcpu-4gb) and Open WebUI OOMs, document it as a blocker and STOP — do not resize other project VMs.

---

## Step 4 — Wire router to tools (after Step 2 & 3 pass)

1. The router env should already point to `<tools-private-ip>`. If the tools VM IP changed, update env and redeploy.
2. Ensure routes exist in `src/router/main.py` (or `src/router/routers/tools_bundle.py`) for:
   - `GET /tools/pdf/status` → proxy to Stirling PDF `/api/v1/info`
   - `GET /tools/chatui/status` → proxy to Open WebUI `/api/config` or health
   - `POST /tools/pdf/convert` → proxy to Stirling PDF `/api/v1/convert`
3. Test from outside:
   ```bash
   curl -s http://<NEW_ROUTER_IP>:8000/tools/pdf/status -H "Authorization: Bearer <TOKEN>"
   ```

---

## Step 5 — Commit & docs

1. Update `docs/AGENT_LOG.md` with a summary table.
2. Update `docs/RUNBOOK.md` with new router public IP, tools VM IP, and `/tools/*` routes.
3. Update `README.md` section "Optional Tools" if needed.
4. Commit everything except credential files:
   ```bash
   git add docs/AGENT_LOG.md docs/RUNBOOK.md README.md nebius/src router tools Dockerfile.*
   git commit -m "fix: redeploy router after recovery, wire tools bundle, strict guardrails"
   ```

---

## Success Criteria

- [ ] `[VM_NAME]` is still RUNNING (never touched).
- [ ] `[OLD_VM_NAME]` public IP released and router has a public IP.
- [ ] `nebius10-router` RUNNING and `/health`, `/pipeline/ingest`, `/pipeline/ask` all PASS.
- [ ] `nebius10-tools` has Stirling PDF + Open WebUI reachable on private IP.
- [ ] At least `/tools/pdf/status` and `/tools/chatui/status` respond through the router.
- [ ] All changes documented and committed.

---

## When Blocked

STOP and ask owner if:
- Router redeploy fails repeatedly.
- Tools VM cannot fit Stirling PDF + Open WebUI.
- You need to delete/update any resource not prefixed `nebius10-`.
- You need credentials you cannot read from existing env files.
