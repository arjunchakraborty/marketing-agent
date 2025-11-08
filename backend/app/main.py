"""FastAPI application entrypoint for the Marketing Agent backend."""
from fastapi import FastAPI

from .api.routes import router as api_router
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Marketing intelligence agent backend supporting analytics, ingestion, and automation workflows.",
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
