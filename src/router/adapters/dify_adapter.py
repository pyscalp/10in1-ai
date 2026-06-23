"""Dify adapter: chat / workflow via Dify public API."""
from .base import http_get_json, http_post_json


async def status(base_url: str) -> dict:
    return await http_get_json(base_url, "/health")


async def chat_messages(
    base_url: str,
    api_key: str,
    query: str,
    user: str,
    conversation_id: str | None = None,
    inputs: dict | None = None,
) -> dict:
    """Send a chat message to a Dify app."""
    payload = {
        "inputs": inputs or {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id or "",
        "user": user,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    return await http_post_json(base_url, "/v1/chat-messages", payload, headers=headers)
