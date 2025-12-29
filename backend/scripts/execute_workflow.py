#!/usr/bin/env python3
"""Execute a ComfyUI workflow from a JSON file."""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.image_generation_service import ImageGenerationService


def main():
    """Execute a workflow from JSON file."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute a ComfyUI workflow from JSON file")
    parser.add_argument("workflow", help="Path to workflow JSON file")
    parser.add_argument("-o", "--output", help="Output image path")
    parser.add_argument("-p", "--prompt", help="Positive prompt to override")
    parser.add_argument("-n", "--negative-prompt", help="Negative prompt to override")
    parser.add_argument("--list-nodes", action="store_true", help="List all text prompt nodes in workflow")
    
    args = parser.parse_args()
    
    if not Path(args.workflow).exists():
        print(f"ERROR: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    print(f"Loading workflow from: {args.workflow}")
    service = ImageGenerationService()
    
    if not service.comfyui_available:
        print("ERROR: ComfyUI is not available. Please ensure ComfyUI is running at http://localhost:8188")
        sys.exit(1)
    
    # Load workflow to inspect nodes if requested
    workflow = service.load_workflow_from_file(args.workflow)
    if not workflow:
        print("ERROR: Failed to load workflow")
        sys.exit(1)
    
    # List prompt nodes if requested
    if args.list_nodes:
        prompt_nodes = service.find_text_prompt_nodes(workflow)
        if prompt_nodes:
            print("\nFound text prompt nodes:")
            for node_id, node_info in prompt_nodes.items():
                print(f"  Node {node_id}:")
                print(f"    Current text: {node_info['current_text'][:80]}...")
        else:
            print("\nNo CLIPTextEncode nodes found in workflow")
        sys.exit(0)
    
    print("Executing workflow...")
    if args.prompt or args.negative_prompt:
        print(f"  Positive prompt: {args.prompt}")
        print(f"  Negative prompt: {args.negative_prompt}")
    
    image_path = service.execute_workflow_from_file(
        workflow_path=args.workflow,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        output_path=args.output,
    )
    
    if image_path:
        print(f"\n✓ Success! Image generated at: {image_path}")
    else:
        print("\n✗ Failed to generate image")
        sys.exit(1)


if __name__ == "__main__":
    main()

