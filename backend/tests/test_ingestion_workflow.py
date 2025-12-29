"""Tests for local CSV ingestion workflow utilities."""
from pathlib import Path

import pytest

from app.workflows.local_csv_ingestion import ingest_directory


def test_ingest_directory_missing_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        ingest_directory(missing_path)


