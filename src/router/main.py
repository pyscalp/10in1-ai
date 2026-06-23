"""Workbench Router entrypoint."""
import os

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import get_settings
from observability import configure_logging, dependency_health

configure_logging()

from routers import (
    crawl4ai,
    browser_use,
    maxun,
    stirling_pdf,
    supabase,
    langflow,
    dify,
    open_webui,
    openhands,
    coolify,
    llm,
    pipeline,
    tools_bundle,
)

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Unified router for 10 open-source AI tools on Nebius Serverless AI.",
    version="0.1.0",
)
security = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """Very simple token auth for the router endpoint."""
    expected = settings.router_auth_token
    if not expected or expected == "change-me":
        # In local/dev mode, auth can be disabled; but Nebius endpoint should still
        # be protected by its own token. Allow passthrough if not configured.
        return
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


@app.get("/")
async def root():
    return {"app": settings.app_name, "environment": settings.app_env}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    """Dependency health summary for monitoring."""
    return await dependency_health()


# Mount all tool routers.
app.include_router(crawl4ai.router, prefix="/crawl4ai", tags=["Crawl4AI"], dependencies=[Depends(verify_token)])
app.include_router(browser_use.router, prefix="/browser-use", tags=["Browser Use"], dependencies=[Depends(verify_token)])
app.include_router(maxun.router, prefix="/maxun", tags=["Maxun"], dependencies=[Depends(verify_token)])
app.include_router(stirling_pdf.router, prefix="/stirling-pdf", tags=["Stirling PDF"], dependencies=[Depends(verify_token)])
app.include_router(supabase.router, prefix="/supabase", tags=["Supabase"], dependencies=[Depends(verify_token)])
app.include_router(langflow.router, prefix="/langflow", tags=["Langflow"], dependencies=[Depends(verify_token)])
app.include_router(dify.router, prefix="/dify", tags=["Dify"], dependencies=[Depends(verify_token)])
app.include_router(open_webui.router, prefix="/open-webui", tags=["Open WebUI"], dependencies=[Depends(verify_token)])
app.include_router(openhands.router, prefix="/openhands", tags=["OpenHands"], dependencies=[Depends(verify_token)])
app.include_router(coolify.router, prefix="/coolify", tags=["Coolify"], dependencies=[Depends(verify_token)])
app.include_router(llm.router, prefix="/llm", tags=["Nebius LLM"], dependencies=[Depends(verify_token)])
app.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"], dependencies=[Depends(verify_token)])

# Tools Bundle routes under /tools/* for the private-IP VM.
app.include_router(tools_bundle.router, prefix="/tools", tags=["Tools Bundle"], dependencies=[Depends(verify_token)])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
