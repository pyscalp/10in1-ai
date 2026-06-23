"""Dify router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.dify_adapter as dify

router = APIRouter()
settings = get_settings()


class DifyChatRequest(BaseModel):
    query: str
    user: str = "nebius-router"
    conversation_id: str | None = None
    inputs: dict | None = {}


@router.get("/health")
async def health():
    return await dify.status(settings.dify_url)


@router.post("/chat-messages")
async def chat_messages(req: DifyChatRequest):
    return await dify.chat_messages(
        base_url=settings.dify_url,
        api_key=settings.dify_api_key,
        query=req.query,
        user=req.user,
        conversation_id=req.conversation_id,
        inputs=req.inputs,
    )
