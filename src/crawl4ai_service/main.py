"""Crawl4AI microservice: single endpoint to crawl a URL and return markdown."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl


class CrawlRequest(BaseModel):
    url: HttpUrl
    markdown: bool = True
    bypass_cache: bool = True


class CrawlResponse(BaseModel):
    url: str
    ok: bool
    markdown: str | None = None
    cleaned_text: str | None = None
    metadata: dict | None = None
    error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the browser installation check on startup.
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            _ = p.chromium
    except Exception:
        pass
    yield


app = FastAPI(
    title="Crawl4AI Microservice",
    description="Browser-based crawling for the Nebius 10-in-1 AI Workbench.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest):
    url = str(req.url)
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"crawl4ai not installed: {exc}")

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, bypass_cache=req.bypass_cache)
            return CrawlResponse(
                url=url,
                ok=result.success,
                markdown=result.markdown if req.markdown else None,
                cleaned_text=result.cleaned_text if not req.markdown else None,
                metadata=result.metadata,
            )
    except Exception as exc:
        return CrawlResponse(url=url, ok=False, error=str(exc))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
