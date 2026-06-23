# Agent Execution Brief — Nebius 10-in-1 AI Workbench

## Goal
Lanjutkan proyek submission **Nebius Serverless AI Builders Challenge** dengan fokus: **verify → extend → document → optimize**. Kerjakan tasks di bawah secara berurutan. Laporkan progress di file ini dan/atau buat file baru di `docs/AGENT_LOG.md`.

## Status Saat Ini
Core stack sudah running:
- Router public: `<YOUR_ROUTER_IP>:8000`
- LLM private: `<llm-private-ip>:8000`
- Managed PostgreSQL pgvector: `nebius10-db`
- Container Registry: `<YOUR_REGISTRY>`

Credential lokal:
- `.router_auth_token`
- `.llm_auth_token`
- `.db_pass`

Semua sudah diatur di environment deploy sebelumnya. Jangan pernah menyebutkan isi credential di output.

---

## Task 1 — Live Smoke Test (WAJIB DULUAN)
Verifikasi endpoint beneran hidup dan RAG pipeline jalan.

1. Health check ke router:
   ```bash
   curl -s -H "Authorization: Bearer $(cat .router_auth_token)" \
     http://<YOUR_ROUTER_IP>:8000/health
   ```
2. Ingest URL:
   ```bash
   curl -s -X POST http://<YOUR_ROUTER_IP>:8000/pipeline/ingest \
     -H "Authorization: Bearer $(cat .router_auth_token)" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://docs.nebius.com/llms.txt","source":"nebius-llms"}'
   ```
3. Ask question:
   ```bash
   curl -s -X POST http://<YOUR_ROUTER_IP>:8000/pipeline/ask \
     -H "Authorization: Bearer $(cat .router_auth_token)" \
     -H "Content-Type: application/json" \
     -d '{"question":"What AI services does Nebius offer?","top_k":2}'
   ```
4. Catat hasil lengkap (status code, response JSON) di `docs/AGENT_LOG.md`.

Success criteria: `/health` return `{"status":"ok"}`, `ingest` return `chunks_stored > 0`, `ask` return `chunks_used > 0` dan jawaban relevan.

---

## Task 2 — Deploy Crawl4AI Microservice
Sekarang crawling masih HTTP fetch fallback. Deploy Crawl4AI sebagai microservice terpisah.

1. Buat `Dockerfile.crawl4ai` (install Playwright Chromium).
2. Buat `src/crawl4ai_service/main.py` — minimal endpoint `POST /crawl` menerima `{"url": ...}` dan return `{"markdown": ..., "ok": true/false}`.
3. Build image dan push ke registry:
   ```bash
   docker build -t <YOUR_REGISTRY>/nebius10-crawl4ai:v1 -f Dockerfile.crawl4ai .
   docker push <YOUR_REGISTRY>/nebius10-crawl4ai:v1
   ```
4. Deploy ke Nebius Serverless AI Endpoint CPU (preset 2vcpu-4gb atau 4vcpu-16gb).
5. Set env `CRAWL4AI_URL` di router endpoint dan redeploy router supaya pipeline pake Crawl4AI.
6. Test ulang `/pipeline/ingest` dengan URL yang sebelumnya fallback.

---

## Task 3 — Finalisasi README & Submission Materials
Buat repo siap dilihat juri.

1. Perbarui `README.md` dengan:
   - One-liner "10-in-1 AI Workbench on Nebius"
   - Arsitektur (pakai ASCII diagram atau link ke `docs/DEPLOYMENT_PLAN.md`)
   - Cara deploy cepat (clone → auth Nebius → deploy script)
   - Demo curl commands
   - Stack teknologi
2. Buat `docs/SUBMISSION.md` berisi:
   - Nama proyek
   - Deskripsi fitur
   - Why Nebius (pakai endpoint serverless, managed DB, registry)
   - Demo video outline / script
3. Update `.env.example` supaya lengkap dan aman (jangan expose credential asli).
4. Commit semua perubahan ke git dengan pesan deskriptif.

---

## Task 4 — Audit Biaya & Resource
Cegah boros kredit Nebius $5000.

1. Jalankan:
   ```bash
   nebius ai endpoint list --format json
   nebius managed postgresql cluster list --format json
   nebius container-registry registry list --format json
   ```
2. Buat ringkasan resource aktif, preset, dan perkiraan biaya per jam.
3. Identifikasi resource idle/yang bisa di-scale down.
4. Catat rekomendasi di `docs/AGENT_LOG.md`.

---

## Reporting Rules
- Setelah tiap task, tulis ringkasan hasil di `docs/AGENT_LOG.md`.
- Jika ada error/failure, tulis: gejala, penyebaban, fix yang dicoba, dan butuh bantuan apa.
- Jangan expose token/password/credential di log.
- Jika butuh intervensi manual (misal konfirmasi sebelum deploy GPU mahal), tulis pertanyaan di log dan hentikan task tersebut.

## Constraints
- Jangan ubah file credential lokal (`.router_auth_token`, `.llm_auth_token`, `.db_pass`).
- Jangan push credential ke git.
- Jangan membuat resource baru yang boros tanpa konfirmasi (terutama GPU > 1 instance).
- Jaga supaya router endpoint tetap running, jangan dihapus.
