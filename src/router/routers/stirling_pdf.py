"""Stirling PDF router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.stirling_pdf_adapter as stirling

router = APIRouter()
settings = get_settings()


class StirlingPdfTextRequest(BaseModel):
    file_path: str


@router.get("/")
async def status():
    return await stirling.health(settings.stirling_pdf_url)


@router.post("/convert/text")
async def convert_to_text(req: StirlingPdfTextRequest):
    return await stirling.convert_to_text(settings.stirling_pdf_url, req.file_path)
