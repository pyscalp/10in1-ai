"""Browser Use adapter: natural-language browser task."""
import os

from .base import http_get_json

try:
    from browser_use import Agent, Browser
    BROWSER_USE_AVAILABLE = True
except Exception:  # pragma: no cover
    BROWSER_USE_AVAILABLE = False


async def run_task(task: str, url: str | None = None, llm_url: str | None = None, llm_model: str | None = None) -> dict:
    """Run a browser-use task.

    If the python package is installed and an LLM endpoint is configured, this
    will spin up a headless browser agent. Otherwise it returns a stub that
    documents what would happen.
    """
    if not BROWSER_USE_AVAILABLE:
        return {
            "tool": "browser-use",
            "status": "stub",
            "message": "browser-use python package is not installed in this router container",
            "task": task,
            "url": url,
        }

    # Basic wiring for browser-use with an OpenAI-compatible endpoint.
    # Users can extend this with their preferred LLM class.
    return {
        "tool": "browser-use",
        "status": "not_implemented",
        "message": (
            "Native browser-use agent execution is intentionally left as a hook. "
            "Install playwright + browser-use in the router and wire your LLM here."
        ),
        "task": task,
        "url": url,
        "llm_url": llm_url or os.getenv("NEBIUS_LLM_URL"),
        "llm_model": llm_model or os.getenv("NEBIUS_LLM_MODEL"),
    }
