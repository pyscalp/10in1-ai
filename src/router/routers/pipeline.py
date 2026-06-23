"""Pipeline router: end-to-end ingest + RAG ask."""
from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter

from pipeline import ingest_url, ask_rag

router = APIRouter()


class IngestRequest(BaseModel):
    url: HttpUrl
    source: str | None = None
    chunk_size: int = 512
    overlap: int = 64


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    model: str | None = None


@router.post("/ingest")
async def ingest(req: IngestRequest):
    return await ingest_url(
        url=str(req.url),
        source=req.source,
        chunk_size=req.chunk_size,
        overlap=req.overlap,
    )


@router.post("/ask")
async def ask(req: AskRequest):
    return await ask_rag(
        question=req.question,
        top_k=req.top_k,
        model=req.model,
    )
