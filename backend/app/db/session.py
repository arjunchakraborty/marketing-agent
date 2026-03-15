"""Database engine and session utilities."""
import os
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..core.config import settings


def _resolve_database_url() -> str:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return url

    relative_path = url.replace("sqlite:///", "")
    db_path = Path(relative_path)
    if not db_path.is_absolute():
        base_dir = Path(__file__).resolve().parents[1]
        db_path = (base_dir / relative_path).resolve()

    # Serverless (Vercel etc.): /var/task is read-only; never mkdir there, use /tmp
    if "/var/task" in str(db_path) or os.environ.get("VERCEL"):
        return "sqlite:////tmp/marketing_agent.db"

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        if e.errno == 30:  # errno.EROFS (read-only file system)
            return "sqlite:////tmp/marketing_agent.db"
        raise

    return f"sqlite:///{db_path}"


engine: Engine = create_engine(_resolve_database_url(), future=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


