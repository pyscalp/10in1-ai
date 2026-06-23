"""Centralised configuration for the Workbench Router."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Nebius 10-in-1 AI Workbench"
    app_env: str = "local"
    log_level: str = "info"
    router_auth_token: str = "change-me"

    # Nebius LLM endpoint (vLLM / OpenAI-compatible)
    nebius_llm_url: str = "http://localhost:8001/v1"
    nebius_llm_model: str = "Qwen/Qwen3-0.6B"
    nebius_llm_token: str = ""

    # Supabase
    supabase_url: str = "http://localhost:54321"
    supabase_key: str = ""
    supabase_db_url: str = ""

    # Managed PostgreSQL (nebius10-db) direct connection
    database_url: str = ""

    # Tool service URLs
    crawl4ai_url: str = ""
    stirling_pdf_url: str = "http://localhost:8080"
    langflow_url: str = "http://localhost:7860"
    dify_url: str = "http://localhost:3000"
    dify_api_key: str = ""
    open_webui_url: str = "http://localhost:8081"
    browser_use_url: str = "http://localhost:8001"
    maxun_url: str = "http://localhost:8082"
    openhands_url: str = "http://localhost:3001"
    openhands_api_key: str = ""
    coolify_url: str = "http://localhost:3002"
    coolify_api_token: str = ""
    coolify_webhook_uuid: str = ""

    # Tools Bundle VM (private IP) service URLs
    tools_stirling_pdf_url: str = ""
    tools_open_webui_url: str = ""
    tools_browser_use_url: str = ""

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() == "local"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
