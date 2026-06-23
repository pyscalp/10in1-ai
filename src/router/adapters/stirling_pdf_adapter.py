"""Stirling PDF adapter: forward PDF operations to a Stirling PDF instance."""
import httpx
from fastapi import UploadFile

from .base import http_get_json


async def health(base_url: str) -> dict:
    return await http_get_json(base_url, "/")


async def status(base_url: str) -> dict:
    """Lightweight status endpoint for the tools bundle health check."""
    return await http_get_json(base_url, "/actuator/health")


async def convert_to_text(base_url: str, file: UploadFile) -> dict:
    """Upload a PDF and extract text through Stirling PDF."""
    content = await file.read()
    files = {
        "fileInput": (file.filename, content, file.content_type or "application/pdf"),
    }
    data = {"outputFormat": "txt"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/api/v1/convert/pdf/text",
            files=files,
            data=data,
        )
        response.raise_for_status()
        return {
            "tool": "stirling-pdf",
            "status": "ok",
            "filename": file.filename,
            "text": response.text,
        }
