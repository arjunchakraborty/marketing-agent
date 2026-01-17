#!/usr/bin/env python3
"""Script to run workflows on ComfyUI Cloud and download generated images."""
import argparse
import json
import sys
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.comfyui_cloud_service import ComfyUICloudService
from app.core.config import settings


def create_simple_workflow(prompt: str, negative_prompt: str = "", width: int = 1024, height: int = 1024) -> dict:
    """
    Create a simple text-to-image workflow for ComfyUI Cloud.
    
    Note: This is a simplified example. In practice, you should use a workflow
    exported from ComfyUI that matches the nodes available on ComfyUI Cloud.
    """
    # Generate unique node IDs
    checkpoint_loader = "1"
    clip_text_encode_pos = "2"
    clip_text_encode_neg = "3"
    empty_latent = "4"
    ksampler = "5"
    vae_decode = "6"
    save_image = "7"

    workflow = {
        checkpoint_loader: {
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors",
            },
            "class_type": "CheckpointLoaderSimple",
        },
        clip_text_encode_pos: {
            "inputs": {
                "text": prompt,
                "clip": [checkpoint_loader, 1],
            },
            "class_type": "CLIPTextEncode",
        },
        clip_text_encode_neg: {
            "inputs": {
                "text": negative_prompt or "blurry, low quality, distorted, watermark, text overlay",
                "clip": [checkpoint_loader, 1],
            },
            "class_type": "CLIPTextEncode",
        },
        empty_latent: {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
            "class_type": "EmptyLatentImage",
        },
        ksampler: {
            "inputs": {
                "seed": int(time.time()) % (2**32),
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": [checkpoint_loader, 0],
                "positive": [clip_text_encode_pos, 0],
                "negative": [clip_text_encode_neg, 0],
                "latent_image": [empty_latent, 0],
            },
            "class_type": "KSampler",
        },
        vae_decode: {
            "inputs": {
                "samples": [ksampler, 0],
                "vae": [checkpoint_loader, 2],
            },
            "class_type": "VAEDecode",
        },
        save_image: {
            "inputs": {
                "filename_prefix": "comfyui_cloud",
                "images": [vae_decode, 0],
            },
            "class_type": "SaveImage",
        },
    }

    return workflow


