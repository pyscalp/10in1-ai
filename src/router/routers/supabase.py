"""Supabase router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
from adapters.supabase_adapter import SupabaseAdapter

router = APIRouter()
settings = get_settings()

adapter = SupabaseAdapter(
    url=settings.supabase_url,
    key=settings.supabase_key,
    db_url=settings.supabase_db_url,
)


class StoreChunkRequest(BaseModel):
    source: str
    text: str
    embedding: list | None = None
    metadata: dict | None = {}


@router.get("/health")
async def health():
    return await adapter.health()


@router.post("/ensure-schema")
async def ensure_schema():
    return await adapter.ensure_schema()


@router.post("/chunks")
async def store_chunk(req: StoreChunkRequest):
    return await adapter.store_chunk(req.source, req.text, req.embedding, req.metadata)


@router.get("/chunks")
async def list_chunks(limit: int = 10):
    return await adapter.list_chunks(limit)
