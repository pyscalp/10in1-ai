"""Adapter for the Browser Use service running on the Tools Bundle VM."""
from .base import http_get_json, http_post_json


async def status(base_url: str) -> dict:
    return await http_get_json(base_url, "/")


async def run_task(base_url: str, task: str, url: str | None = None) -> dict:
    payload = {"task": task}
    if url is not None:
        payload["url"] = url
    return await http_post_json(base_url, "/", payload)
