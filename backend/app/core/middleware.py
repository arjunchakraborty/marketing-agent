"""Authentication middleware for securing API endpoints."""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication on protected endpoints."""
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a public endpoint
        path = request.url.path
        
        # Allow public endpoints
        if path in self.PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/redoc"):
            return await call_next(request)
        
        # Allow OPTIONS requests for CORS
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check authentication for protected endpoints
        settings = get_settings()
        
        # If no API keys configured, skip auth (development mode)
        if not settings.api_keys:
            return await call_next(request)
        
        # Extract API key from headers
        x_api_key = request.headers.get("X-API-Key")
        authorization = request.headers.get("Authorization")
        
        # Try Authorization Bearer token if X-API-Key is not present
        api_key = x_api_key
        if not api_key and authorization:
            if authorization.startswith("Bearer "):
                api_key = authorization.replace("Bearer ", "")
        
        # Check if API key is provided
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required. Provide X-API-Key header or Authorization Bearer token."},
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Check if API key is valid
        if api_key not in settings.api_keys:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        return await call_next(request)

