"""Lightweight observability helpers for the Workbench Router."""
import logging
import sys
from datetime import datetime, timezone

import httpx

from config import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Configure structured JSON-ish logging for production."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(level=level, stream=sys.stdout, format=fmt)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


async def _check_http(base_url: str, path: str = "/", timeout: float = 5.0) -> dict:
    if not base_url:
        return {"status": "not_configured"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{base_url.rstrip('/')}/{path.lstrip('/')}")
            response.raise_for_status()
            return {"status": "ok", "http_status": response.status_code}
        except httpx.HTTPStatusError as exc:
            return {"status": "degraded", "http_status": exc.response.status_code}
        except httpx.RequestError as exc:
            return {"status": "down", "error": str(exc)}


async def dependency_health() -> dict:
    """Return health snapshot of all configured dependencies."""
    deps = {
        "llm": await _check_http(settings.nebius_llm_url, "/models"),
        "crawl4ai": await _check_http(settings.crawl4ai_url, "/health"),
        "database": {"status": "ok" if settings.database_url else "not_configured"},
        "tools_stirling_pdf": await _check_http(settings.tools_stirling_pdf_url, "/actuator/health"),
        "tools_open_webui": await _check_http(settings.tools_open_webui_url, "/api/config"),
        "tools_browser_use": await _check_http(settings.tools_browser_use_url, "/"),
    }
    overall = "ok" if all(d.get("status") in ("ok", "not_configured") for d in deps.values()) else "degraded"
    return {
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": deps,
    }
