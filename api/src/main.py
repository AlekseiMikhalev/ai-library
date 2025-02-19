from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.v1.upload import router as api_v1_router
from src.config.settings import AppSettings


@lru_cache()
def get_settings() -> AppSettings:
    config = AppSettings()
    return config


app_settings = get_settings()

docs_url = "/docs" if app_settings.ENABLE_DOCS else None
redoc_url = "/redoc" if app_settings.ENABLE_DOCS else None
openapi_url = "/openapi.json" if app_settings.ENABLE_DOCS else None


ai_library_app = FastAPI(
    **app_settings.model_dump(),
    summary=Path("docs/app_overview.md").read_text(),
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    root_path="/api",
)

ai_library_app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=app_settings.CORS_METHODS,
    allow_headers=app_settings.CORS_HEADERS,
)


@ai_library_app.get("/", tags=["healthcheck"])
def healthcheck() -> dict[str, Any]:
    """Health check endpoint for the AI Library API."""
    return app_settings.app_info


ai_library_app.include_router(api_v1_router)
