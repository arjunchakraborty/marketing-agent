#!/usr/bin/env python
"""Script to clear experiment data from the database."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


def clear_experiments(experiment_run_id: str = None):
    """Clear experiment data from database."""
    print("Connecting to database...")
    print(f"Database URL: {settings.database_url}")
    
    tables_to_clear = [
        "email_feature_catalog",
        "visual_element_correlations",
        "image_analysis_results",
        "campaign_analysis",
        "experiment_runs",
    ]
    
    with engine.begin() as connection:
        if experiment_run_id:
            # Clear specific experiment
            print(f"\nClearing experiment run: {experiment_run_id}")
            for table in tables_to_clear:
                try:
                    result = connection.execute(
                        text(f"DELETE FROM {table} WHERE experiment_run_id = :run_id"),
                        {"run_id": experiment_run_id}
                    )
                    count = result.rowcount
                    if count > 0:
                        print(f"  ✓ Deleted {count} rows from {table}")
                except Exception as e:
                    print(f"  ✗ Error clearing {table}: {str(e)}")
        else:
            # Clear all experiments
            print("\nClearing all experiment data...")
            total_deleted = 0
            for table in tables_to_clear:
                try:
                    # First count rows
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    
                    if count > 0:
                        # Delete all rows
                        result = connection.execute(text(f"DELETE FROM {table}"))
                        deleted = result.rowcount
                        total_deleted += deleted
                        print(f"  ✓ Deleted {deleted} rows from {table}")
                    else:
                        print(f"  - No rows in {table}")
                except Exception as e:
                    # Table might not exist
                    if "no such table" in str(e).lower():
                        print(f"  - Table {table} does not exist (skipping)")
                    else:
                        print(f"  ✗ Error clearing {table}: {str(e)}")
            
            print(f"\nTotal rows deleted: {total_deleted}")


def list_experiments():
    """List all experiment runs."""
    print("Connecting to database...")
    
    with engine.begin() as connection:
        try:
            result = connection.execute(
                text("""
                    SELECT experiment_run_id, name, status, created_at, 
                           (SELECT COUNT(*) FROM campaign_analysis WHERE campaign_analysis.experiment_run_id = experiment_runs.experiment_run_id) as campaign_count,
                           (SELECT COUNT(*) FROM image_analysis_results WHERE image_analysis_results.experiment_run_id = experiment_runs.experiment_run_id) as image_count
                    FROM experiment_runs
                    ORDER BY created_at DESC
                """)
            )
            rows = result.fetchall()
            
            if rows:
                print(f"\nFound {len(rows)} experiment runs:")
                print("-" * 100)
                print(f"{'Run ID':<40} {'Name':<30} {'Status':<15} {'Campaigns':<10} {'Images':<10} {'Created':<20}")
                print("-" * 100)
                for row in rows:
                    run_id = row[0] or "N/A"
                    name = (row[1] or "Unnamed")[:28]
                    status = row[2] or "unknown"
                    campaign_count = row[3] or 0
                    image_count = row[4] or 0
                    created_at = row[5] or "N/A"
                    print(f"{run_id:<40} {name:<30} {status:<15} {campaign_count:<10} {image_count:<10} {created_at:<20}")
            else:
                print("\nNo experiment runs found")
            
            return [row[0] for row in rows if row[0]]
        except Exception as e:
            if "no such table" in str(e).lower():
                print("\nNo experiment_runs table found (database may be empty)")
            else:
                print(f"\nError listing experiments: {str(e)}")
            return []


def main():
    parser = argparse.ArgumentParser(description="Clear experiment data from database")
    parser.add_argument(
        "--experiment-id",
        help="Specific experiment run ID to clear (if not provided, clears all)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all experiment runs"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion (required when clearing all experiments)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_experiments()
        return
    
    if not args.experiment_id:
        # Clearing all experiments requires confirmation
        if not args.confirm:
            print("WARNING: This will delete ALL experiment data from the database!")
            print("Use --confirm flag to proceed, or use --experiment-id to delete a specific experiment.")
            print("\nUse --list to see all experiment runs first.")
            return
    
    clear_experiments(experiment_run_id=args.experiment_id)
    
    print("\n" + "=" * 80)
    print("Experiment data cleared!")
    print("=" * 80)


if __name__ == "__main__":
    main()

