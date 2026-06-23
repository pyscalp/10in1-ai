"""Base helpers used by all tool adapters."""
import httpx
from fastapi import HTTPException

DEFAULT_TIMEOUT = 60.0


async def http_post_json(base_url: str, path: str, payload: dict | None = None, headers: dict | None = None, files: dict | None = None):
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{base_url.rstrip('/')}/{path.lstrip('/')}",
                json=payload if payload is not None and files is None else None,
                files=files,
                headers=headers or {},
            )
            response.raise_for_status()
            return response.json() if response.text else {"ok": True}
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Downstream error: {exc.response.text}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Could not reach downstream service: {exc}",
            ) from exc


async def http_get_json(base_url: str, path: str, params: dict | None = None, headers: dict | None = None):
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(
                f"{base_url.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                headers=headers or {},
            )
            response.raise_for_status()
            return response.json() if response.text else {"ok": True}
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Downstream error: {exc.response.text}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Could not reach downstream service: {exc}",
            ) from exc
