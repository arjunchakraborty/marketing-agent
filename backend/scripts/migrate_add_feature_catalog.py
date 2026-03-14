#!/usr/bin/env python
"""Migration script to add feature_catalog column to image_analysis_results table."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.db.session import engine


def check_column_exists(table_name: str, column_name: str, engine) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Add missing columns to image_analysis_results table if they don't exist."""
    print("Checking image_analysis_results table structure...")
    
    # Check if table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'image_analysis_results' not in tables:
        print("ERROR: image_analysis_results table does not exist!")
        print("Please run the application first to create the tables.")
        return False
    
    columns_to_add = [
        ('feature_catalog', 'TEXT'),
        ('email_features', 'TEXT'),  # Also check for email_features
    ]
    
    success = True
    for column_name, column_type in columns_to_add:
        # Check if column exists
        if check_column_exists('image_analysis_results', column_name, engine):
            print(f"✓ {column_name} column already exists")
            continue
        
        print(f"Adding {column_name} column...")
        
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(f"""
                        ALTER TABLE image_analysis_results 
                        ADD COLUMN {column_name} {column_type}
                    """)
                )
            print(f"✓ Successfully added {column_name} column")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"✓ {column_name} column already exists (detected during add)")
            else:
                print(f"ERROR: Failed to add {column_name} column: {str(e)}")
                success = False
    
    return success


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

