from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/nursing_pipeline"
    ANTHROPIC_API_KEY: str = ""
    UPLOAD_DIR: str = "/data/uploads"
    MARKDOWN_DIR: str = "/data/markdown"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EXTRACT_CHUNK_CHARS: int = 12000  # max chars sent to Claude per extraction call

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
