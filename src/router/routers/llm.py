"""LLM router: proxy to the Nebius Serverless AI vLLM endpoint."""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import httpx

from config import get_settings

router = APIRouter()
settings = get_settings()


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list
    temperature: float = 0.7
    max_tokens: int | None = None


@router.get("/models")
@router.get("/v1/models")
async def list_models():
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                f"{settings.nebius_llm_url.rsplit('/v1', 1)[0]}/v1/models",
                headers={"Authorization": f"Bearer {settings.nebius_llm_token}"} if settings.nebius_llm_token else {},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completion(req: ChatCompletionRequest):
    model = req.model or settings.nebius_llm_model
    payload = {
        "model": model,
        "messages": req.messages,
        "temperature": req.temperature,
    }
    if req.max_tokens:
        payload["max_tokens"] = req.max_tokens

    base_url = settings.nebius_llm_url.rsplit("/v1", 1)[0] + "/v1"
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.nebius_llm_token}",
                } if settings.nebius_llm_token else {"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
