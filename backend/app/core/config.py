from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings, loaded from the environment and backend/.env."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str = "postgresql+asyncpg://job_user:job_password@localhost:5432/job_scraper"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"  # comma-separated
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