def main():
    """Main function to run ComfyUI Cloud workflow."""
    parser = argparse.ArgumentParser(
        description="Run a workflow on ComfyUI Cloud and download generated images"
    )
    parser.add_argument(
        "--workflow",
        type=str,
        help="Path to workflow JSON file (API format)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Text prompt for image generation (creates simple workflow if no workflow file provided)",
    )
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default="",
        help="Negative prompt (things to avoid in the image)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Image width (default: 1024)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help="Image height (default: 1024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for downloaded image(s)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Timeout in seconds (default: {settings.comfyui_cloud_timeout})",
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Only check status of a job (requires --prompt-id)",
    )
    parser.add_argument(
        "--prompt-id",
        type=str,
        help="Prompt ID (job ID) to check status for",
    )
    parser.add_argument(
        "--user-info",
        action="store_true",
        help="Show user information and exit",
    )
    parser.add_argument(
        "--object-info",
        action="store_true",
        help="Show available nodes/object info and exit",
    )
    
    args = parser.parse_args()
    
    # Initialize service
    print("Initializing ComfyUI Cloud Service...")
    try:
        service = ComfyUICloudService()
    except Exception as e:
        print(f"ERROR: Failed to initialize service: {type(e).__name__}: {str(e)}")
        sys.exit(1)
    
    if not service.api_key:
        print("ERROR: ComfyUI Cloud API key not configured.")
        print("Set COMFYUI_CLOUD_API_KEY environment variable or configure in settings.")
        sys.exit(1)
    
    print(f"✓ Connected to ComfyUI Cloud at {service.base_url}")
    
    # Handle user info request
    if args.user_info:
        try:
            user_info = service.get_user_info()
            print("\nUser Information:")
            print(json.dumps(user_info, indent=2))
        except Exception as e:
            print(f"ERROR: Failed to get user info: {type(e).__name__}: {str(e)}")
            sys.exit(1)
        return
    
    # Handle object info request
    if args.object_info:
        try:
            object_info = service.get_object_info()
            print("\nAvailable Nodes/Object Info:")
            print(f"Found {len(object_info)} node types")
            # Show first 20 node types as example
            for i, node_type in enumerate(list(object_info.keys())[:20], 1):
                print(f"  {i}. {node_type}")
            if len(object_info) > 20:
                print(f"  ... and {len(object_info) - 20} more")
            print("\nFull object info saved to object_info.json")
            with open("object_info.json", "w") as f:
                json.dump(object_info, f, indent=2)
        except Exception as e:
            print(f"ERROR: Failed to get object info: {type(e).__name__}: {str(e)}")
            sys.exit(1)
        return
    
    # Handle status check only
    if args.status_only:
        if not args.prompt_id:
            print("ERROR: --status-only requires --prompt-id")
            sys.exit(1)
        
        try:
            status_info = service.get_job_status(args.prompt_id)
            print(f"\nJob Status for {args.prompt_id}:")
            print(f"  ID: {status_info.get('id', args.prompt_id)}")
            print(f"  Status: {status_info.get('status', 'unknown')}")
            
            if status_info.get('created_at'):
                print(f"  Created: {status_info['created_at']}")
            if status_info.get('updated_at'):
                print(f"  Updated: {status_info['updated_at']}")
            if status_info.get('last_state_update'):
                print(f"  Last State Update: {status_info['last_state_update']}")
            if status_info.get('assigned_inference'):
                print(f"  Assigned Inference: {status_info['assigned_inference']}")
            if status_info.get('error_message'):
                print(f"  Error: {status_info['error_message']}")
            if status_info.get('history'):
                print(f"  History: Available (workflow completed)")
            
            # Show full JSON if requested or if there are additional fields
            print("\nFull status information:")
            print(json.dumps(status_info, indent=2))
        except Exception as e:
            print(f"ERROR: Failed to get job status: {type(e).__name__}: {str(e)}")
            sys.exit(1)
        return
    
    # Load or create workflow
    workflow = None
    
    if args.workflow:
        # Load workflow from file
        workflow_path = Path(args.workflow)
        if not workflow_path.exists():
            print(f"ERROR: Workflow file not found: {workflow_path}")
            sys.exit(1)
        
        print(f"\nLoading workflow from {workflow_path}...")
        try:
            with open(workflow_path, "r") as f:
                workflow_data = json.load(f)
            
            # Handle different workflow formats
            if isinstance(workflow_data, dict):
                # Check if it's wrapped in a "workflow" key
                if "workflow" in workflow_data:
                    workflow = workflow_data["workflow"]
                else:
                    # Assume it's already in API format
                    workflow = workflow_data
            
            print(f"✓ Loaded workflow with {len(workflow)} nodes")
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in workflow file: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to load workflow: {type(e).__name__}: {str(e)}")
            sys.exit(1)
    
    elif args.prompt:
        # Create simple workflow from prompt
        print(f"\nCreating simple workflow from prompt...")
        print(f"  Prompt: {args.prompt}")
        print(f"  Size: {args.width}x{args.height}")
        workflow = create_simple_workflow(
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            width=args.width,
            height=args.height,
        )
        print(f"✓ Created workflow with {len(workflow)} nodes")
    
    else:
        print("ERROR: Must provide either --workflow <file> or --prompt <text>")
        parser.print_help()
        sys.exit(1)
    
    # Submit workflow
    print("\nSubmitting workflow to ComfyUI Cloud...")
    try:
        submit_result = service.submit_workflow(workflow)
        prompt_id = submit_result["prompt_id"]
        print(f"✓ Workflow submitted successfully!")
        print(f"  Prompt ID (Job ID): {prompt_id}")
        print(f"  Client ID: {submit_result.get('client_id', 'N/A')}")
    except Exception as e:
        print(f"ERROR: Failed to submit workflow: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Wait for completion and download
    print(f"\nWaiting for workflow to complete (timeout: {args.timeout or service.timeout}s)...")
    try:
        status_info = service.wait_for_completion(prompt_id, timeout=args.timeout)
        
        # ComfyUI Cloud returns "success" status when job completes (not "completed")
        if status_info["status"] != "success":
            print(f"ERROR: Workflow did not complete successfully: {status_info}")
            sys.exit(1)
        
        print("✓ Workflow completed successfully!")
        
        # Extract and download outputs
        # History should be automatically fetched when status is "success", but ensure it's present
        if "history" not in status_info:
            print("⚠ Warning: History not found in status_info, fetching explicitly...")
            try:
                status_info["history"] = service.get_history_for_prompt(prompt_id)
            except Exception as e:
                print(f"ERROR: Failed to retrieve history: {type(e).__name__}: {str(e)}")
                sys.exit(1)
        
        history_entry = status_info["history"]
        output_files = service.extract_outputs_from_history(history_entry)
        
        if not output_files:
            print("⚠ Warning: No output files found in completed workflow")
            print("History entry:", json.dumps(history_entry, indent=2))
            return
        
        print(f"\nFound {len(output_files)} output file(s)")
        
        # Download all outputs
        downloaded_paths = []
        for i, output_info in enumerate(output_files, 1):
            print(f"\nDownloading output {i}/{len(output_files)}...")
            print(f"  Filename: {output_info['filename']}")
            print(f"  Subfolder: {output_info.get('subfolder', '')}")
            print(f"  Type: {output_info.get('type', 'output')}")
            
            try:
                # Determine output path
                if args.output:
                    if len(output_files) == 1:
                        save_path = args.output
                    else:
                        # Multiple outputs, append index
                        path_obj = Path(args.output)
                        save_path = str(path_obj.parent / f"{path_obj.stem}_{i}{path_obj.suffix}")
                else:
                    save_path = None
                
                downloaded_path = service.download_output(
                    filename=output_info["filename"],
                    subfolder=output_info["subfolder"],
                    output_type=output_info["type"],
                    output_path=save_path,
                )
                
                downloaded_paths.append(downloaded_path)
                print(f"  ✓ Downloaded to: {downloaded_path}")
                
            except Exception as e:
                error_msg = str(e) or f"{type(e).__name__} occurred"
                print(f"  ✗ Failed to download: {type(e).__name__}: {error_msg}")
                # Print full traceback for debugging
                import traceback
                print("  Full error details:")
                traceback.print_exc()
        
        print(f"\n✓ Success! Downloaded {len(downloaded_paths)} file(s):")
        for path in downloaded_paths:
            print(f"  - {path}")
        
    except TimeoutError as e:
        print(f"\n✗ Timeout: {str(e)}")
        print(f"\nYou can check the status later using:")
        print(f"  python {sys.argv[0]} --status-only --prompt-id {prompt_id}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

