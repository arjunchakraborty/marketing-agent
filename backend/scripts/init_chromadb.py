#!/usr/bin/env python
"""Script to initialize ChromaDB with a default collection."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError as e:
    CHROMADB_AVAILABLE = False
    print(f"ERROR: ChromaDB not available: {type(e).__name__}: {str(e)}")
    print("Install with: pip install chromadb")
    sys.exit(1)

from app.core.config import settings


def init_chromadb(collection_name: str = "UCO_Gear_Campaigns", overwrite: bool = False):
    """
    Initialize ChromaDB with a default collection.
    
    Args:
        collection_name: Name of the collection to create
        overwrite: If True, delete existing collection before creating new one
    """
    # Resolve vector_db_path relative to backend directory
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path
    
    # Create directory if it doesn't exist
    vector_db_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Initializing ChromaDB at: {vector_db_path}")
    print(f"Collection name: {collection_name}")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    # Check if collection already exists
    try:
        existing_collection = client.get_collection(name=collection_name)
        if overwrite:
            print(f"Collection '{collection_name}' already exists. Deleting...")
            client.delete_collection(name=collection_name)
            print(f"✓ Deleted existing collection '{collection_name}'")
        else:
            count = existing_collection.count()
            print(f"✓ Collection '{collection_name}' already exists with {count} documents")
            print("  Use --overwrite to recreate it")
            return True
    except Exception:
        # Collection doesn't exist, which is fine
        pass
    
    # Create the collection
    try:
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Campaign analysis embeddings"}
        )
        print(f"✓ Successfully created collection '{collection_name}'")
        print(f"✓ ChromaDB initialized at: {vector_db_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create collection: {type(e).__name__}: {str(e)}")
        return False


def list_collections():
    """List all existing collections."""
    # Resolve vector_db_path relative to backend directory
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path
    
    if not vector_db_path.exists():
        print(f"ChromaDB directory does not exist: {vector_db_path}")
        return
    
    print(f"Listing collections in: {vector_db_path}")
    
    try:
        client = chromadb.PersistentClient(
            path=str(vector_db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        if not collections:
            print("No collections found.")
        else:
            print(f"Found {len(collections)} collection(s):")
            for col in collections:
                try:
                    collection = client.get_collection(name=col.name)
                    count = collection.count()
                    print(f"  - {col.name}: {count} documents")
                except Exception as e:
                    print(f"  - {col.name}: (error getting count: {str(e)})")
    except Exception as e:
        print(f"Failed to list collections: {type(e).__name__}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize ChromaDB with a default collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with default collection name
  python scripts/init_chromadb.py

  # Initialize with custom collection name
  python scripts/init_chromadb.py --collection my_campaigns

  # Overwrite existing collection
  python scripts/init_chromadb.py --overwrite

  # List all collections
  python scripts/init_chromadb.py --list
        """
    )
    
    parser.add_argument(
        "--collection",
        default="UCO_Gear_Campaigns",
        help="Collection name to create (default: UCO_Gear_Campaigns)"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete existing collection if it exists before creating new one"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing collections instead of creating one"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_collections()
    else:
        success = init_chromadb(collection_name=args.collection, overwrite=args.overwrite)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
