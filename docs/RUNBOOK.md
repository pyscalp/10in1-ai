# Nebius 10-in-1 AI Workbench — Runbook & Deployment Reference

Dokumen ini adalah catatan lengkap hasil deployment nyata untuk **Nebius Serverless AI Builders Challenge**. Semua nama resource, ID, endpoint, credential path, dan perintah pemanggilan tercatat di sini agar mudah dipelihara, direproduksi, atau didebug.

> **Status:** core stack sudah deploy dan RAG pipeline berjalan end-to-end. Tools bundle (`/tools/pdf/status`, `/tools/chatui/status`) aktif.  
> **Terakhir diupdate:** 23 Jun 2026.

---

## 1. Ringkasan Arsitektur yang Sudah Jalan

```text
                         ┌─────────────────────────────────────┐
                         │  User / curl / Open WebUI / demo    │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────────┐
                    │  Workbench Router                         │
                    │  Nebius Serverless AI Endpoint (CPU)      │
                    │  /pipeline/ingest  +  /pipeline/ask       │
                    │  /tools/pdf/status + /tools/chatui/status │
                    │  public: <YOUR_ROUTER_IP>:8000               │
                    └──────────────┬────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   ┌─────────────┐        ┌─────────────────┐       ┌─────────────────────┐
   │ Crawl4AI    │        │ Nebius LLM      │       │ Tools VM            │
   │ microservice│        │ Serverless AI   │       │ nebius10-tools      │
   │ private     │        │ Endpoint (CPU)  │       │ <tools-private-ip>         │
   │ <crawl4ai-private-ip> │        │ private <llm-private-ip>:8000│  ├─ Stirling PDF     │
   └─────────────┘        └─────────────────┘       │  ├─ Open WebUI      │
                                                    │  └─ Browser Use     │
                                                    └─────────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────────────────┐
                    │  Nebius Managed PostgreSQL (pgvector)     │
                    │  cluster: nebius10-db                     │
                    │  db: workbench  |  user: workbench        │
                    └───────────────────────────────────────────┘
```

### Komponen aktif

| # | Komponen | Platform | Status |
|---|----------|----------|--------|
| 1 | Workbench Router | Nebius Serverless AI Endpoint CPU `cpu-e2` / `2vcpu-8gb` | **RUNNING** |
| 2 | LLM inference | Nebius Serverless AI Endpoint CPU `cpu-d3` / `4vcpu-16gb` | **RUNNING** |
| 3 | Crawl4AI microservice | Nebius Serverless AI Endpoint CPU `cpu-d3` / `4vcpu-16gb` | **RUNNING** |
| 4 | Tools VM | Nebius Compute Instance `cpu-d3` / `4vcpu-16gb` | **RUNNING** |
| 5 | Managed PostgreSQL | Nebius Managed PostgreSQL | **RUNNING** |
| 6 | Container Registry | Nebius Container Registry | **READY** |

Tools yang sudah aktif di Tools VM: **Stirling PDF**, **Open WebUI**, **Browser Use**, **Langflow**. Browser Use dan Langflow tersedia via compose profile (`--profile browser-use` / `--profile langflow`).

---

## 2. Resource Nebius yang Sudah Dibuat

### 2.1 Container Registry

| Field | Value |
|-------|-------|
| Name | `nebius10-registry` |
| ID | `[REGISTRY_ID]` |
| Endpoint | `<YOUR_REGISTRY>` |

Images yang sudah dipush:

| Image | Tag | Digunakan oleh |
|-------|-----|----------------|
| `<YOUR_REGISTRY>/nebius10-llm` | `cpu` | LLM endpoint |
| `<YOUR_REGISTRY>/nebius10-crawl4ai` | `v1` | Crawl4AI endpoint |
| `<YOUR_REGISTRY>/nebius10-router` | `slim-v16` | Router endpoint (aktif) |
| `<YOUR_REGISTRY>/nebius10-browser-use` | `v1` | Browser Use microservice |

### 2.2 Managed PostgreSQL

| Field | Value |
|-------|-------|
| Name | `nebius10-db` |
| ID | `[DB_CLUSTER_ID]` |
| Status | `PHASE_RUNNING` |
| Database | `workbench` |
| User | `workbench` |
| Host (private-rw) | `<YOUR_DB_HOST>` |
| Public access | **disabled** |
| Port | `5432` |
| SSL mode | `require` |

