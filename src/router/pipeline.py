"""End-to-end Workbench pipeline: crawl -> chunk -> embed -> store -> answer."""
import hashlib
import re
from typing import List

import httpx
from adapters.crawl4ai_adapter import crawl as crawl4ai_crawl
from adapters.supabase_adapter import SupabaseAdapter
from config import get_settings

settings = get_settings()


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Simple sliding-window chunking."""
    words = re.split(r"\s+", text.strip())
    if not words or words == [""]:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks


class EmbeddingModel:
    """Lazy-loading sentence-transformers embedding model."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed; run: pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: List[str]) -> List[List[float]]:
        model = self._load()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()


embedding_model = EmbeddingModel()


def _get_supabase_adapter() -> SupabaseAdapter:
    # Prefer the managed PostgreSQL DATABASE_URL if provided; fall back to Supabase direct URL.
    db_url = settings.database_url or settings.supabase_db_url
    return SupabaseAdapter(
        url=settings.supabase_url,
        key=settings.supabase_key,
        db_url=db_url,
    )


def _simple_html_to_text(html: str) -> str:
    """Very basic HTML tag stripping for the HTTP fallback."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def _fetch_url_text(url: str) -> str:
    """Lightweight HTTP fallback when crawl4ai/browser is unavailable."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0 WorkbenchBot"})
        response.raise_for_status()
        return _simple_html_to_text(response.text)


async def ingest_url(
    url: str,
    source: str | None = None,
    chunk_size: int = 512,
    overlap: int = 64,
) -> dict:
    """Crawl a URL, chunk it, embed it and store the chunks in Supabase pgvector."""
    crawl_result = await crawl4ai_crawl(url, markdown=True, bypass_cache=True)

    if crawl_result.get("status") == "stub":
        crawl_result["success"] = False

    if crawl_result.get("success"):
        text = crawl_result.get("markdown") or crawl_result.get("cleaned_text") or ""
    else:
        # Fallback to a plain HTTP fetch if crawl4ai failed (e.g. no browser).
        try:
            text = await _fetch_url_text(url)
            crawl_result["fallback"] = "http"
        except Exception as exc:
            return {
                "status": "error",
                "step": "crawl",
                "message": f"crawl4ai failed and HTTP fallback also failed: {exc}",
                "detail": crawl_result,
            }

    if not text.strip():
        return {
            "status": "error",
            "step": "extract",
            "message": "No text extracted from URL",
            "crawl_result": crawl_result,
        }

    chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return {
            "status": "error",
            "step": "chunk",
            "message": "Text could not be chunked",
        }

    try:
        embeddings = embedding_model.encode(chunks)
    except Exception as exc:
        return {
            "status": "error",
            "step": "embed",
            "message": str(exc),
        }

    adapter = _get_supabase_adapter()
    source_label = source or url
    stored = 0
    errors = []
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = hashlib.sha256(f"{source_label}:{idx}:{chunk_text[:80]}".encode()).hexdigest()
        try:
            await adapter.store_chunk(
                source=source_label,
                text=chunk_text,
                embedding=embedding,
                meta={
                    "chunk_index": idx,
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "chunk_id": chunk_id,
                    "url": url,
                },
            )
            stored += 1
        except Exception as exc:
            errors.append({"index": idx, "error": str(exc)})

    return {
        "status": "ok" if not errors else "partial",
        "source": source_label,
        "url": url,
        "chunks_total": len(chunks),
        "chunks_stored": stored,
        "errors": errors,
        "crawl_summary": {
            "success": crawl_result.get("success"),
            "status": crawl_result.get("status"),
        },
    }


async def ask_rag(
    question: str,
    top_k: int = 5,
    model: str | None = None,
) -> dict:
    """Retrieve relevant chunks and ask the Nebius LLM endpoint."""
    try:
        question_embedding = embedding_model.encode([question])[0]
    except Exception as exc:
        return {
            "status": "error",
            "step": "embed_question",
            "message": str(exc),
        }

    adapter = _get_supabase_adapter()
    try:
        chunks = await adapter.search_similar(question_embedding, limit=top_k)
    except Exception as exc:
        return {
            "status": "error",
            "step": "retrieve",
            "message": str(exc),
        }

    retrieval_meta = {
        "chunks_found": len(chunks),
        "top_k": top_k,
        "distances": [c.get("distance") for c in chunks],
        "sources": list({c.get("source") for c in chunks if c.get("source")}),
    }

    context = "\n\n---\n\n".join(
        f"[Source: {c.get('source', 'unknown')}]\n{c.get('text', '')}" for c in chunks
    )
    system_prompt = (
        "You are a helpful research assistant. Use only the provided context to answer. "
        "If the context does not contain the answer, say so."
    )
    context = context[:6000]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    try:
        from routers.llm import chat_completion
        from fastapi import HTTPException

        class _Request:
            def __init__(self, model, messages, temperature=0.3, max_tokens=1024):
                self.model = model
                self.messages = messages
                self.temperature = temperature
                self.max_tokens = max_tokens

        response = await chat_completion(
            _Request(
                model=model or settings.nebius_llm_model,
                messages=messages,
            )
        )
    except HTTPException as exc:
        return {
            "status": "error",
            "step": "llm",
            "detail": exc.detail,
            "code": exc.status_code,
        }
    except Exception as exc:
        return {
            "status": "error",
            "step": "llm",
            "message": str(exc),
        }

    return {
        "status": "ok",
        "question": question,
        "chunks_used": len(chunks),
        "sources": list({c.get("source") for c in chunks if c.get("source")}),
        "context": context,
        "answer": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "llm_response": response,
        "retrieval": retrieval_meta,
    }
