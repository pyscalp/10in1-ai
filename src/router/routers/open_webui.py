"""Open WebUI router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.open_webui_adapter as open_webui

router = APIRouter()
settings = get_settings()


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list


@router.get("/")
async def status():
    return await open_webui.status(settings.open_webui_url)


@router.get("/models")
async def models():
    return await open_webui.models(settings.open_webui_url)


@router.post("/chat/completions")
async def chat_completion(req: ChatCompletionRequest):
    # Token must be an Open WebUI API key; in this MVP we rely on the public endpoint.
    return await open_webui.chat_completion(
        settings.open_webui_url,
        token="not-configured",
        model=req.model,
        messages=req.messages,
    )