Schema yang sudah diapply: `nebius/supabase_schema.sql`

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_source_idx ON chunks(source);
```

> **Catatan penting:** index awal pakai `ivfflat (embedding vector_cosine_ops)` tapi query pakai operator `<=>` (L2 distance), yang menyebabkan retrieval mengembalikan 0 rows. Fix: ganti ke `hnsw (embedding vector_cosine_ops)`.

### 2.3 LLM Endpoint

| Field | Value |
|-------|-------|
| Name | `nebius10-llm` |
| ID | `[ENDPOINT_ID]` |
| Status | `RUNNING` |
| Platform | `cpu-d3` |
| Preset | `4vcpu-16gb` |
| Image | `<YOUR_REGISTRY>/nebius10-llm:cpu` |
| Private endpoint | `<llm-private-ip>:8000` |
| Public endpoint | *(none — private only)* |
| Container port | `8000` |
| Auth | Nebius endpoint token + `LLM_API_TOKEN` |
| Model file | `/models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` |
| Runtime | `llama-cpp-python[server]` (OpenAI-compatible) |
| Context length | ~4096 tokens |

Cara build image LLM:

```bash
bash nebius/build-llm-cpu.sh
```

Cara deploy LLM endpoint:

```bash
export LLM_API_TOKEN=$(openssl rand -hex 32)
bash nebius/deploy-llm-cpu.sh
```

### 2.4 Crawl4AI Endpoint

| Field | Value |
|-------|-------|
| Name | `nebius10-crawl4ai` |
| ID | `[ENDPOINT_ID]` |
| Status | `RUNNING` |
| Platform | `cpu-d3` |
| Preset | `4vcpu-16gb` |
| Image | `<YOUR_REGISTRY>/nebius10-crawl4ai:v1` |
| Private endpoint | `<crawl4ai-private-ip>:8000` |
| Public endpoint | *(none — private only)* |
| Container port | `8000` |

### 2.5 Tools VM

| Field | Value |
|-------|-------|
| Name | `nebius10-tools` |
| ID | `[INSTANCE_ID]` |
| Status | `RUNNING` |
| Preset | `4vcpu-16gb` |
| Private IP | `<tools-private-ip>` |
| Stirling PDF | `http://<tools-private-ip>:8080` |
| Open WebUI | `http://<tools-private-ip>:3000` |
| Browser Use | tersedia via compose profile |

### 2.6 Router Endpoint

| Field | Value |
|-------|-------|
| Name | `nebius10-router` |
| ID | `[ENDPOINT_ID]` |
| Status | `RUNNING` |
| Platform | `cpu-e2` |
| Preset | `2vcpu-8gb` |
| Image | `<YOUR_REGISTRY>/nebius10-router:slim-v16` |
| Public endpoint | `<YOUR_ROUTER_IP>:8000` |
| Private endpoint | `<ROUTER_PRIVATE_IP>:8000` |
| Container port | `8000` |
| Auth | Bearer token (`ROUTER_AUTH_TOKEN`) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |

Cara build & push router image:

```bash
docker build -t <YOUR_REGISTRY>/nebius10-router:slim-v16 -f Dockerfile.router .
docker push <YOUR_REGISTRY>/nebius10-router:slim-v16
```

Cara deploy router endpoint:

```bash
export ROUTER_AUTH_TOKEN=$(cat .router_auth_token)
export NEBIUS_LLM_URL="http://<llm-private-ip>:8000/v1"
export NEBIUS_LLM_MODEL="/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
export NEBIUS_LLM_TOKEN=$(cat .llm_auth_token)
export CRAWL4AI_URL="http://<crawl4ai-private-ip>:8000"
export DATABASE_URL="postgresql://workbench:<password>@<YOUR_DB_HOST>:5432/workbench"
export TOOLS_STIRLING_PDF_URL="http://<TOOLS_VM_IP>:8080"
export TOOLS_OPEN_WEBUI_URL="http://<TOOLS_VM_IP>:3000"
export TOOLS_BROWSER_USE_URL="http://<TOOLS_VM_IP>:8001"
export TOOLS_LANGFLOW_URL="http://<TOOLS_VM_IP>:7860"

bash nebius/deploy-router.sh \
  <YOUR_REGISTRY>/nebius10-router:slim-v16
```

