"""Tools Bundle router: proxies to the private-IP tools VM.

Routes:
  /tools/pdf/*        -> Stirling PDF on the Tools Bundle VM
  /tools/chatui/*     -> Open WebUI on the Tools Bundle VM
  /tools/browser-use/ -> Browser Use service on the Tools Bundle VM
"""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File

from config import get_settings
import adapters.stirling_pdf_adapter as stirling
import adapters.open_webui_adapter as open_webui
import adapters.tools_browser_use_adapter as tools_browser_use

router = APIRouter()
settings = get_settings()


def _stirling_url() -> str:
    url = settings.tools_stirling_pdf_url
    if not url:
        raise HTTPException(status_code=503, detail="tools_stirling_pdf_url is not configured")
    return url


def _open_webui_url() -> str:
    url = settings.tools_open_webui_url
    if not url:
        raise HTTPException(status_code=503, detail="tools_open_webui_url is not configured")
    return url


def _browser_use_url() -> str:
    url = settings.tools_browser_use_url
    if not url:
        raise HTTPException(status_code=503, detail="tools_browser_use_url is not configured")
    return url


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list


class BrowserUseRequest(BaseModel):
    task: str
    url: str | None = None


# Stirling PDF proxy
@router.get("/pdf/")
async def stirling_status():
    return await stirling.health(_stirling_url())


@router.get("/pdf/status")
async def stirling_pdf_status():
    """Proxy Stirling PDF /actuator/health for a lightweight health check."""
    return await stirling.status(_stirling_url())


@router.post("/pdf/upload")
async def stirling_pdf_upload(file: UploadFile = File(...)):
    """Upload a PDF file and extract text via Stirling PDF."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf files are accepted")
    return await stirling.convert_to_text(_stirling_url(), file)


# Open WebUI proxy
@router.get("/chatui/")
async def open_webui_status():
    return await open_webui.status(_open_webui_url())


@router.get("/chatui/status")
async def open_webui_health_status():
    """Proxy Open WebUI /api/config for a lightweight health check."""
    return await open_webui.status(_open_webui_url())


@router.get("/chatui/models")
async def open_webui_models():
    return await open_webui.models(_open_webui_url())


@router.post("/chatui/chat/completions")
async def open_webui_chat_completion(req: ChatCompletionRequest):
    return await open_webui.chat_completion(
        _open_webui_url(),
        token="not-configured",
        model=req.model,
        messages=req.messages,
    )


# Browser Use proxy
@router.get("/browser-use/")
async def browser_use_status():
    return await tools_browser_use.status(_browser_use_url())


@router.post("/browser-use/")
async def browser_use_run_task(req: BrowserUseRequest):
    return await tools_browser_use.run_task(_browser_use_url(), req.task, req.url)
