"""Vercel serverless entry point: expose the FastAPI app for serverless deployment."""
from app.main import app

__all__ = ["app"]
