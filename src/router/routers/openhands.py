"""OpenHands router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.openhands_adapter as openhands

router = APIRouter()
settings = get_settings()


class OpenHandsTaskRequest(BaseModel):
    prompt: str
    repository: str | None = None


@router.post("/task")
async def start_task(req: OpenHandsTaskRequest):
    return await openhands.start_task(
        base_url=settings.openhands_url,
        prompt=req.prompt,
        repository=req.repository,
        api_key=settings.openhands_api_key,
    )
