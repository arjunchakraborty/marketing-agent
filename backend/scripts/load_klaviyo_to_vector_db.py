#!/usr/bin/env python
"""Script to load Klaviyo analysis JSON into vector database."""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workflows.load_klaviyo_analysis_to_vector_db import (
    load_klaviyo_analysis_to_vector_db,
    search_campaigns_by_similarity,
)


def main():
    parser = argparse.ArgumentParser(
        description="Load Klaviyo campaign data from CSV and image analyses from JSON files into vector database"
    )
    parser.add_argument(
        "--csv",
        default="/Users/a0c1fjt/work/data 2/UCO_Gear_campaigns/campaigns.csv",
        help="Path to email_campaigns.csv file",
    )
    parser.add_argument(
        "--image-folder",
        default="/Users/a0c1fjt/work/data 2/UCO_Gear_campaigns/image-analysis-extract",
        help="Path to image-analysis-extract folder containing JSON files",
    )
    parser.add_argument(
        "--collection",
        default="UCO_Gear_campaigns",
        help="Vector database collection name (default: klaviyo_campaigns)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing campaigns",
    )
    parser.add_argument(
        "--search",
        help="Search for similar campaigns (e.g., 'bright colorful campaigns')",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of search results to return (default: 5)",
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
    
    # Search mode
    if args.search:
        print(f"Searching for campaigns similar to: '{args.search}'")
        print("=" * 80)
        
        try:
            results = search_campaigns_by_similarity(
                query_text=args.search,
                n_results=args.n_results,
                collection_name=args.collection,
            )
            
            print(f"\nFound {results['total_found']} similar campaigns:\n")
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. Campaign ID: {result['campaign_id']}")
                print(f"   Campaign Name: {result['metadata'].get('campaign_name', 'N/A')}")
                print(f"   Similarity Score: {result['similarity_score']:.3f}")
                print(f"   Open Rate: {result['metadata'].get('open_rate', 'N/A')}")
                print(f"   Click Rate: {result['metadata'].get('click_rate', 'N/A')}")
                print(f"   Image Analyses: {result['metadata'].get('total_image_analyses', 0)}")
                print()
            
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        
        return
    
    # Load mode
    print(f"Loading campaign data from CSV: {args.csv}")
    print(f"Loading image analyses from folder: {args.image_folder}")
    print("=" * 80)
    
    try:
        summary = load_klaviyo_analysis_to_vector_db(
            csv_file_path=args.csv,
            image_analysis_folder=args.image_folder,
            collection_name=args.collection,
            overwrite_existing=args.overwrite,
        )
        
        print("\n" + "=" * 80)
        print("LOADING SUMMARY")
        print("=" * 80)
        print(f"Collection: {summary['collection_name']}")
        print(f"Vector DB Path: {summary['vector_db_path']}")
        print(f"Total Campaigns: {summary['total_campaigns']}")
        print(f"Loaded: {summary['loaded']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Errors: {summary['errors']}")
        print(f"Campaigns with Images: {summary['campaigns_with_images']}")
        print(f"Campaigns without Images: {summary['campaigns_without_images']}")
        
        if summary['errors'] > 0:
            print("\nErrors:")
            for error in summary['error_details']:
                print(f"  - {error['campaign_id']}: {error['error']}")
        
        print("\n" + "=" * 80)
        print("Loading complete!")
        print("=" * 80)
        print(f"\nTo search for similar campaigns, use:")
        print(f"  python backend/scripts/load_klaviyo_to_vector_db.py --search 'your query'")
        
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

