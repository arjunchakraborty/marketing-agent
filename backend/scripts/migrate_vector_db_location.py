#!/usr/bin/env python
"""Script to migrate vector database from old location to backend/storage/vectors."""
import shutil
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def migrate_vector_db():
    """Move vector database from old location to new location."""
    # Old location (project root)
    old_path = Path(__file__).parent.parent.parent / "storage" / "vectors"
    
    # New location (backend/storage/vectors)
    new_path = Path(__file__).parent.parent / "storage" / "vectors"
    
    print(f"Checking for existing vector database...")
    print(f"Old location: {old_path}")
    print(f"New location: {new_path}")
    
    if not old_path.exists():
        print(f"No existing vector database found at {old_path}")
        print(f"Vector database will be created at {new_path} when first used.")
        return True
    
    if new_path.exists():
        print(f"Vector database already exists at {new_path}")
        response = input("Do you want to overwrite it? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled.")
            return False
        shutil.rmtree(new_path)
    
    # Create new directory
    new_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Move the directory
    print(f"Moving vector database from {old_path} to {new_path}...")
    shutil.move(str(old_path), str(new_path))
    
    print(f"✓ Successfully migrated vector database to {new_path}")
    return True

if __name__ == "__main__":
    success = migrate_vector_db()
    sys.exit(0 if success else 1)


