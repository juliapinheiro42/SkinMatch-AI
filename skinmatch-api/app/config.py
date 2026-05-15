from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://skinmatch:skinmatch@localhost:5433/skinmatch"
    openai_api_key: str | None = None
    agent_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    ocr_provider: str = "tesseract"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


settings = Settings()
