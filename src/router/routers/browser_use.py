"""Browser Use router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.browser_use_adapter as browser_use

router = APIRouter()
settings = get_settings()


class BrowserUseRequest(BaseModel):
    task: str
    url: str | None = None


@router.post("/")
async def run_browser_task(req: BrowserUseRequest):
    return await browser_use.run_task(
        req.task,
        req.url,
        llm_url=settings.nebius_llm_url,
        llm_model=settings.nebius_llm_model,
    )