---

## 3. File Credential Lokal (tidak di-commit)

| File | Isi | Digunakan saat |
|------|-----|----------------|
| `.router_auth_token` | Bearer token untuk router endpoint | semua curl ke router |
| `.llm_auth_token` | Token auth ke LLM endpoint | deploy router, direct LLM call |
| `.db_pass` | Password user `workbench` PostgreSQL | deploy, debug SQL |

Pastikan ketiga file ini ada di `.gitignore` dan tidak pernah di-push.

---

## 4. Environment Variables Router Endpoint

Berikut env vars yang aktif di endpoint `nebius10-router`:

```bash
APP_ENV=production
LOG_LEVEL=info
ROUTER_AUTH_TOKEN=<isi .router_auth_token>
NEBIUS_LLM_URL=http://<llm-private-ip>:8000/v1
NEBIUS_LLM_MODEL=/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
NEBIUS_LLM_TOKEN=<isi .llm_auth_token>
CRAWL4AI_URL=http://<crawl4ai-private-ip>:8000
DATABASE_URL=postgresql://workbench:<password>@<YOUR_DB_HOST>:5432/workbench
TOOLS_STIRLING_PDF_URL=http://<TOOLS_VM_IP>:8080
TOOLS_OPEN_WEBUI_URL=http://<TOOLS_VM_IP>:3000
TOOLS_BROWSER_USE_URL=http://<TOOLS_VM_IP>:8001
TOOLS_LANGFLOW_URL=http://<TOOLS_VM_IP>:7860
```

Tool URLs yang sudah aktif: Stirling PDF, Open WebUI, Browser Use, Langflow. Browser Use dan Langflow tersedia via compose profile.

---

## 5. Cara Memanggil Endpoint

### 5.1 Health check

```bash
export ROUTER_IP="<YOUR_ROUTER_IP>:8000"
export ROUTER_TOKEN=$(cat .router_auth_token)

curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/health"
```

Response:

```json
{"status":"ok"}
```

### 5.2 Ingest URL ke vector DB

```bash
curl -s -X POST "http://${ROUTER_IP}/pipeline/ingest" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.nebius.com/llms.txt",
    "source": "nebius-llms"
  }'
```

Response contoh:

```json
{
  "status": "ok",
  "source": "nebius-llms",
  "url": "https://docs.nebius.com/llms.txt",
  "chunks_total": 9,
  "chunks_stored": 9,
  "errors": [],
  "crawl_summary": {
    "success": true,
    "status": null
  }
}
```

> `crawl_summary.success: true` karena router sekarang memanggil Crawl4AI microservice private.

### 5.3 Ask / RAG

```bash
curl -s -X POST "http://${ROUTER_IP}/pipeline/ask" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What AI services does Nebius offer?",
    "top_k": 2
  }'
```

Response contoh:

```json
{
  "status": "ok",
  "question": "What AI services does Nebius offer?",
  "chunks_used": 2,
  "sources": ["nebius-docs"],
  "context": "[Source: nebius-docs]\n...",
  "answer": "Nebius offers Serverless AI Endpoints...",
  "llm_response": { ... },
  "retrieval": {
    "chunks_found": 2,
    "top_k": 2,
    "distances": [0.2243, 0.6102],
    "sources": ["nebius-docs"]
  }
}
```

### 5.4 Direct LLM call (tanpa RAG)

```bash
export LLM_TOKEN=$(cat .llm_auth_token)

curl -s -X POST "http://<llm-private-ip>:8000/v1/chat/completions" \
  -H "Authorization: Bearer ${LLM_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    "messages": [{"role":"user","content":"Hello"}],
    "temperature": 0.3,
    "max_tokens": 256
  }'
```

> Hanya bisa dipanggil dari dalam subnet Nebius (misalnya via `nebius ai endpoint ssh`) karena LLM endpoint private.

---

## 6. Known Issues & Fixes

### 6.1 Retrieval mengembalikan 0 chunks (`chunks_used: 0`)

