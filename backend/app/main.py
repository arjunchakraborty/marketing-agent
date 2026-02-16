"""FastAPI application entrypoint for the Marketing Agent backend."""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.config import settings
from .core.middleware import APIKeyMiddleware
from .models.kpi_cache import ensure_cache_tables
from .db.session import engine


def setup_logging():
    """Configure logging for the application."""
    from .core.config import settings
    
    # Convert string log level to logging constant
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    root_level = log_level_map.get(settings.log_level.upper(), logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)  # Handler accepts all levels
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)
    
    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to DEBUG for detailed output if enabled
    if settings.log_experiments_debug:
        logging.getLogger("app.api.v1.experiments").setLevel(logging.DEBUG)
        logging.getLogger("app.workflows.campaign_strategy_workflow").setLevel(logging.DEBUG)
    else:
        logging.getLogger("app.api.v1.experiments").setLevel(root_level)
        logging.getLogger("app.workflows.campaign_strategy_workflow").setLevel(root_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def create_app() -> FastAPI:
    # Ensure cache tables exist on startup
    ensure_cache_tables(engine)
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Marketing intelligence agent backend supporting analytics, ingestion, and automation workflows.",
    )

    # Ensure localhost variants are included for development
    origins = list(settings.allowed_origins)
    if "http://localhost:3000" in origins and "http://127.0.0.1:3000" not in origins:
        origins.append("http://127.0.0.1:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Add API key authentication middleware (after CORS to allow OPTIONS requests)
    app.add_middleware(APIKeyMiddleware)

    app.include_router(api_router, prefix=settings.api_prefix)

    return app


# Setup logging before creating the app
setup_logging()

app = create_app()
