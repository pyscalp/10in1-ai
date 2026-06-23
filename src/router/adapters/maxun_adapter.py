"""Maxun adapter: point-and-click scraping workflow API."""
from .base import http_get_json, http_post_json


async def get_status(base_url: str) -> dict:
    """Health / status of a Maxun instance."""
    return await http_get_json(base_url, "/")


async def run_robot(base_url: str, robot_id: str, payload: dict | None = None) -> dict:
    """Trigger a Maxun robot / scrape run."""
    return await http_post_json(
        base_url,
        f"/api/v1/robots/{robot_id}/run",
        payload or {},
    )