- **Gejala:** `/pipeline/ask` status ok tapi `chunks_used: 0`, jawaban LLM halusinasi.
- **Penyebab:** index `ivfflat (embedding vector_cosine_ops)` + query `<=>` (L2) tidak kompatibel.
- **Fix:** drop index lama, buat `hnsw (embedding vector_cosine_ops)`.

```sql
DROP INDEX IF EXISTS chunks_embedding_idx;
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
ON chunks USING hnsw (embedding vector_cosine_ops);
```

### 6.2 Context length exceeded

- **Gejala:** `ask` error 400: `context_length_exceeded`.
- **Penyebab:** model Qwen2.5-0.5B context limit ~4096 token; `top_k` besar + chunk panjang melebihi batas.
- **Fix:** gunakan `top_k: 1` atau `top_k: 2`, atau turunkan `chunk_size` saat ingest.

### 6.3 Router image cache di Nebius

- **Gejala:** redeploy tapi kode lama masih berjalan.
- **Penyebab:** Nebius cache image layer.
- **Fix:** gunakan tag baru setiap rebuild (`slim-v2`, `slim-v3`, dst) dan update deploy script.

### 6.4 Public IP quota penuh

- **Gejala:** deploy public endpoint gagal karena quota public IP habis.
- **Fix:** detach public IP dari instance/endpoint yang tidak dipakai via console Nebius.

---

## 7. Perintah Debug Berguna

### Cek status endpoint

```bash
nebius ai endpoint list --format json
nebius ai endpoint get [ENDPOINT_ID] --format json
nebius ai endpoint get [ENDPOINT_ID] --format json
```

### Stream log router

```bash
nebius ai endpoint logs --follow [ENDPOINT_ID]
```

### SSH ke endpoint

```bash
nebius ai endpoint ssh [ENDPOINT_ID]
```

### Cek isi PostgreSQL lokal

```bash
psql "postgresql://workbench:<password>@<YOUR_DB_HOST>:5432/workbench?sslmode=require" \
  -c "SELECT id, source, vector_dims(embedding), text FROM chunks LIMIT 5;"
```

---

## 8. Next Steps / Future Work

1. **GPU vLLM endpoint** — coba ulang deploy GPU (`deploy-vllm.sh`) begitu GPU quota/scheduling tersedia, untuk model yang lebih besar dan context lebih panjang.
2. **Crawl4AI microservice** — deploy sebagai endpoint terpisah dengan Playwright Chromium, lalu set `CRAWL4AI_URL` di router.
3. **Stirling PDF microservice** — deploy `frooodle/s-pdf:latest` dan set `STIRLING_PDF_URL`.
4. **Open WebUI** — ✅ deploy di Tools VM, terhubung ke router via OpenAI-compatible `/llm/v1`.
5. **Langflow / Dify** — ✅ Langflow deploy di Tools VM, adapter router aktif. Dify masih future work.
6. **Browser Use / Maxun / OpenHands / Coolify** — tetap optional, dokumentasikan sebagai extension.
7. **Demo video & blog** — rekam demo end-to-end dan perbarui `blog/BLOG.md`.
8. **CI/CD** — tambahkan GitHub Actions untuk build & push image otomatis.

---

## 9. Referensi File

| File | Fungsi |
|------|--------|
| `Dockerfile.router` | Image router (FastAPI + embedding + psycopg2) |
| `Dockerfile.llm-cpu` | Image LLM CPU (`llama-cpp-python` + GGUF) |
| `nebius/deploy-router.sh` | Deploy router endpoint |
| `nebius/deploy-llm-cpu.sh` | Deploy LLM CPU endpoint |
| `nebius/deploy-vllm.sh` | Deploy LLM GPU endpoint (vLLM) |
| `nebius/supabase_schema.sql` | Schema pgvector |
| `src/router/pipeline.py` | Logika ingest + RAG ask |
| `src/router/adapters/supabase_adapter.py` | Store & vector search PostgreSQL |
| `src/router/routers/pipeline.py` | Route `/pipeline/ingest` & `/pipeline/ask` |
| `src/router/config.py` | Konfigurasi env var |
| `.env.example` | Template env lokal |
| `.router_auth_token` | Token router (lokal, jangan di-commit) |
| `.llm_auth_token` | Token LLM (lokal, jangan di-commit) |
| `.db_pass` | Password DB (lokal, jangan di-commit) |
