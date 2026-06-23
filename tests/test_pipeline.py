"""Smoke tests for the end-to-end pipeline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "router"))

from pipeline import _chunk_text, ingest_url, ask_rag


def test_chunk_text_splits_properly():
    text = " ".join([f"word{i}" for i in range(20)])
    chunks = _chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_empty():
    assert _chunk_text("") == []
    assert _chunk_text("   ") == []


@pytest.mark.asyncio
async def test_ingest_url_handles_stub_crawl():
    """If crawl4ai returns a stub, ingest should report error at crawl step."""
    with patch("pipeline.crawl4ai_crawl", new=AsyncMock(return_value={
        "tool": "crawl4ai",
        "status": "stub",
        "message": "not installed",
        "url": "https://example.com",
    })):
        result = await ingest_url("https://example.com")
        assert result["status"] == "error"
        assert result["step"] == "crawl"


@pytest.mark.asyncio
async def test_ingest_url_successful_path():
    """Happy path: crawl returns text, chunks are embedded and stored."""
    fake_crawl = {
        "success": True,
        "markdown": "This is a test document. " * 50,
        "cleaned_text": None,
    }
    with patch("pipeline.crawl4ai_crawl", new=AsyncMock(return_value=fake_crawl)):
        with patch("pipeline.embedding_model") as mock_emb:
            mock_emb.encode.side_effect = lambda texts, **kwargs: [[0.1] * 384 for _ in texts]
            with patch("pipeline._get_supabase_adapter") as mock_adapter_factory:
                mock_adapter = AsyncMock()
                mock_adapter.store_chunk.return_value = {"status": "ok"}
                mock_adapter_factory.return_value = mock_adapter

                result = await ingest_url("https://example.com", chunk_size=20, overlap=5)

                assert result["status"] == "ok"
                assert result["url"] == "https://example.com"
                assert result["chunks_stored"] > 0
                assert result["chunks_total"] == result["chunks_stored"]
                assert result["errors"] == []


@pytest.mark.asyncio
async def test_ask_rag_no_db_url():
    """ask_rag should fail gracefully when vector search is not configured."""
    with patch("pipeline.embedding_model") as mock_emb:
        mock_emb.encode.return_value = [[0.1] * 384]
        with patch("pipeline._get_supabase_adapter") as mock_adapter_factory:
            mock_adapter = AsyncMock()
            mock_adapter.search_similar.side_effect = RuntimeError("SUPABASE_DB_URL is required for vector search")
            mock_adapter_factory.return_value = mock_adapter

            result = await ask_rag("What is this?")
            assert result["status"] == "error"
            assert result["step"] == "retrieve"
