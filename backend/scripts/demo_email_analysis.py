#!/usr/bin/env python
"""Demo script showing what email analysis results look like."""
import json

# Simulated analysis result based on the UCO Camp Chef Knife email description
demo_result = {
    "image_id": "demo-12345",
    "campaign_id": "uco-camp-chef-knife",
    "overall_description": "Promotional email for UCO Camp Chef Knife featuring outdoor cooking scenarios, product features, discount offer, and multiple product images.",
    "visual_elements": [
        {
            "element_type": "logo",
            "description": "UCO logo in orange with tagline 'Unplug • Connect • Outdoors'",
            "position": "top-left",
            "colors": ["#FF6600", "orange"]
        },
        {
            "element_type": "navigation_menu",
            "description": "Navigation links: CAMPING, BACKYARD & PATIO, HIKING, EMERGENCY PREP",
            "position": "top-center",
            "colors": ["#000000", "black"]
        },
        {
            "element_type": "product_image",
            "description": "Hands slicing tomato on cutting board with onions and lettuce",
            "position": "middle",
            "colors": ["red", "green", "light green"]
        },
        {
            "element_type": "headline",
            "description": "UCO Camp Chef Knife announcement with 15% discount code CAMPKNIFE",
            "position": "middle",
            "text_content": "UCO Camp Chef Knife - 15% OFF with code CAMPKNIFE"
        },
        {
            "element_type": "cta_button",
            "description": "Orange call-to-action button",
            "position": "middle-center",
            "colors": ["#FF6600", "orange"],
            "text_content": "GRAB YOUR NEW CHEF KNIFE"
        },
        {
            "element_type": "product_image",
            "description": "Close-up of UCO knife with blue handle and silver blade",
            "position": "middle",
            "colors": ["blue", "silver", "gray"]
        },
        {
            "element_type": "product_image",
            "description": "UCO knife on cutting board with grilled meat, garlic, and jalapeño",
            "position": "bottom",
            "colors": ["blue", "silver", "brown", "green"]
        }
    ],
    "dominant_colors": [
        "#FF6600",  # Orange (brand color, CTA button)
        "#0000FF",  # Blue (knife handle)
        "#FFFFFF",  # White (background)
        "#000000",  # Black (text)
        "#FF0000",  # Red (tomato, brand accent)
        "#00FF00",  # Green (vegetables, nature)
    ],
    "text_content": """UCO Camp Chef Knife
15% OFF with code CAMPKNIFE

Features:
• Razor-Sharp Edge
• Premium Stainless Steel
• Comfortable, Non-Slip Grip
• Safe & Travel-Ready
• Packable Performance
• Not Just for Camp
• Perfect Gift Under $30

This isn't just another camp knife—it's the one you'll actually love to use. Your outdoor meals just got a serious upgrade.

GRAB YOUR NEW CHEF KNIFE""",
    "composition_analysis": "Three-column layout with header navigation, main content area featuring product images and text, and prominent CTA button. Visual hierarchy guides eye from logo → product images → features → CTA. Balanced use of white space and product photography.",
    "marketing_relevance": "Strong promotional email with clear value proposition, discount incentive, feature highlights, and multiple product use cases. Effective use of social proof through real-world usage images. Clear CTA with urgency.",
    "email_features": [
        {
            "feature_type": "logo",
            "feature_category": "branding",
            "confidence": 0.95,
            "position": "top-left",
            "bbox": {"x_min": 5, "y_min": 5, "x_max": 20, "y_max": 15},
            "text_content": "UCO",
            "color": "#FF6600"
        },
        {
            "feature_type": "call to action button",
            "feature_category": "cta_buttons",
            "confidence": 0.92,
            "position": "middle-center",
            "bbox": {"x_min": 35, "y_min": 55, "x_max": 65, "y_max": 62},
            "text_content": "GRAB YOUR NEW CHEF KNIFE",
            "color": "#FF6600"
        },
        {
            "feature_type": "discount badge",
            "feature_category": "promotions",
            "confidence": 0.88,
            "position": "middle",
            "bbox": {"x_min": 10, "y_min": 25, "x_max": 40, "y_max": 30},
            "text_content": "15% OFF with code CAMPKNIFE",
            "color": "#FF0000"
        },
        {
            "feature_type": "product image",
            "feature_category": "products",
            "confidence": 0.90,
            "position": "middle",
            "bbox": {"x_min": 10, "y_min": 20, "x_max": 90, "y_max": 50},
            "text_content": None,
            "color": None
        },
        {
            "feature_type": "headline",
            "feature_category": "content",
            "confidence": 0.85,
            "position": "middle",
            "bbox": {"x_min": 10, "y_min": 30, "x_max": 90, "y_max": 45},
            "text_content": "UCO Camp Chef Knife",
            "color": "#000000"
        },
        {
            "feature_type": "navigation menu",
            "feature_category": "structure",
            "confidence": 0.87,
            "position": "top-center",
            "bbox": {"x_min": 20, "y_min": 8, "x_max": 80, "y_max": 12},
            "text_content": "CAMPING, BACKYARD & PATIO, HIKING, EMERGENCY PREP",
            "color": "#000000"
        }
    ],
    "feature_catalog": {
        "cta_buttons": [
            {
                "feature_type": "call to action button",
                "confidence": 0.92,
                "position": "middle-center",
                "text_content": "GRAB YOUR NEW CHEF KNIFE",
                "color": "#FF6600"
            }
        ],
        "promotions": [
            {
                "feature_type": "discount badge",
                "confidence": 0.88,
                "position": "middle",
                "text_content": "15% OFF with code CAMPKNIFE",
                "color": "#FF0000"
            }
        ],
        "products": [
            {
                "feature_type": "product image",
                "confidence": 0.90,
                "position": "middle",
                "text_content": None
            }
        ],
        "content": [
            {
                "feature_type": "headline",
                "confidence": 0.85,
                "position": "middle",
                "text_content": "UCO Camp Chef Knife",
                "color": "#000000"
            }
        ],
        "branding": [
            {
                "feature_type": "logo",
                "confidence": 0.95,
                "position": "top-left",
                "text_content": "UCO",
                "color": "#FF6600"
            }
        ],
        "social_proof": [],
        "urgency": [],
        "structure": [
            {
                "feature_type": "navigation menu",
                "confidence": 0.87,
                "position": "top-center",
                "text_content": "CAMPING, BACKYARD & PATIO, HIKING, EMERGENCY PREP",
                "color": "#000000"
            }
        ],
        "summary": {
            "total_cta_buttons": 1,
            "total_promotions": 1,
            "total_products": 1,
            "total_content_elements": 1,
            "total_branding_elements": 1,
            "total_social_proof": 0,
            "total_urgency_indicators": 0,
            "total_structure_elements": 1
        }
    }
}

