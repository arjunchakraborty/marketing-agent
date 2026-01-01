"""API key authentication for securing endpoints."""
from fastapi import Header, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

from .config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Verify API key from either X-API-Key header or Authorization Bearer token.
    
    Args:
        x_api_key: API key from X-API-Key header
        authorization: Authorization header (supports Bearer token format)
    
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()
    
    # Skip authentication if API keys are not configured (for development)
    if not settings.api_keys:
        return "no-auth"
    
    # Try X-API-Key header first
    api_key = x_api_key
    
    # Fall back to Authorization Bearer token
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization.replace("Bearer ", "")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header or Authorization Bearer token.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if the API key is valid
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key

