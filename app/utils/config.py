from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "AI Chat Service"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "chatdb"

    @property
    def DATABASE_URL(self) -> str:
        """Returns the PostgreSQL async connection string."""
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{user}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    DB_ECHO: bool = False  # set True to log all SQL statements

    # ── OpenAI ───────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Gemini (OpenAI-compatible endpoint, fallback) ────
    GEMINI_API_KEY: str = ""
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-"

    # ── Jina AI ──────────────────────────────────────────
    JINA_API_KEY: str = ""

    # ── MCP ──────────────────────────────────────────────
    MCP_SERVER_URL: str = "http://localhost:6969/mcp"
    MCP_SERVER_TOKEN: str = ""


settings = Settings()
__all__ = ["settings"]