def print_demo_results():
    """Print demo analysis results."""
    print("\n" + "=" * 80)
    print("EMAIL IMAGE ANALYSIS RESULTS (Demo)")
    print("=" * 80)
    
    print(f"\nImage ID: {demo_result['image_id']}")
    print(f"Campaign ID: {demo_result['campaign_id']}")
    
    print("\n" + "-" * 80)
    print("OVERALL DESCRIPTION:")
    print("-" * 80)
    print(demo_result['overall_description'])
    
    print("\n" + "-" * 80)
    print(f"VISUAL ELEMENTS ({len(demo_result['visual_elements'])} found):")
    print("-" * 80)
    for i, elem in enumerate(demo_result['visual_elements'], 1):
        print(f"\n{i}. {elem['element_type'].upper()}")
        print(f"   Description: {elem['description']}")
        print(f"   Position: {elem['position']}")
        if elem.get('colors'):
            print(f"   Colors: {', '.join(elem['colors'])}")
    
    print("\n" + "-" * 80)
    print("DOMINANT COLORS:")
    print("-" * 80)
    for color in demo_result['dominant_colors']:
        print(f"  • {color}")
    
    print("\n" + "-" * 80)
    print(f"EMAIL FEATURES DETECTED ({len(demo_result['email_features'])} found):")
    print("-" * 80)
    for i, feature in enumerate(demo_result['email_features'], 1):
        print(f"\n{i}. {feature['feature_type'].upper()}")
        print(f"   Category: {feature['feature_category']}")
        print(f"   Confidence: {feature['confidence']:.2f}")
        print(f"   Position: {feature['position']}")
        if feature.get('text_content'):
            print(f"   Text: {feature['text_content']}")
        if feature.get('color'):
            print(f"   Color: {feature['color']}")
    
    print("\n" + "-" * 80)
    print("FEATURE CATALOG SUMMARY:")
    print("-" * 80)
    summary = demo_result['feature_catalog']['summary']
    for key, value in summary.items():
        if value > 0:
            print(f"  {key.replace('total_', '').replace('_', ' ').title()}: {value}")
    
    print("\n" + "-" * 80)
    print("EXTRACTED TEXT CONTENT:")
    print("-" * 80)
    print(demo_result['text_content'])
    
    print("\n" + "-" * 80)
    print("COMPOSITION ANALYSIS:")
    print("-" * 80)
    print(demo_result['composition_analysis'])
    
    print("\n" + "-" * 80)
    print("MARKETING RELEVANCE:")
    print("-" * 80)
    print(demo_result['marketing_relevance'])
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    print("\nTo analyze your own image, use:")
    print("  python backend/scripts/analyze_email_image.py <path_to_image>")
    print("=" * 80)

if __name__ == "__main__":
    print_demo_results()

