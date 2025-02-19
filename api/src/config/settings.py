from typing import Any

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    app_info: dict[str, Any] = {
        "title": "AI Library",
        "version": "0.1.0",
        "author": "mikhalev.aleksei1@gmail.com",
        "created": "2025-02-16",
    }

    ENABLE_DOCS: bool = False

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_DB: str
    NEO4J_PASSWORD: str

    # MongoDB
    MONGO_DB_URL: str
    MONGO_DB_NAME: str

    # LLMSherpa
    LLMSHERPA_API_URL: str

    # CORS
    CORS_ORIGINS: list[str]
    CORS_HEADERS: list[str]
    CORS_METHODS: list[str]

    # Logs
    DEBUG_MODE: bool = False

    class Config:
        env_file = "../../.env"
        extra = "allow"


app_settings = AppSettings()
