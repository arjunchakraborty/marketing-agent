#!/usr/bin/env python
"""Script to analyze all images in Klaviyo directory and store in database."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.bulk_image_analysis_service import analyze_all_images_in_directory


def main():
    parser = argparse.ArgumentParser(
        description="Analyze all email images in a directory and store results in database"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="/Users/kerrief/projects/klyaviyo",
        help="Directory containing images (default: /Users/kerrief/projects/klyaviyo)",
    )
    parser.add_argument(
        "--experiment-id",
        help="Experiment run ID (default: auto-generated)",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-analyze images even if analysis already exists",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    print(f"Analyzing images in: {args.directory}")
    print("=" * 80)
    
    try:
        summary = analyze_all_images_in_directory(
            directory_path=args.directory,
            experiment_run_id=args.experiment_id,
            skip_existing=not args.no_skip_existing,
        )
        
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Experiment Run ID: {summary['experiment_run_id']}")
        print(f"Total Images: {summary['total_images']}")
        print(f"Analyzed: {summary['analyzed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Errors: {summary['errors']}")
        
        if summary['errors'] > 0:
            print("\nErrors:")
            for result in summary['results']:
                if result['status'] == 'error':
                    print(f"  - {result['image_path']}: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        print("Analysis complete! Results stored in database.")
        print("=" * 80)
        print(f"\nTo retrieve analyses for a campaign, use:")
        print(f"  from app.services.bulk_image_analysis_service import get_analysis_for_campaign")
        print(f"  analyses = get_analysis_for_campaign('CAMPAIGN_ID')")
        
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

