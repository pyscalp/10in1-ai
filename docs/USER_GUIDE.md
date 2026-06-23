# Nebius 10-in-1 AI Workbench — User Guide

Panduan praktis buat user yang mau pakai workbench. Semua endpoint diakses via **satu router publik**; backend (LLM, Crawl4AI, Tools VM, DB) komunikasi via private IP.

> **Router publik aktif:** `http://<YOUR_ROUTER_IP>:8000`  
> **Auth:** Bearer token (simpan di `.router_auth_token`, jangan di-commit)

---

## 1. Setup cepat

```bash
export ROUTER_IP="<YOUR_ROUTER_IP>:8000"
export ROUTER_TOKEN=$(cat .router_auth_token)
```

Semua curl di bawah pakai dua variabel di atas.

---

## 2. Health check

```bash
curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/health"
```

Response:
```json
{"status":"ok"}
```

---

## 3. RAG Pipeline

### 3.1 Ingest URL ke knowledge base

```bash
curl -s -X POST "http://${ROUTER_IP}/pipeline/ingest" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.nebius.com/llms.txt",
    "source": "nebius-llms"
  }'
```

Response:
```json
{
  "status": "ok",
  "source": "nebius-llms",
  "url": "https://docs.nebius.com/llms.txt",
  "chunks_total": 9,
  "chunks_stored": 9,
  "errors": [],
  "crawl_summary": {"success": true, "status": null}
}
```

### 3.2 Ask / tanya pertanyaan

```bash
curl -s -X POST "http://${ROUTER_IP}/pipeline/ask" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What AI services does Nebius offer?",
    "top_k": 2
  }'
```

Response:
```json
{
  "status": "ok",
  "question": "What AI services does Nebius offer?",
  "chunks_used": 2,
  "sources": ["nebius-docs", "nebius-llms"],
  "context": "...",
  "answer": "..."
}
```

---

## 4. Tools Bundle

### 4.1 Stirling PDF — status

```bash
curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/tools/pdf/status"
```

Response:
```json
{"groups":["liveness","readiness"],"status":"UP"}
```

### 4.2 Stirling PDF — upload & extract text

```bash
curl -s -X POST "http://${ROUTER_IP}/tools/pdf/upload" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -F "file=@/path/to/document.pdf"
```

Response:
```json
{
  "tool": "stirling-pdf",
  "status": "ok",
  "filename": "document.pdf",
  "text": "... extracted text ..."
}
```

### 4.3 Open WebUI — status

```bash
curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/tools/chatui/status"
```

Response:
```json
{"onboarding":true,"status":true,"name":"Open WebUI","version":"0.9.6",...}
```

### 4.4 Browser Use — navigasi halaman web

```bash
curl -s -X POST "http://${ROUTER_IP}/tools/browser-use/" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Extract title and body text",
    "url": "https://example.com"
  }'
```

Response:
```json
{
  "title": "Example Domain",
  "body_text": "This domain is for use in illustrative examples..."
}
```

### 4.5 Langflow — health & run flow

**Health:**
```bash
curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/langflow/health"
```

Response:
```json
{"status":"ok"}
```

**Run flow (ganti `{flow_id}` dengan ID flow yang sudah dibuat di Langflow):**
```bash
curl -s -X POST "http://${ROUTER_IP}/langflow/run/my-flow-id" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "my-flow-id",
    "payload": {"input": "hello"}
  }'
```

### 4.6 OpenAI-compatible chat completions

Router bisa dipakai sebagai backend OpenAI-compatible (misalnya untuk Open WebUI):

```bash
curl -s -X POST "http://${ROUTER_IP}/llm/v1/chat/completions" \
  -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

List models:
```bash
curl -s -H "Authorization: Bearer ${ROUTER_TOKEN}" \
  "http://${ROUTER_IP}/llm/v1/models"
```

---

## 5. Error codes

| HTTP | Arti | Solusi |
|------|------|--------|
| `401` | Token salah atau hilang | Cek `.router_auth_token` |
| `502` | Backend nggak reachable | Cek status service di `/health` atau `/tools/*/status` |
| `503` | Tool URL belum dikonfigurasi | Cek env vars router |

---

## 6. Tips

- `source` di `/pipeline/ingest` bebas, tapi konsisten biar gampang difilter.
- `top_k` di `/pipeline/ask` default bisa 2–5; naikin kalau jawaban kurang lengkap.
- PDF upload maksimal tergantung timeout Stirling PDF (default 60 detik).
