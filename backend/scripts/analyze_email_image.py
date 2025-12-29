#!/usr/bin/env python
"""Script to analyze a single email image."""
import argparse
import base64
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.image_analysis_service import ImageAnalysisService


def analyze_image_file(image_path: str, campaign_id: str = None, campaign_name: str = None):
    """Analyze an image file."""
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        print(f"Error: Image file not found: {image_path}")
        return None
    
    # Read image and convert to base64
    with open(image_path_obj, "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    # Initialize service
    print("Initializing Image Analysis Service...")
    service = ImageAnalysisService()
    
    # Analyze image
    print(f"Analyzing image: {image_path}")
    print("=" * 80)
    
    result = service.analyze_image(
        image_base64=image_base64,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        analysis_type="full",
        use_feature_detection=False,
    )
    
    return result


def analyze_image_url(image_url: str, campaign_id: str = None, campaign_name: str = None):
    """Analyze an image from URL."""
    print("Initializing Image Analysis Service...")
    service = ImageAnalysisService()
    
    print(f"Analyzing image from URL: {image_url}")
    print("=" * 80)
    
    result = service.analyze_image(
        image_url=image_url,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        analysis_type="full",
        use_feature_detection=False,
    )
    
    return result


def print_results(result: dict):
    """Print analysis results in a readable format."""
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\nImage ID: {result.get('image_id', 'N/A')}")
    print(f"Campaign ID: {result.get('campaign_id', 'N/A')}")
    
    # Overall description
    if result.get('overall_description'):
        print("\n" + "-" * 80)
        print("OVERALL DESCRIPTION:")
        print("-" * 80)
        print(result['overall_description'])
    
    # Visual elements
    visual_elements = result.get('visual_elements', [])
    if visual_elements:
        print("\n" + "-" * 80)
        print(f"VISUAL ELEMENTS ({len(visual_elements)} found):")
        print("-" * 80)
        for i, elem in enumerate(visual_elements, 1):
            print(f"\n{i}. {elem.get('element_type', 'Unknown')}")
            if elem.get('description'):
                print(f"   Description: {elem['description']}")
            if elem.get('position'):
                print(f"   Position: {elem['position']}")
            if elem.get('colors'):
                print(f"   Colors: {elem['colors']}")
    
    # Dominant colors
    dominant_colors = result.get('dominant_colors', [])
    if dominant_colors:
        print("\n" + "-" * 80)
        print("DOMINANT COLORS:")
        print("-" * 80)
        for color in dominant_colors:
            print(f"  - {color}")
    
    # Email features (currently disabled)
    email_features = result.get('email_features', [])
    if email_features:
        print("\n" + "-" * 80)
        print(f"EMAIL FEATURES DETECTED ({len(email_features)} found):")
        print("-" * 80)
        for i, feature in enumerate(email_features, 1):
            print(f"\n{i}. {feature.get('feature_type', 'Unknown')}")
            print(f"   Category: {feature.get('feature_category', 'N/A')}")
            print(f"   Confidence: {feature.get('confidence', 0):.2f}")
            if feature.get('position'):
                print(f"   Position: {feature['position']}")
            if feature.get('text_content'):
                print(f"   Text: {feature['text_content']}")
            if feature.get('color'):
                print(f"   Color: {feature['color']}")
            if feature.get('bbox'):
                print(f"   Bounding Box: {feature['bbox']}")
    
    # Feature catalog
    feature_catalog = result.get('feature_catalog', {})
    if feature_catalog:
        print("\n" + "-" * 80)
        print("FEATURE CATALOG:")
        print("-" * 80)
        
        summary = feature_catalog.get('summary', {})
        if summary:
            print("\nSummary:")
            for key, value in summary.items():
                if key.startswith('total_') and value > 0:
                    print(f"  {key.replace('total_', '').replace('_', ' ').title()}: {value}")
        
        # Show categorized features
        categories = ['cta_buttons', 'promotions', 'products', 'content', 'branding', 'social_proof', 'urgency', 'structure']
        for category in categories:
            items = feature_catalog.get(category, [])
            if items:
                print(f"\n{category.replace('_', ' ').title()} ({len(items)}):")
                for item in items[:3]:  # Show first 3
                    print(f"  - {item.get('feature_type', 'Unknown')} (confidence: {item.get('confidence', 0):.2f})")
    
    # Text content
    if result.get('text_content'):
        print("\n" + "-" * 80)
        print("EXTRACTED TEXT CONTENT:")
        print("-" * 80)
        print(result['text_content'])
    
    # Composition analysis
    if result.get('composition_analysis'):
        print("\n" + "-" * 80)
        print("COMPOSITION ANALYSIS:")
        print("-" * 80)
        print(result['composition_analysis'])
    
    # Marketing relevance
    if result.get('marketing_relevance'):
        print("\n" + "-" * 80)
        print("MARKETING RELEVANCE:")
        print("-" * 80)
        print(result['marketing_relevance'])
    
    # Errors
    if result.get('error'):
        print("\n" + "-" * 80)
        print("ERRORS:")
        print("-" * 80)
        print(result['error'])
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Analyze an email image")
    parser.add_argument("image", help="Path to image file or URL")
    parser.add_argument("--campaign-id", help="Campaign ID for context")
    parser.add_argument("--campaign-name", help="Campaign name for context")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    # Determine if it's a URL or file path
    if args.image.startswith("http://") or args.image.startswith("https://"):
        result = analyze_image_url(args.image, args.campaign_id, args.campaign_name)
    else:
        result = analyze_image_file(args.image, args.campaign_id, args.campaign_name)
    
    if result is None:
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_results(result)


if __name__ == "__main__":
    main()

