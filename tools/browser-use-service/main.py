"""Lightweight browser automation service using Playwright."""
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright


class TaskRequest(BaseModel):
    task: str
    url: str | None = None


class TaskResponse(BaseModel):
    status: str
    task: str
    url: str | None
    result: str


app = FastAPI(title="Browser Use Microservice")


@app.get("/")
async def health():
    return {"status": "ok", "service": "browser-use"}


@app.post("/", response_model=TaskResponse)
async def run_task(req: TaskRequest):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            target_url = req.url or "https://www.google.com"
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            text = await page.inner_text("body")
            await browser.close()
            return TaskResponse(
                status="ok",
                task=req.task,
                url=target_url,
                result=f"Title: {title}\n\nBody text (first 2000 chars):\n{text[:2000]}",
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
