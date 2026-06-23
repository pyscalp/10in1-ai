"""Langflow router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.langflow_adapter as langflow

router = APIRouter()
settings = get_settings()


class LangflowRunRequest(BaseModel):
    flow_id: str
    payload: dict


@router.get("/health")
async def health():
    return await langflow.status(settings.langflow_url)


@router.post("/run/{flow_id}")
async def run_flow(flow_id: str, req: LangflowRunRequest):
    return await langflow.run_flow(settings.langflow_url, flow_id, req.payload)
