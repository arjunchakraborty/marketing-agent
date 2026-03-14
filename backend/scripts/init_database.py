#!/usr/bin/env python
"""Script to initialize SQLite database with all required tables."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.db.session import engine
from app.models.kpi_cache import ensure_cache_tables
from app.models.campaign_analysis import (
    CampaignAnalysis,
    EmailFeatureCatalog,
    ExperimentRun,
    ImageAnalysisResult,
    VisualElementCorrelation,
)


def init_campaign_analysis_tables(db_engine: Engine) -> None:
    """Initialize campaign analysis related tables."""
    print("Creating campaign analysis tables...")
    
    CampaignAnalysis.__table__.create(db_engine, checkfirst=True)
    print("  ✓ campaign_analysis")
    
    ImageAnalysisResult.__table__.create(db_engine, checkfirst=True)
    print("  ✓ image_analysis_results")
    
    VisualElementCorrelation.__table__.create(db_engine, checkfirst=True)
    print("  ✓ visual_element_correlations")
    
    EmailFeatureCatalog.__table__.create(db_engine, checkfirst=True)
    print("  ✓ email_feature_catalog")
    
    ExperimentRun.__table__.create(db_engine, checkfirst=True)
    print("  ✓ experiment_runs")


def init_campaigns_table(db_engine: Engine) -> None:
    """Initialize campaigns table for Klaviyo data."""
    print("Creating campaigns table...")
    
    create_stmt = text("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT NOT NULL,
            campaign_name TEXT,
            subject TEXT,
            sent_at TEXT,
            sent_count INTEGER DEFAULT 0,
            delivered_count INTEGER DEFAULT 0,
            bounced_count INTEGER DEFAULT 0,
            opened_count INTEGER DEFAULT 0,
            clicked_count INTEGER DEFAULT 0,
            converted_count INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0.0,
            open_rate REAL,
            click_rate REAL,
            conversion_rate REAL,
            unsubscribed_count INTEGER DEFAULT 0,
            spam_count INTEGER DEFAULT 0,
            products TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(campaign_id)
        )
    """)
    
    with db_engine.begin() as connection:
        connection.execute(create_stmt)
        
        # Create indexes
        try:
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_sent_at ON campaigns(sent_at)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_conversion_rate ON campaigns(conversion_rate)"))
        except Exception:
            pass  # Indexes might already exist
    
    print("  ✓ campaigns")


def init_dataset_registry_table(db_engine: Engine) -> None:
    """Initialize dataset registry table for CSV ingestion."""
    print("Creating dataset registry table...")
    
    create_stmt = text("""
        CREATE TABLE IF NOT EXISTS dataset_registry (
            table_name TEXT PRIMARY KEY,
            business TEXT NOT NULL,
            category TEXT NOT NULL,
            dataset_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            columns TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        )
    """)
    
    with db_engine.begin() as connection:
        connection.execute(create_stmt)
    
    print("  ✓ dataset_registry")


def init_email_campaigns_table(db_engine: Engine) -> None:
    """Initialize email_campaigns table for campaign generation."""
    print("Creating email_campaigns table...")
    
    create_stmt = text("""
        CREATE TABLE IF NOT EXISTS email_campaigns (
            campaign_id TEXT PRIMARY KEY,
            campaign_name TEXT NOT NULL,
            subject_line TEXT,
            preview_text TEXT,
            html_content TEXT NOT NULL,
            design_guidance TEXT,
            talking_points TEXT,
            products TEXT,
            hero_image_url TEXT,
            product_images TEXT,
            expected_metrics TEXT,
            similar_campaigns TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    with db_engine.begin() as connection:
        connection.execute(create_stmt)
    
    print("  ✓ email_campaigns")


def init_database(overwrite: bool = False) -> bool:
    """
    Initialize SQLite database with all required tables.
    
    Args:
        overwrite: If True, drop all tables before recreating (WARNING: This will delete all data!)
    """
    # Get database path
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        relative_path = db_url.replace("sqlite:///", "")
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            backend_dir = Path(__file__).parent.parent
            db_path = backend_dir / relative_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Initializing database at: {db_path}")
    else:
        print(f"Initializing database at: {db_url}")
    
    if overwrite:
        print("\n⚠️  WARNING: Overwrite mode enabled. This will delete all existing data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return False
        
        # Drop all tables
        print("\nDropping existing tables...")
        from app.models.campaign_analysis import Base
        Base.metadata.drop_all(engine)
        
        # Drop other tables manually
        with engine.begin() as connection:
            for table in ["campaigns", "dataset_registry", "email_campaigns"]:
                try:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
                except Exception:
                    pass
    
    print("\nCreating tables...")
    
    try:
        # Initialize cache tables (KPI and prompt-to-SQL cache)
        print("\nCreating cache tables...")
        ensure_cache_tables(engine)
        print("  ✓ kpi_precomputed_sql")
        print("  ✓ prompt_sql_cache")
        
        # Initialize campaign analysis tables
        print("\nCreating campaign analysis tables...")
        init_campaign_analysis_tables(engine)
        
        # Initialize campaigns table
        print("\nCreating campaigns table...")
        init_campaigns_table(engine)
        
        # Initialize dataset registry
        print("\nCreating dataset registry table...")
        init_dataset_registry_table(engine)
        
        # Initialize email campaigns table
        print("\nCreating email campaigns table...")
        init_email_campaigns_table(engine)
        
        print("\n✓ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to initialize database: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def list_tables() -> None:
    """List all tables in the database."""
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        relative_path = db_url.replace("sqlite:///", "")
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            backend_dir = Path(__file__).parent.parent
            db_path = backend_dir / relative_path
        
        if not db_path.exists():
            print(f"Database does not exist: {db_path}")
            return
        
        print(f"Database location: {db_path}")
    
    try:
        with engine.connect() as connection:
            # For SQLite
            if db_url.startswith("sqlite:///"):
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            else:
                # For PostgreSQL
                result = connection.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
            
            tables = [row[0] for row in result]
            
            if not tables:
                print("No tables found in database.")
            else:
                print(f"\nFound {len(tables)} table(s):")
                for table in tables:
                    # Get row count
                    try:
                        count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        print(f"  - {table}: {count} rows")
                    except Exception:
                        print(f"  - {table}")
    except Exception as e:
        print(f"Failed to list tables: {type(e).__name__}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize SQLite database with all required tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database (creates tables if they don't exist)
  python scripts/init_database.py

  # Overwrite existing database (WARNING: deletes all data!)
  python scripts/init_database.py --overwrite

  # List all tables in the database
  python scripts/init_database.py --list
        """
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Drop all existing tables before creating new ones (WARNING: This will delete all data!)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing tables instead of initializing"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_tables()
    else:
        success = init_database(overwrite=args.overwrite)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
