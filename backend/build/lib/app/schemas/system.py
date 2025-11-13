"""System-level response models."""
from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Health status of the service")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the health check")
