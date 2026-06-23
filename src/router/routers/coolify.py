"""Coolify router."""
from pydantic import BaseModel
from fastapi import APIRouter

from config import get_settings
import adapters.coolify_adapter as coolify

router = APIRouter()
settings = get_settings()


class DeployWebhookRequest(BaseModel):
    webhook_uuid: str | None = None


@router.get("/")
async def status():
    return await coolify.status(settings.coolify_url, settings.coolify_api_token)


@router.post("/deploy")
async def deploy(req: DeployWebhookRequest):
    uuid = req.webhook_uuid or settings.coolify_webhook_uuid
    return await coolify.deploy_via_webhook(settings.coolify_url, uuid)
