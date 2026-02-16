#!/usr/bin/env python
"""
Recreate UCO_Gear_Campaigns with cosine distance and re-ingest.

The existing collection was created with ChromaDB's default L2 distance, which
gives poor semantic ranking for text (e.g. "Camp Chef Knife" matching unrelated
campaigns). This script:

1. Deletes the existing UCO_Gear_Campaigns collection.
2. Re-runs the Klaviyo → vector DB load. The collection is recreated with
   hnsw:space=cosine, so search uses cosine distance and ranking improves.

Run from repo root, or ensure backend is on PYTHONPATH.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from app.core.config import settings


COLLECTION_NAME = "UCO_Gear_Campaigns"

# Same defaults as load_klaviyo_to_vector_db.py so one command does delete + re-ingest
DEFAULT_CSV = "/Users/a0c1fjt/work/data 2/UCO_Gear_campaigns/campaigns.csv"
DEFAULT_IMAGE_FOLDER = "/Users/a0c1fjt/work/data 2/UCO_Gear_campaigns/image-analysis-extract"


def delete_collection(collection_name: str) -> bool:
    """Delete the collection so it can be recreated with cosine."""
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path

    client = chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    try:
        coll = client.get_collection(name=collection_name)
        count = coll.count()
        client.delete_collection(name=collection_name)
        print(f"Deleted collection '{collection_name}' ({count} documents).")
        return True
    except Exception as e:
        print(f"Collection '{collection_name}' not found or error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Recreate UCO_Gear_Campaigns with cosine distance and re-ingest campaigns."
    )
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV,
        help="Path to campaigns CSV",
    )
    parser.add_argument(
        "--image-folder",
        default=DEFAULT_IMAGE_FOLDER,
        help="Path to image-analysis-extract folder",
    )
    parser.add_argument(
        "--collection",
        default=COLLECTION_NAME,
        help="Collection name to recreate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only delete the collection; do not re-ingest.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)

    if not CHROMADB_AVAILABLE:
        print("ERROR: ChromaDB not available. Install with: pip install chromadb", file=sys.stderr)
        sys.exit(1)

    print("Step 1: Delete existing collection (so it will be recreated with cosine)...")
    if not delete_collection(args.collection):
        sys.exit(1)

    if args.dry_run:
        print("\nDry run: skipping re-ingest.")
        print("Re-ingest with:")
        print(f"  python backend/scripts/load_klaviyo_to_vector_db.py --collection {args.collection}")
        return

    print("\nStep 2: Re-ingest campaigns (collection will be created with cosine)...")
    try:
        from app.workflows.load_klaviyo_analysis_to_vector_db import load_klaviyo_analysis_to_vector_db
        summary = load_klaviyo_analysis_to_vector_db(
            csv_file_path=args.csv,
            image_analysis_folder=args.image_folder,
            collection_name=args.collection,
            overwrite_existing=True,
        )
        print("\n" + "=" * 80)
        print("RE-INGEST SUMMARY")
        print("=" * 80)
        print(f"Collection: {summary['collection_name']}")
        print(f"Loaded: {summary['loaded']} | Skipped: {summary['skipped']} | Errors: {summary['errors']}")
        print("=" * 80)
        print("\nDone. Campaign search now uses cosine distance; try e.g. --search 'Camp Chef Knife'.")
    except Exception as e:
        print(f"Re-ingest failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
