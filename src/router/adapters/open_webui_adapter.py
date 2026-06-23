"""Open WebUI adapter: proxy useful endpoints."""
from .base import http_get_json, http_post_json


async def status(base_url: str) -> dict:
    return await http_get_json(base_url, "/api/config")


async def models(base_url: str, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return await http_get_json(base_url, "/api/models", headers=headers)


async def chat_completion(
    base_url: str,
    token: str,
    model: str,
    messages: list,
) -> dict:
    """Proxy an OpenAI-compatible chat completion through Open WebUI."""
    payload = {"model": model, "messages": messages}
    headers = {"Authorization": f"Bearer {token}"}
    return await http_post_json(base_url, "/api/chat/completions", payload, headers=headers)
