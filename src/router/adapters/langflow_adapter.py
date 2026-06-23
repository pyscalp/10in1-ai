"""Langflow adapter: interact with a Langflow instance."""
from .base import http_get_json, http_post_json


async def status(base_url: str) -> dict:
    return await http_get_json(base_url, "/health")


async def run_flow(base_url: str, flow_id: str, payload: dict, api_key: str | None = None) -> dict:
    """Run a Langflow flow via its public API.

    Langflow exposes: POST /api/v1/run/{flow_id}
    """
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    return await http_post_json(
        base_url,
        f"/api/v1/run/{flow_id}",
        payload,
        headers=headers,
    )
