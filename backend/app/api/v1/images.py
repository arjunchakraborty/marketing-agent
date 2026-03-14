"""Image serving endpoints for campaign preview."""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Resolve the storage root once (backend/storage/)
_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage"


def _resolve_image_path(image_path: str) -> Path:
    """Resolve and validate an image path within the storage directory.

    Accepts either:
      - A relative path under storage/ (e.g. "generated_images/hero_17d165f4.png")
      - An absolute path that falls inside the storage directory
    """
    candidate = Path(image_path)

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (_STORAGE_ROOT / candidate).resolve()

    # Security: ensure the resolved path is inside the storage root
    if not str(resolved).startswith(str(_STORAGE_ROOT)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return resolved


_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


@router.get(
    "/{image_path:path}",
    summary="Serve an image from the storage directory",
    responses={
        200: {"content": {"image/png": {}, "image/jpeg": {}}},
        404: {"description": "Image not found"},
    },
)
async def serve_image(image_path: str) -> FileResponse:
    """Serve an image file from backend storage.

    The path is relative to the storage/ directory.
    Examples:
      - /api/v1/images/generated_images/hero_17d165f4.png
      - /api/v1/images/product_images/uco_gear/9996813992257/03b22301_9996813992257.png
    """
    resolved = _resolve_image_path(image_path)
    media_type = _MEDIA_TYPES.get(resolved.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(resolved),
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
