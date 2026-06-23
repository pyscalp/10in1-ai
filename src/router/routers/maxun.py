"""Maxun router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.maxun_adapter as maxun

router = APIRouter()
settings = get_settings()


class MaxunRunRequest(BaseModel):
    robot_id: str
    payload: dict | None = {}


@router.get("/")
async def status():
    return await maxun.get_status(settings.maxun_url)


@router.post("/run")
async def run_robot(req: MaxunRunRequest):
    return await maxun.run_robot(settings.maxun_url, req.robot_id, req.payload or {})
