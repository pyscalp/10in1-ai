"""Supabase adapter: persistence, vector search and metadata."""
import json
from typing import List

from .base import DEFAULT_TIMEOUT


class SupabaseAdapter:
    def __init__(self, url: str, key: str, db_url: str | None = None):
        self.url = url
        self.key = key
        self.db_url = db_url
        self._client = None

    def client(self):
        if self._client is None:
            try:
                from supabase import create_client
            except ImportError as exc:
                raise RuntimeError(f"supabase python package not installed: {exc}")
            self._client = create_client(self.url, self.key)
        return self._client

    async def health(self) -> dict:
        try:
            self.client().table("chunks").select("id", count="exact").limit(1).execute()
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    async def ensure_schema(self) -> dict:
        """Create the chunks table + vector extension if using raw DB URL."""
        if not self.db_url:
            return {"status": "skipped", "message": "SUPABASE_DB_URL not set"}
        return {
            "status": "manual",
            "message": "Run the SQL from nebius/supabase_schema.sql in your Supabase SQL editor",
        }

    async def store_chunk(self, source: str, text: str, embedding: List[float] | None = None, meta: dict | None = None) -> dict:
        payload = {
            "source": source,
            "text": text,
            "metadata": json.dumps(meta or {}),
        }
        if embedding:
            payload["embedding"] = embedding

        # Prefer raw Postgres connection when available (local pgvector / Supabase direct connection).
        if self.db_url:
            import psycopg2

            vector_literal = "[" + ",".join(str(v) for v in embedding) + "]" if embedding else None
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO chunks (source, text, metadata, embedding)
                        VALUES (%s, %s, %s::jsonb, %s::vector)
                        RETURNING id
                        """,
                        (source, text, payload["metadata"], vector_literal),
                    )
                    row = cur.fetchone()
                    conn.commit()
            return {"status": "ok", "id": row[0] if row else None}

        result = self.client().table("chunks").insert(payload).execute()
        return {"status": "ok", "data": result.data}

    async def list_chunks(self, limit: int = 10) -> dict:
        result = self.client().table("chunks").select("*").limit(limit).execute()
        return {"status": "ok", "data": result.data}

    async def search_similar(self, embedding: List[float], limit: int = 5) -> List[dict]:
        """Vector similarity search using pgvector via raw SQL."""
        if not self.db_url:
            raise RuntimeError("SUPABASE_DB_URL is required for vector search")
        import psycopg2
        from psycopg2.extras import RealDictCursor

        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, source, text, metadata, embedding <=> %s::vector AS distance
                    FROM chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vector_literal, vector_literal, limit),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]
