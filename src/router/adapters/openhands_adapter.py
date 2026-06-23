"""OpenHands adapter: ask a coding agent to improve the pipeline."""
from .base import http_post_json


async def start_task(
    base_url: str,
    prompt: str,
    repository: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Start an OpenHands session with a prompt.

    OpenHands runtime APIs vary by version; this is a generic HTTP hook.
    In local compose, the OpenHands UI/API is exposed on port 3001.
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {"prompt": prompt}
    if repository:
        payload["repository"] = repository
    try:
        return await http_post_json(base_url, "/api/conversation", payload, headers=headers)
    except Exception as exc:
        return {
            "tool": "openhands",
            "status": "stub",
            "message": str(exc),
            "prompt": prompt,
            "repository": repository,
        }
