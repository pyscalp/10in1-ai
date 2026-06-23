"""Crawl4AI router."""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

import adapters.crawl4ai_adapter as crawl4ai

router = APIRouter()


class CrawlRequest(BaseModel):
    url: str
    markdown: bool = True
    bypass_cache: bool = True


@router.post("/")
async def crawl_page(req: CrawlRequest):
    try:
        return await crawl4ai.crawl(req.url, req.markdown, req.bypass_cache)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
