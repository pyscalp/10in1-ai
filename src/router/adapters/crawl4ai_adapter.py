"""Crawl4AI adapter: URL -> markdown / cleaned HTML.

If CRAWL4AI_URL is set, the adapter calls the remote Crawl4AI microservice.
Otherwise it tries to import crawl4ai locally (legacy / local mode).
"""

import os

import httpx


async def _call_remote_crawl4ai(url: str, service_url: str) -> dict:
    """Call the Crawl4AI microservice."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{service_url.rstrip('/')}/crawl",
            json={"url": url},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "url": url,
            "success": data.get("ok", False),
            "markdown": data.get("markdown"),
            "cleaned_text": None,
            "metadata": data.get("metadata"),
            "tool": "crawl4ai_service",
        }


async def crawl(url: str, markdown: bool = True, bypass_cache: bool = True) -> dict:
    """Crawl a single URL and return markdown or cleaned text."""
    service_url = os.getenv("CRAWL4AI_URL", "")
    if service_url:
        try:
            return await _call_remote_crawl4ai(url, service_url)
        except Exception as exc:
            return {
                "url": url,
                "success": False,
                "tool": "crawl4ai_service",
                "status": "error",
                "message": f"Remote Crawl4AI service failed: {exc}",
            }

    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError as exc:
        return {
            "tool": "crawl4ai",
            "status": "stub",
            "message": f"crawl4ai package not installed: {exc}",
            "url": url,
        }

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, bypass_cache=bypass_cache)
            return {
                "url": url,
                "success": result.success,
                "markdown": result.markdown if markdown else None,
                "cleaned_text": result.cleaned_text if not markdown else None,
                "metadata": result.metadata,
            }
    except Exception as exc:
        return {
            "url": url,
            "success": False,
            "tool": "crawl4ai",
            "status": "error",
            "message": str(exc),
        }
