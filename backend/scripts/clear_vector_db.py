#!/usr/bin/env python
"""Script to clear vector database collections."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ERROR: ChromaDB not available. Install with: pip install chromadb")
    sys.exit(1)

from app.core.config import settings


def clear_collection(collection_name: str):
    """Clear a specific collection."""
    # Resolve vector_db_path relative to backend directory
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path
    
    print(f"Connecting to vector database at: {vector_db_path}")
    
    client = chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"Collection '{collection_name}' has {count} documents")
        
        # Delete the collection
        client.delete_collection(name=collection_name)
        print(f"✓ Deleted collection '{collection_name}'")
        return True
    except Exception as e:
        print(f"Collection '{collection_name}' not found or error: {str(e)}")
        return False


def list_collections():
    """List all collections."""
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path
    
    client = chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    collections = client.list_collections()
    if collections:
        print(f"\nFound {len(collections)} collections:")
        for coll in collections:
            print(f"  - {coll.name} ({coll.count()} documents)")
    else:
        print("\nNo collections found")
    
    return [coll.name for coll in collections]


def clear_all_collections():
    """Clear all collections."""
    collections = list_collections()
    
    if not collections:
        print("No collections to clear")
        return
    
    print(f"\nClearing {len(collections)} collections...")
    for coll_name in collections:
        clear_collection(coll_name)


def main():
    parser = argparse.ArgumentParser(description="Clear vector database collections")
    parser.add_argument(
        "--collection",
        help="Collection name to clear (default: UCO_Gear_Campaigns)",
        default="UCO_Gear_Campaigns",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clear all collections"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all collections"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_collections()
        return
    
    if args.all:
        clear_all_collections()
    else:
        clear_collection(args.collection)
    
    print("\n" + "=" * 80)
    print("Vector database cleared!")
    print("=" * 80)
    print("\nYou can now rerun the import:")
    print("  python backend/scripts/load_klaviyo_to_vector_db.py")


if __name__ == "__main__":
    main()


