from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings have safe defaults so the app boots with no .env at all."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Nexus Agents"
    secret_key: str = "dev-insecure-change-me"
    database_url: str = "sqlite:///./agent_platform.db"
    token_ttl_hours: int = 168

    # LLM
    llm_provider: str = "auto"  # auto | anthropic | openai | free | demo
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    # Defaults point at OpenRouter's free tier. Override for real OpenAI
    # (https://api.openai.com/v1, gpt-4o-mini) or Gemini/Groq.
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "deepseek/deepseek-chat-v3-0324:free"
    # Tried in order if the primary model is rate-limited (429) — free OpenRouter
    # models saturate at different times, so cycling improves the odds of a reply.
    openai_fallback_models: str = (
        "meta-llama/llama-3.3-70b-instruct:free,"
        "qwen/qwen-2.5-72b-instruct:free,"
        "google/gemma-2-9b-it:free,"
        "mistralai/mistral-7b-instruct:free"
    )
    openai_referer: str = "https://nexus-agents.onrender.com"
    openai_title: str = "Nexus Agents"
    llm_max_tokens: int = 600

    # Free keyless provider (Pollinations, OpenAI-compatible) — used when no paid
    # key is configured, and as automatic fallback when a paid provider errors.
    free_base_url: str = "https://text.pollinations.ai/openai"
    free_model: str = "openai"
    free_referer: str = "nexus-agents"

    # Channels
    avito_api_base: str = "https://api.avito.ru"

    cors_origins: str = "*"

    @property
    def resolved_provider(self) -> str:
        if self.llm_provider != "auto":
            return self.llm_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "free"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
