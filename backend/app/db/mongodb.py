"""MongoDB client and database access (replaces PostgreSQL/SQLite when use_mongodb=True)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from ..core.config import settings

_client: Optional["MongoClient"] = None  # type: ignore[name-defined]


def get_mongo_client():
    """Return singleton MongoDB client. Lazy import to avoid requiring pymongo when unused."""
    global _client
    if _client is None:
        try:
            from pymongo import MongoClient
            _client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
            )
        except ImportError as e:
            raise RuntimeError(
                "MongoDB support requires pymongo. Install with: pip install pymongo"
            ) from e
    return _client


def get_database():
    """Return the configured MongoDB database."""
    client = get_mongo_client()
    return client[settings.mongodb_database]


def get_collection(name: str):
    """Return a MongoDB collection by name."""
    return get_database()[name]


@contextmanager
def get_db_context() -> Generator:
    """Context manager yielding the database (for compatibility with session-like usage)."""
    yield get_database()
