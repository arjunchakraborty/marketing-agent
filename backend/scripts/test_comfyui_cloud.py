#!/usr/bin/env python3
"""Example script for using ComfyUI Cloud service."""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.comfyui_cloud_service import ComfyUICloudService


def progress_callback(data: dict):
    """Example progress callback."""
    msg_type = data.get("type")
    msg_data = data.get("data", {})
    
    if msg_type == "progress":
        value = msg_data.get("value", 0)
        max_value = msg_data.get("max", 1)
        print(f"  Progress: {value}/{max_value}")
    elif msg_type == "executing":
        node = msg_data.get("node")
        if node:
            print(f"  Executing node: {node}")


async def main():
    """Example usage of ComfyUI Cloud service."""
    print("Initializing ComfyUI Cloud Service...")
    service = ComfyUICloudService()
    
    if not service.api_key:
        print("ERROR: ComfyUI Cloud API key not configured.")
        print("Set COMFYUI_CLOUD_API_KEY environment variable.")
        sys.exit(1)
    
    print("✓ ComfyUI Cloud service initialized!")
    
    # Example 1: Get object info
    print("\n1. Fetching available nodes...")
    # try:
    #     object_info = service.get_object_info()
    #     print(f"   Found {len(object_info)} node types")
    # except Exception as e:
    #     print(f"   Error: {e}")

    service.download_output("9a1fdaf8-c4b9-4f75-9899-41b7642dc3a3","","" "../storage/" )
    
    # Example 2: Load and submit a workflow
    print("\n2. Loading workflow...")
    workflow_path = backend_dir / "storage" / "Flux-Dev-ComfyUI-Workflow-api.json"
    
    if not workflow_path.exists():
        print(f"   Workflow file not found: {workflow_path}")
        print("   Creating a simple example workflow...")
        
        # Create a minimal example workflow
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors",
                },
                "class_type": "CheckpointLoaderSimple",
            },
            "2": {
                "inputs": {
                    "text": "a beautiful landscape, high quality",
                    "clip": ["1", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "3": {
                "inputs": {
                    "text": "blurry, low quality",
                    "clip": ["1", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "4": {
                "inputs": {
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1,
                },
                "class_type": "EmptyLatentImage",
            },
            "5": {
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                },
                "class_type": "KSampler",
            },
            "6": {
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2],
                },
                "class_type": "VAEDecode",
            },
            "7": {
                "inputs": {
                    "filename_prefix": "test",
                    "images": ["6", 0],
                },
                "class_type": "SaveImage",
            },
        }
    else:
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
        print(f"   Loaded workflow from {workflow_path}")
    
    # Example 3: Submit workflow
    print("\n3. Submitting workflow...")
    try:
        prompt_id = service.submit_workflow(workflow)
        print(f"   Workflow submitted! Prompt ID: {prompt_id}")
    except Exception as e:
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Example 4: Wait for completion with progress
    print("\n4. Waiting for completion...")
    try:
        outputs = await service.wait_for_completion(
            prompt_id,
            progress_callback=progress_callback,
        )
        print(f"   ✓ Workflow completed! Found {len(outputs)} output nodes")
    except Exception as e:
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Example 5: Download outputs
    print("\n5. Downloading outputs...")
    try:
        downloaded_files = service.download_outputs(outputs)
        print(f"   ✓ Downloaded {len(downloaded_files)} files:")
        for file_path in downloaded_files:
            print(f"     - {file_path}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 6: Complete end-to-end execution
    print("\n6. Running complete end-to-end execution...")
    try:
        # Modify workflow prompt
        if "2" in workflow and "inputs" in workflow["2"]:
            workflow["2"]["inputs"]["text"] = "a futuristic cityscape at sunset, highly detailed"
        
        downloaded_files = await service.execute_workflow(
            workflow,
            progress_callback=progress_callback,
        )
        print(f"   ✓ Complete execution finished! Downloaded {len(downloaded_files)} files")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

