"""Database engine and session utilities."""
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..core.config import settings


def _resolve_database_url() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        relative_path = url.replace("sqlite:///", "")
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            base_dir = Path(__file__).resolve().parents[1]
            db_path = (base_dir / relative_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"
    return url


engine: Engine = create_engine(_resolve_database_url(), future=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


