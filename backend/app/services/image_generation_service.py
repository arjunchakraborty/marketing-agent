"""Service for generating images using ComfyUI workflows."""
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating images using ComfyUI workflows."""

    def __init__(self) -> None:
        """Initialize the image generation service."""
        self.comfyui_base_url = settings.comfyui_base_url
        self.comfyui_available = False
        self.client_id = str(uuid.uuid4())
        self.available_models = []

        # Check ComfyUI availability
        try:
            response = httpx.get(f"{self.comfyui_base_url}/system_stats", timeout=5.0)
            response.raise_for_status()
            self.comfyui_available = True
            logger.info(f"ComfyUI available at {self.comfyui_base_url}")
            
            # Try to get available models
            try:
                models_response = httpx.get(f"{self.comfyui_base_url}/object_info", timeout=5.0)
                models_response.raise_for_status()
                object_info = models_response.json()
                if "CheckpointLoaderSimple" in object_info:
                    checkpoint_info = object_info["CheckpointLoaderSimple"]
                    if "input" in checkpoint_info and "required" in checkpoint_info["input"]:
                        if "ckpt_name" in checkpoint_info["input"]["required"]:
                            ckpt_info = checkpoint_info["input"]["required"]["ckpt_name"]
                            if isinstance(ckpt_info, list):
                                self.available_models = ckpt_info
                                logger.info(f"Found {len(self.available_models)} available models")
            except Exception as e:
                logger.warning(f"Could not fetch available models: {str(e)}")
        except Exception as e:
            logger.warning(f"ComfyUI not available at {self.comfyui_base_url}: {str(e)}")

    def generate_hero_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        size: str = "1024x1024",
        output_path: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        workflow_override: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Generate a hero image using ComfyUI workflow.
        
        Args:
            prompt: Description of the image to generate
            style: Style preference (e.g., "professional", "modern", "vibrant")
            size: Image size (default: "1024x1024", format: "WIDTHxHEIGHT")
            output_path: Optional path to save the image
            negative_prompt: Negative prompt (things to avoid)
            workflow_override: Optional custom workflow JSON to override default
            
        Returns:
            Path to the generated image, or None if generation failed
        """
        if not self.comfyui_available:
            logger.error("ComfyUI is not available. Please ensure ComfyUI is running.")
            return None

        enhanced_prompt = prompt
        if style:
            enhanced_prompt = f"{prompt}, {style} style, high quality, marketing email hero image, professional photography"

        # Default negative prompt
        if not negative_prompt:
            negative_prompt = "blurry, low quality, distorted, watermark, text overlay, ugly, bad anatomy"

        # Parse size
        width, height = self._parse_size(size)

        sample_prompt = " Primary action shot of a person chopping vegetables outdoors.The elements include Hands of person (wearing patterned shirt + jeans), Green cutting board, Red onion slices, Tomato (whole),Lettuce (bunch) and Outdoor setting (grass, chair, natural light). color scheme is Natural outdoor palette (earthy tones + vibrant produce colors) and composition is Medium shot focused on hands/food, shallow depth of field"

        try:
            # Use custom workflow if provided, otherwise use default
            if workflow_override:
                # If it's a string, treat it as a file path
                if isinstance(workflow_override, str):
                    workflow = self.load_workflow_from_file(workflow_override)
                    if not workflow:
                        raise ValueError(f"Failed to load workflow from {workflow_override}")
                    # Apply prompt overrides to the loaded workflow
                    
                else:
                    # It's already a workflow dictionary
                    workflow = workflow_override
            else:
                workflow = self._create_default_workflow(
                    prompt=sample_prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                )

            # Validate workflow before executing
            is_valid, error_msg = self.validate_workflow(workflow)
            if not is_valid:
                logger.error(f"Invalid workflow: {error_msg}")
                raise ValueError(f"Invalid workflow: {error_msg}")
            
            # Execute workflow
            image_path = self._execute_workflow(workflow, output_path)
            return image_path

        except Exception as e:
            logger.error(f"ComfyUI image generation failed: {str(e)}", exc_info=True)
            return None

    def _parse_size(self, size: str) -> tuple[int, int]:
        """Parse size string to width and height."""
        try:
            parts = size.split("x")
            if len(parts) == 2:
                return (int(parts[0]), int(parts[1]))
        except Exception:
            pass
        # Default to 1024x1024
        return (1024, 1024)

    def _create_default_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
    ) -> Dict:
        """
        Create a default ComfyUI workflow for text-to-image generation.
        
        This creates a basic workflow with:
        - CheckpointLoaderSimple (loads the model)
        - CLIPTextEncode (positive prompt)
        - CLIPTextEncode (negative prompt)
        - EmptyLatentImage (sets image size)
        - KSampler (generates the image)
        - VAEDecode (decodes the latent)
        - SaveImage (saves the result)
        """
        # Try to use an available model, fallback to configured model
        model_name = settings.comfyui_model
        if self.available_models and model_name not in self.available_models:
            logger.warning(f"Configured model '{model_name}' not found. Available models: {self.available_models[:5]}")
            if self.available_models:
                model_name = self.available_models[0]
                logger.info(f"Using first available model: {model_name}")
        
        # Generate unique node IDs (ComfyUI prefers string IDs)
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
                    "ckpt_name": model_name,
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            },
            clip_text_encode_pos: {
                "inputs": {
                    "text": prompt,
                    "clip": [checkpoint_loader, 1],
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Prompt)"
                }
            },
            clip_text_encode_neg: {
                "inputs": {
                    "text": negative_prompt,
                    "clip": [checkpoint_loader, 1],
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Negative)"
                }
            },
            empty_latent: {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1,
                },
                "class_type": "EmptyLatentImage",
                "_meta": {
                    "title": "Empty Latent Image"
                }
            },
            ksampler: {
                "inputs": {
                    "seed": int(time.time()) % (2**32),  # Ensure seed is within valid range
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
                "_meta": {
                    "title": "KSampler"
                }
            },
            vae_decode: {
                "inputs": {
                    "samples": [ksampler, 0],
                    "vae": [checkpoint_loader, 2],
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE Decode"
                }
            },
            save_image: {
                "inputs": {
                    "filename_prefix": "hero",
                    "images": [vae_decode, 0],
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "Save Image"
                }
            },
        }

        return workflow

    def _execute_workflow(
        self,
        workflow: Dict,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Execute a ComfyUI workflow and retrieve the generated image.
        
        Args:
            workflow: ComfyUI workflow dictionary
            output_path: Optional path to save the image
            
        Returns:
            Path to the generated image
        """
        # Step 1: Queue the prompt
        prompt_data = {"prompt": workflow, "client_id": self.client_id}
        
        try:
            response = httpx.post(
                f"{self.comfyui_base_url}/prompt",
                json=prompt_data,
                timeout=10.0,
            )
            
            # Get detailed error message if request failed
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"ComfyUI API error ({response.status_code}): {error_detail}")
                logger.error(f"Workflow sent: {json.dumps(workflow, indent=2)}")
                raise ValueError(f"ComfyUI API error ({response.status_code}): {error_detail}")
            
            response.raise_for_status()
            prompt_response = response.json()
            
            # Check for errors in response
            if "error" in prompt_response:
                error_msg = prompt_response["error"]
                logger.error(f"ComfyUI workflow error: {error_msg}")
                logger.error(f"Workflow sent: {json.dumps(workflow, indent=2)}")
                raise ValueError(f"ComfyUI workflow error: {error_msg}")
            
            prompt_id = prompt_response.get("prompt_id")
            if not prompt_id:
                logger.error(f"Unexpected ComfyUI response: {prompt_response}")
                raise ValueError(f"ComfyUI did not return a prompt_id: {prompt_response}")
            
            logger.info(f"Queued ComfyUI workflow, prompt_id: {prompt_id}")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error queueing ComfyUI workflow: {error_detail}")
            logger.error(f"Workflow sent: {json.dumps(workflow, indent=2)}")
            raise ValueError(f"ComfyUI HTTP error: {error_detail}") from e
        except Exception as e:
            logger.error(f"Failed to queue ComfyUI workflow: {str(e)}", exc_info=True)
            logger.error(f"Workflow sent: {json.dumps(workflow, indent=2)}")
            raise

        # Step 2: Poll for completion
        max_attempts = settings.comfyui_timeout // 2  # Poll every 2 seconds
        for attempt in range(max_attempts):
            try:
                # Check history for completion
                history_response = httpx.get(
                    f"{self.comfyui_base_url}/history/{prompt_id}",
                    timeout=5.0,
                )
                history_response.raise_for_status()
                history = history_response.json()

                if prompt_id in history:
                    # Workflow completed
                    output_images = history[prompt_id]["outputs"]
                    logger.info(f"ComfyUI workflow completed, prompt_id: {prompt_id}")

                    # Find the SaveImage node output
                    for node_id, node_output in output_images.items():
                        if "images" in node_output:
                            images = node_output["images"]
                            if images:
                                image_info = images[0]
                                filename = image_info["filename"]
                                subfolder = image_info.get("subfolder", "")
                                image_type = image_info.get("type", "output")

                                # Step 3: Download the image
                                image_url = f"{self.comfyui_base_url}/view"
                                params = {
                                    "filename": filename,
                                    "subfolder": subfolder,
                                    "type": image_type,
                                }

                                img_response = httpx.get(image_url, params=params, timeout=30.0)
                                img_response.raise_for_status()

                                # Step 4: Save the image
                                if output_path:
                                    save_path = Path(output_path)
                                else:
                                    storage_dir = Path(__file__).parent.parent.parent / "storage" / "generated_images"
                                    storage_dir.mkdir(parents=True, exist_ok=True)
                                    save_path = storage_dir / f"hero_{uuid.uuid4().hex[:8]}.png"

                                save_path.parent.mkdir(parents=True, exist_ok=True)

                                with open(save_path, "wb") as f:
                                    f.write(img_response.content)

                                logger.info(f"Generated and saved image to {save_path}")
                                return str(save_path)

                # Check if there's an error
                queue_response = httpx.get(
                    f"{self.comfyui_base_url}/queue",
                    timeout=5.0,
                )
                queue_response.raise_for_status()
                queue = queue_response.json()

                # Check for errors in queue
                if "queue_running" in queue:
                    for item in queue["queue_running"]:
                        if item[1] == prompt_id:
                            # Still running
                            break
                    else:
                        # Not in running queue, check if it failed
                        if "queue_pending" in queue:
                            for item in queue["queue_pending"]:
                                if item[1] == prompt_id:
                                    # Still pending
                                    break
                            else:
                                logger.warning(f"Prompt {prompt_id} not found in queue, may have failed")
                else:
                    # Check if completed
                    if prompt_id not in history:
                        time.sleep(2)
                        continue

            except httpx.HTTPError as e:
                logger.warning(f"Error checking ComfyUI status: {str(e)}")
                time.sleep(2)
                continue

            time.sleep(2)

        raise TimeoutError(f"ComfyUI workflow timed out after {settings.comfyui_timeout} seconds")

    def generate_image_from_reference(
        self,
        reference_images: List[str],
        prompt: str,
        style: Optional[str] = None,
        strength: float = 0.7,
    ) -> Optional[str]:
        """
        Generate an image based on reference images using ComfyUI img2img workflow.
        
        Args:
            reference_images: List of image paths/URLs to use as reference
            prompt: Description of desired image
            style: Style preference
            strength: Control strength for img2img (0.0-1.0)
            
        Returns:
            Path to generated image or None
        """
        if not self.comfyui_available:
            logger.error("ComfyUI is not available")
            return None

        if not reference_images:
            logger.warning("No reference images provided, falling back to text-to-image")
            return self.generate_hero_image(prompt, style=style)

        enhanced_prompt = prompt
        if style:
            enhanced_prompt = f"{prompt}, {style} style"

        # For now, use the first reference image
        # In a full implementation, you could blend multiple reference images
        reference_image_path = reference_images[0]

        try:
            # Create img2img workflow
            workflow = self._create_img2img_workflow(
                prompt=enhanced_prompt,
                image_path=reference_image_path,
                strength=strength,
            )

            # Execute workflow
            image_path = self._execute_workflow(workflow)
            return image_path

        except Exception as e:
            logger.error(f"ComfyUI img2img generation failed: {str(e)}", exc_info=True)
            return None

    def _create_img2img_workflow(
        self,
        prompt: str,
        image_path: str,
        strength: float = 0.7,
        width: int = 1024,
        height: int = 1024,
    ) -> Dict:
        """
        Create a ComfyUI workflow for image-to-image generation.
        
        This workflow:
        1. Loads the reference image
        2. Encodes it with VAE
        3. Applies the prompt with specified strength
        4. Generates the new image
        """
        # Upload the reference image first if it's a local path
        if Path(image_path).exists():
            # Upload to ComfyUI
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {"overwrite": "true"}
                upload_response = httpx.post(
                    f"{self.comfyui_base_url}/upload/image",
                    files=files,
                    data=data,
                    timeout=30.0,
                )
                upload_response.raise_for_status()
                upload_result = upload_response.json()
                image_filename = upload_result["name"]
        else:
            # Assume it's already in ComfyUI or is a URL
            # For URLs, you'd need to download and upload first
            image_filename = Path(image_path).name

        # Generate unique node IDs
        checkpoint_loader = "1"
        load_image = "2"
        vae_encode = "3"
        clip_text_encode_pos = "4"
        clip_text_encode_neg = "5"
        ksampler = "6"
        vae_decode = "7"
        save_image = "8"

        workflow = {
            checkpoint_loader: {
                "inputs": {
                    "ckpt_name": settings.comfyui_model,
                },
                "class_type": "CheckpointLoaderSimple",
            },
            load_image: {
                "inputs": {
                    "image": image_filename,
                },
                "class_type": "LoadImage",
            },
            vae_encode: {
                "inputs": {
                    "pixels": [load_image, 0],
                    "vae": [checkpoint_loader, 2],
                },
                "class_type": "VAEEncode",
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
                    "text": "blurry, low quality, distorted",
                    "clip": [checkpoint_loader, 1],
                },
                "class_type": "CLIPTextEncode",
            },
            ksampler: {
                "inputs": {
                    "seed": int(time.time()),
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": strength,
                    "model": [checkpoint_loader, 0],
                    "positive": [clip_text_encode_pos, 0],
                    "negative": [clip_text_encode_neg, 0],
                    "latent_image": [vae_encode, 0],
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
                    "filename_prefix": "hero_img2img",
                    "images": [vae_decode, 0],
                },
                "class_type": "SaveImage",
            },
        }

        return workflow

    def load_workflow_from_file(self, workflow_path: str) -> Optional[Dict]:
        """
        Load a ComfyUI workflow from a JSON file.
        
        ComfyUI workflows can be saved in different formats:
        - Direct workflow dictionary: {"1": {...}, "2": {...}}
        - Wrapped format: {"workflow": {"1": {...}}, "extra": {...}}
        - Full format with links: {"nodes": [...], "links": [...]}
        
        Args:
            workflow_path: Path to the workflow JSON file (relative paths resolved from backend directory)
            
        Returns:
            Normalized workflow dictionary (nodes only) or None if failed
        """
        try:
            # Resolve relative paths relative to backend directory
            workflow_file = Path(workflow_path)
            if not workflow_file.is_absolute():
                # Resolve relative to backend directory (parent of app directory)
                backend_dir = Path(__file__).parent.parent.parent
                workflow_file = backend_dir / workflow_path
            else:
                workflow_file = workflow_file
            
            with open(workflow_file, "r") as f:
                data = json.load(f) 
            
            # Normalize the workflow structure
            #workflow = self._normalize_workflow(data)
            workflow = data 
            
            if workflow:
                logger.info(f"Loaded workflow from {workflow_file} ({len(workflow)} nodes)")
                return workflow
            else:
                logger.error(f"Could not extract workflow from {workflow_file}")
                return None
        except Exception as e:
            logger.error(f"Failed to load workflow from {workflow_file}: {str(e)}")
            return None

    def _normalize_workflow(self, data: Dict) -> Optional[Dict]:
        """
        Normalize a ComfyUI workflow from various JSON formats.
        
        Args:
            data: Raw JSON data from workflow file
            
        Returns:
            Normalized workflow dictionary with node IDs as keys
        """
        # Case 1: Direct workflow format {"1": {...}, "2": {...}}
        if isinstance(data, dict):
            # Check if it looks like a workflow (has nodes with class_type)
            has_class_type = any(
                isinstance(v, dict) and "class_type" in v 
                for v in data.values()
            )
            if has_class_type:
                return data
            
            # Case 2: Wrapped format {"workflow": {...}}
            if "workflow" in data:
                return self._normalize_workflow(data["workflow"])
            
            # Case 3: Full format with nodes array {"nodes": [...], "links": [...]}
            if "nodes" in data:
                # Convert nodes array to dictionary format
                workflow = {}
                for node in data["nodes"]:
                    node_id = str(node.get("id", node.get("_id", len(workflow))))
                    workflow[node_id] = {
                        "class_type": node.get("type", node.get("class_type")),
                        "inputs": node.get("properties", node.get("inputs", {})),
                    }
                    # Preserve _meta if present
                    if "_meta" in node:
                        workflow[node_id]["_meta"] = node["_meta"]
                return workflow
        
        return None

    def execute_workflow_from_file(
        self,
        workflow_path: str,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        prompt_overrides: Optional[Dict[str, str]] = None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Load and execute a workflow from a JSON file with text prompt overrides.
        
        This is a convenience method that combines loading and executing.
        
        Args:
            workflow_path: Path to the workflow JSON file
            prompt: Optional positive prompt to override (automatically finds CLIPTextEncode nodes)
            negative_prompt: Optional negative prompt to override (automatically finds CLIPTextEncode nodes)
            prompt_overrides: Optional dictionary for manual overrides
                            Key format: "node_id:input_name" or "node_id"
                            Example: {"2:text": "new prompt", "3:text": "new negative"}
                            Note: If prompt/negative_prompt are provided, they take precedence
            output_path: Optional path to save the generated image
            
        Returns:
            Path to the generated image or None if failed
        """
        workflow = self.load_workflow_from_file(workflow_path)
        
        if not workflow:
            logger.error(f"Failed to load workflow from {workflow_path}")
            return None
        
        # Apply text prompt overrides if provided
        if prompt or negative_prompt:
            workflow = self.override_text_prompts(workflow, prompt, negative_prompt)
        
        # Apply manual prompt overrides if provided
        if prompt_overrides:
            workflow = self._apply_workflow_overrides(workflow, prompt_overrides)
        
        # Execute workflow
        try:
            image_path = self._execute_workflow(workflow, output_path)
            return image_path
        except Exception as e:
            logger.error(f"Failed to execute workflow: {str(e)}", exc_info=True)
            return None

    def override_text_prompts(
        self,
        workflow: Dict,
        positive_prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
    ) -> Dict:
        """
        Automatically find and override text prompts in a workflow.
        
        This method finds CLIPTextEncode nodes and overrides their text inputs.
        If multiple CLIPTextEncode nodes exist, it will override all of them.
        For more control, use prompt_overrides parameter with specific node IDs.
        
        Args:
            workflow: Workflow dictionary
            positive_prompt: Positive prompt text (overrides first CLIPTextEncode node found)
            negative_prompt: Negative prompt text (overrides second CLIPTextEncode node found, or all if only one exists)
            
        Returns:
            Modified workflow dictionary
        """
        workflow = json.loads(json.dumps(workflow))  # Deep copy
        
        # Find all CLIPTextEncode nodes
        text_encode_nodes = []
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                text_encode_nodes.append(node_id)
        
        if not text_encode_nodes:
            logger.warning("No CLIPTextEncode nodes found in workflow")
            return workflow
        
        # Override positive prompt (first node)
        if positive_prompt and len(text_encode_nodes) > 0:
            first_node = text_encode_nodes[0]
            if "inputs" not in workflow[first_node]:
                workflow[first_node]["inputs"] = {}
            workflow[first_node]["inputs"]["text"] = positive_prompt
            logger.info(f"Overrode positive prompt in node {first_node}: {positive_prompt[:50]}...")
        
        # Override negative prompt (second node if exists, otherwise first)
        if negative_prompt:
            if len(text_encode_nodes) > 1:
                # Use second node for negative prompt
                second_node = text_encode_nodes[1]
                if "inputs" not in workflow[second_node]:
                    workflow[second_node]["inputs"] = {}
                workflow[second_node]["inputs"]["text"] = negative_prompt
                logger.info(f"Overrode negative prompt in node {second_node}: {negative_prompt[:50]}...")
            elif len(text_encode_nodes) == 1:
                # Only one node, override it (assuming it's negative if positive was also set)
                if positive_prompt:
                    logger.warning("Only one CLIPTextEncode node found. Overriding it with negative prompt.")
                first_node = text_encode_nodes[0]
                if "inputs" not in workflow[first_node]:
                    workflow[first_node]["inputs"] = {}
                workflow[first_node]["inputs"]["text"] = negative_prompt
                logger.info(f"Overrode prompt in node {first_node}: {negative_prompt[:50]}...")
        
        return workflow

    def find_text_prompt_nodes(self, workflow: Dict) -> Dict[str, Dict]:
        """
        Find all text prompt nodes in a workflow.
        
        Args:
            workflow: Workflow dictionary
            
        Returns:
            Dictionary mapping node_id to node data for CLIPTextEncode nodes
        """
        prompt_nodes = {}
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                current_text = node_data.get("inputs", {}).get("text", "")
                prompt_nodes[node_id] = {
                    "node_id": node_id,
                    "current_text": current_text,
                    "node_data": node_data,
                }
        return prompt_nodes

    def _apply_workflow_overrides(
        self,
        workflow: Dict,
        overrides: Dict[str, any],
    ) -> Dict:
        """
        Apply overrides to workflow nodes.
        
        Args:
            workflow: Workflow dictionary
            overrides: Dictionary of overrides
                     Format: "node_id:input_name" -> value
                     Or: "node_id" -> value (for text inputs)
                     Values can be strings, numbers, lists, etc.
        
        Returns:
            Modified workflow dictionary
        """
        workflow = json.loads(json.dumps(workflow))  # Deep copy
        
        for key, value in overrides.items():
            if ":" in key:
                node_id, input_name = key.split(":", 1)
            else:
                node_id = key
                # Try to guess the input name for common node types
                if node_id in workflow:
                    node = workflow[node_id]
                    node_type = node.get("class_type", "")
                    if node_type == "CLIPTextEncode":
                        input_name = "text"
                    elif node_type == "KSampler":
                        input_name = "seed"  # Common override
                    elif node_type == "EmptyLatentImage":
                        input_name = "width"  # Common override
                    else:
                        input_name = "text"  # Default fallback
            
            if node_id in workflow:
                if "inputs" not in workflow[node_id]:
                    workflow[node_id]["inputs"] = {}
                workflow[node_id]["inputs"][input_name] = value
                logger.info(f"Applied override: {key} = {value}")
            else:
                logger.warning(f"Node {node_id} not found in workflow for override {key}")
        
        return workflow

    def get_available_models(self) -> List[str]:
        """
        Get list of available checkpoint models from ComfyUI.
        
        Returns:
            List of model names
        """
        if not self.comfyui_available:
            return []
        
        try:
            response = httpx.get(f"{self.comfyui_base_url}/object_info", timeout=10.0)
            response.raise_for_status()
            object_info = response.json()
            
            if "CheckpointLoaderSimple" in object_info:
                checkpoint_info = object_info["CheckpointLoaderSimple"]
                if "input" in checkpoint_info and "required" in checkpoint_info["input"]:
                    if "ckpt_name" in checkpoint_info["input"]["required"]:
                        ckpt_info = checkpoint_info["input"]["required"]["ckpt_name"]
                        if isinstance(ckpt_info, list):
                            return ckpt_info
                        elif isinstance(ckpt_info, (list, tuple)) and len(ckpt_info) > 0:
                            # Sometimes it's a tuple with [0] being the list
                            if isinstance(ckpt_info[0], list):
                                return ckpt_info[0]
            
            logger.warning("Could not parse available models from ComfyUI object_info")
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []

    def validate_workflow(self, workflow: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate a workflow structure before sending to ComfyUI.
        
        Args:
            workflow: Workflow dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(workflow, dict):
            return False, "Workflow must be a dictionary"
        
        if len(workflow) == 0:
            return False, "Workflow is empty"
        
        # Check that all nodes have required fields
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                print(node_data)
                return False, f"Node {node_id} is not a dictionary"
            
            if "class_type" not in node_data:
                print(node_data)
                return False, f"Node {node_id} missing 'class_type'"
            
            if "inputs" not in node_data:
                print(node_data)
                return False, f"Node {node_id} missing 'inputs'"
        
        return True, None
