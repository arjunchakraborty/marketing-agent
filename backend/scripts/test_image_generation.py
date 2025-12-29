#!/usr/bin/env python3
"""Test script for image generation service."""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.image_generation_service import ImageGenerationService


def main():
    """Test image generation."""
    print("Initializing Image Generation Service...")
    service = ImageGenerationService()
    
    if not service.comfyui_available:
        print("ERROR: ComfyUI is not available. Please ensure ComfyUI is running at http://localhost:8188")
        sys.exit(1)
    
    print("✓ ComfyUI is available!")
    
    # Show available models
    print("\nFetching available models...")
    available_models = service.get_available_models()
    if available_models:
        print(f"Found {len(available_models)} available models:")
        for i, model in enumerate(available_models[:10], 1):
            marker = " ← configured" if model == service.comfyui_model else ""
            print(f"  {i}. {model}{marker}")
        if len(available_models) > 10:
            print(f"  ... and {len(available_models) - 10} more")
    else:
        print("  Warning: Could not fetch available models")
        print(f"  Using configured model: {service.comfyui_model}")
    
    print("\nGenerating hero image...")
    print("  Prompt: A professional product showcase for email marketing")
    print("  Style: modern")
    print("  Size: 1024x1024")
    
    # Generate an image
    try:
        image_path = service.generate_hero_image(
            prompt="A professional product showcase for email marketing",
            style="modern",
            size="1024x1024",
        )
        
        if image_path:
            print(f"\n✓ Success! Image generated at: {image_path}")
        else:
            print("\n✗ Failed to generate image (returned None)")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error generating image: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

