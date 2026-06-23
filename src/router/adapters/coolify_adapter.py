"""Coolify adapter: trigger a deployment via webhook or API."""
from .base import http_get_json, http_post_json


async def status(base_url: str, api_token: str | None = None) -> dict:
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    try:
        return await http_get_json(base_url, "/api/v1/health", headers=headers)
    except Exception as exc:
        return {
            "tool": "coolify",
            "status": "stub",
            "message": str(exc),
        }


async def deploy_via_webhook(base_url: str, webhook_uuid: str) -> dict:
    """Trigger a Coolify webhook deployment.

    The webhook URL is usually: {coolify_url}/webhooks/source/{uuid}
    """
    headers = {"Content-Type": "application/json"}
    try:
        return await http_post_json(
            base_url,
            f"/webhooks/source/{webhook_uuid}",
            {},
            headers=headers,
        )
    except Exception as exc:
        return {
            "tool": "coolify",
            "status": "stub",
            "message": str(exc),
            "webhook_uuid": webhook_uuid,
        }
