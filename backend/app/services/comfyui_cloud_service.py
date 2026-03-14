"""Service for generating images using ComfyUI Cloud workflows."""
import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlparse, urlencode

import httpx
import websockets
from websockets.client import WebSocketClientProtocol

from ..core.config import settings

logger = logging.getLogger(__name__)


class ComfyUICloudService:
    """Service for generating images using ComfyUI Cloud workflows."""

    def __init__(self) -> None:
        """Initialize the ComfyUI Cloud service."""
        self.api_key = (settings.comfyui_cloud_api_key or "").strip()
        base_url = settings.comfyui_cloud_base_url or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = settings.comfyui_cloud_timeout
        self.client_id = str(uuid.uuid4())

        if not self.api_key:
            logger.warning("ComfyUI Cloud API key not configured. Set COMFYUI_CLOUD_API_KEY environment variable.")
            logger.warning("Note: The environment variable name must be COMFYUI_CLOUD_API_KEY (not COMFY_CLOUD_API_KEY)")
        else:
            logger.info(f"ComfyUI Cloud API key loaded (length: {len(self.api_key)}, starts with: {self.api_key[:4]}...)")
        
        if not self.base_url:
            raise ValueError("ComfyUI Cloud base URL is not configured. Set COMFYUI_CLOUD_BASE_URL environment variable.")
        
        # Validate URL format
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid ComfyUI Cloud base URL: {self.base_url}. URL must start with http:// or https://")
        
        # Validate hostname is present
        try:
            parsed = urlparse(self.base_url)
            if not parsed.netloc:
                raise ValueError(f"Invalid ComfyUI Cloud base URL: {self.base_url}. Missing hostname.")
        except Exception as e:
            raise ValueError(f"Invalid ComfyUI Cloud base URL format: {self.base_url}. Error: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with API key."""
        if not self.api_key:
            logger.error("API key is empty when trying to get headers!")
            raise ValueError("ComfyUI Cloud API key is required. Set COMFYUI_CLOUD_API_KEY environment variable.")
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        logger.debug(f"Headers prepared with API key (length: {len(self.api_key)})")
        return headers

    def submit_workflow(
        self,
        workflow: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit a workflow to ComfyUI Cloud for execution.

        Args:
            workflow: ComfyUI workflow dictionary
            extra_data: Optional extra data (e.g., API keys for partner nodes)

        Returns:
            Prompt ID for tracking the workflow execution

        Raises:
            ValueError: If API key is missing or request fails
            httpx.HTTPStatusError: If HTTP request fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required. Set COMFYUI_CLOUD_API_KEY environment variable.")

        url = f"{self.base_url}/api/prompt"
        payload = {"prompt": workflow}
        
        if extra_data:
            payload["extra_data"] = extra_data

        try:
            headers = self._get_headers()
            logger.debug(f"Submitting workflow to {url} with headers: {list(headers.keys())}")
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                error_msg = result.get("error", "Unknown error")
                raise ValueError(f"Failed to submit workflow: {error_msg}")
            
            logger.info(f"Workflow submitted successfully, prompt_id: {prompt_id}")
            return prompt_id
            
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            status_code = e.response.status_code if e.response else 0
            
            if status_code == 401:
                raise ValueError("Invalid ComfyUI Cloud API key") from e
            elif status_code == 402:
                raise ValueError("Insufficient credits for ComfyUI Cloud") from e
            elif status_code == 429:
                raise ValueError("ComfyUI Cloud subscription inactive") from e
            else:
                raise ValueError(f"ComfyUI Cloud API error ({status_code}): {error_detail}") from e

    def upload_image(
        self,
        image_path: str,
        image_type: str = "input",
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """
        Upload an image to ComfyUI Cloud.

        Args:
            image_path: Path to the image file
            image_type: Type of image ("input" or "output")
            overwrite: Whether to overwrite existing files

        Returns:
            Upload result with filename and other metadata

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If upload fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        url = f"{self.base_url}/api/upload/image"
        
        try:
            with open(image_file, "rb") as f:
                files = {"image": (image_file.name, f, "image/png")}
                data = {
                    "type": image_type,
                    "overwrite": "true" if overwrite else "false",
                }
                
                # Remove Content-Type from headers for multipart request
                # httpx will set Content-Type automatically for multipart
                headers = {"X-API-Key": self.api_key}
                logger.debug(f"Upload image headers: X-API-Key present (length: {len(self.api_key)})")
                
                response = httpx.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60.0,
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Image uploaded successfully: {result.get('name', 'unknown')}")
                return result
                
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"Failed to upload image: {error_detail}") from e

    def get_job_status(self, prompt_id: str) -> Dict[str, Any]:
        """
        Check the status of a workflow job.

        Args:
            prompt_id: The prompt ID returned from submit_workflow

        Returns:
            Job status information

        Raises:
            ValueError: If request fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/job/{prompt_id}/status"
        
        try:
            response = httpx.get(
                url,
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"Failed to get job status: {error_detail}") from e

    async def wait_for_completion(
        self,
        prompt_id: str,
        timeout: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Wait for workflow completion using WebSocket connection.

        Args:
            prompt_id: The prompt ID to monitor
            timeout: Timeout in seconds (defaults to configured timeout)
            progress_callback: Optional callback function for progress updates
                             Called with message data dict

        Returns:
            Dictionary mapping node IDs to their outputs

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
            ValueError: If execution fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        timeout = timeout or self.timeout
        ws_url = f"wss://cloud.comfy.org/ws?clientId={self.client_id}&token={self.api_key}"
        
        outputs: Dict[str, Any] = {}
        
        async def _wait_for_completion_inner():
            async with websockets.connect(ws_url,max_size=None) as ws:
                logger.info(f"WebSocket connected, waiting for prompt_id: {prompt_id}")
                async for message in ws:
                    try:
                        if isinstance(message, str):
                            message_json = json.loads(message)
                            msg_type = message_json.get('type')
                            msg_data = message_json.get('data', {})
                            
                            # Get prompt_id from data or top level
                            msg_prompt_id = msg_data.get('prompt_id') or message_json.get('prompt_id')
                            
                            # Only process messages for our prompt_id
                            if msg_prompt_id and msg_prompt_id != prompt_id:
                                continue
                            
                            # Call progress callback if provided
                            if progress_callback:
                                try:
                                    progress_callback(message_json)
                                except Exception as e:
                                    logger.warning(f"Progress callback error: {e}")
                            
                            if msg_type == 'executing':
                                node = msg_data.get('node')
                                if node:
                                    logger.info(f"Executing node: {node}")
                                else:
                                    logger.info("Execution complete")
                                    # Execution is done, return the prompt_id so we can fetch results
                                    return prompt_id
                            
                            elif msg_type == 'progress':
                                value = msg_data.get('value', 0)
                                max_value = msg_data.get('max', 1)
                                logger.debug(f"Progress: {value}/{max_value}")
                            
                            elif msg_type == 'executed' and msg_data.get('output'):
                                node_id = msg_data.get('node')
                                if node_id:
                                    outputs[node_id] = msg_data['output']
                                    logger.debug(f"Node {node_id} executed with outputs")
                            
                            elif msg_type == 'execution_success':
                                logger.info("Job completed successfully!")
                                return prompt_id
                            
                            elif msg_type == 'execution_error':
                                exception_msg = msg_data.get('exception_message', 'Unknown error')
                                node_type = msg_data.get('node_type', '')
                                raise ValueError(f"Execution error in {node_type}: {exception_msg}")
                        else:
                            # Handle binary messages (preview images, etc.)
                            logger.debug("Received binary message")
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse WebSocket message: {e}")
                        continue
                    except KeyError as e:
                        logger.warning(f"Missing key in WebSocket message: {e}")
                        continue
                
                # If we exit the loop without returning, timeout or error occurred
                raise ValueError("WebSocket connection closed before completion")
        
        try:
            await asyncio.wait_for(_wait_for_completion_inner(), timeout=timeout)
            return prompt_id
        except asyncio.TimeoutError:
            raise TimeoutError(f"Job did not complete within {timeout}s")
                    
        except websockets.exceptions.WebSocketException as e:
            raise ValueError(f"WebSocket error: {str(e)}") from e

    def download_output(
        self,
        promptId: str,
        subfolder: str = "",
        output_type: str = "output",
        output_path: Optional[str] = None,
    ) -> List[str]:
        """
        Download an output file from ComfyUI Cloud.

        Args:
            filename: Name of the file to download
            subfolder: Subfolder path (usually empty for cloud)
            output_type: Type of output ("output" or "input")
            output_path: Optional local path to save the file

        Returns:
            Path to the downloaded file

        Raises:
            ValueError: If download fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/history_v2/{promptId}" 
        try:
            # Get redirect URL (don't follow to avoid sending auth to storage)
            headers = {"X-API-Key": self.api_key}
            logger.debug(f"Download output headers: X-API-Key present (length: {len(self.api_key)})")
            response = httpx.get(
                url,
                headers=headers,
                follow_redirects=False,
                timeout=30.0,
            )
            response.raise_for_status()
            # Use response.json() instead of json.loads(response.content) to avoid encoding issues
            history = response.json()
            if promptId not in history:
                raise ValueError(f"Prompt ID {promptId} not found in history")
            if 'outputs' not in history[promptId]:
                raise ValueError(f"No outputs found for prompt ID {promptId}")
            images_output = []
            for node_id, node_output in history[promptId]['outputs'].items():
                if 'images' in node_output:
                    for idx, image in enumerate(node_output['images']):
                        try:
                            data = {
                                "filename": image['filename'], 
                                "subfolder": image.get('subfolder', ''), 
                                "type": image.get('type', 'output')
                            }
                            url_values = urlencode(data)
                            view_url = f"{self.base_url}/api/view?{url_values}"
                            view_response = httpx.get(
                                view_url,
                                headers=headers,
                                follow_redirects=False,
                                timeout=30.0,
                            )

                            if view_response.status_code == 302:
                                signed_url = view_response.headers.get("location")
                                if not signed_url:
                                    raise ValueError("No redirect URL in response")
                                
                                # Fetch from signed URL without auth headers
                                file_response = httpx.get(signed_url, timeout=60.0)
                                file_response.raise_for_status()
                            
                                # Save file
                                if output_path:
                                    save_path = Path(output_path)
                                else:
                                    storage_dir = Path(__file__).parent.parent.parent / "storage" / "generated_images"
                                    storage_dir.mkdir(parents=True, exist_ok=True)
                                    # Use promptId and index to create unique filename
                                    if idx == 0:
                                        save_path = storage_dir / f"{promptId}.png"
                                    else:
                                        save_path = storage_dir / f"{promptId}_{idx}.png"
                                
                                save_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                with open(save_path, "wb") as f:
                                    f.write(file_response.content)
                                
                                logger.info(f"Downloaded output to {save_path}")
                                images_output.append(str(save_path))
                                
                            else:
                                logger.warning(f"Unexpected response status {view_response.status_code} for image download")
                        except Exception as e:
                            logger.error(f"Failed to download image {image.get('filename', 'unknown')}: {e}")
                            continue
            
            if not images_output:
                raise ValueError(f"No images found in outputs for prompt {promptId}")
            
            return images_output
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"Failed to download output: {error_detail}") from e

    def download_outputs(
        self,
        promptId: str,
        output_dir: Optional[str] = None,
    ) -> List[str]:
        """
        Download all output files from a completed workflow.

        Args:
            promptId: The prompt ID from wait_for_completion
            output_dir: Optional directory to save files (defaults to storage/generated_images)

        Returns:
            List of paths to downloaded files
        """
        # Use download_output to get the images
        try:
            images = self.download_output(
                promptId=promptId,
                output_path=None,  # Let it use default path
            )
            if isinstance(images, list):
                return [str(img) for img in images]
            elif isinstance(images, (str, Path)):
                return [str(images)]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to download outputs for prompt {promptId}: {e}")
            return []

    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[str]:
        """
        Execute a workflow end-to-end: submit, wait for completion, and download outputs.

        Args:
            workflow: ComfyUI workflow dictionary
            extra_data: Optional extra data (e.g., API keys for partner nodes)
            output_dir: Optional directory to save output files
            progress_callback: Optional callback for progress updates

        Returns:
            List of paths to downloaded output files

        Raises:
            ValueError: If execution fails
            TimeoutError: If workflow times out
        """
        # Submit workflow
        prompt_id = self.submit_workflow(workflow, extra_data=extra_data)
        logger.info(f"Workflow submitted with prompt_id: {prompt_id}")
        
        # Wait for completion - returns prompt_id when done
        completed_prompt_id = await self.wait_for_completion(
            prompt_id,
            progress_callback=progress_callback,
        )
        
        logger.info(f"Workflow completed, prompt_id: {completed_prompt_id}")
        
        # Download outputs using the prompt_id
        #downloaded_files = self.download_outputs(completed_prompt_id, output_dir=output_dir)
        #logger.info(f"Downloaded {len(downloaded_files)} output files")
        
        return prompt_id

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current queue status.

        Returns:
            Queue status information
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/queue"
        
        try:
            response = httpx.get(
                url,
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"Failed to get queue status: {error_detail}") from e

    def cancel_job(self, prompt_id: str) -> bool:
        """
        Cancel a queued job.

        Args:
            prompt_id: The prompt ID to cancel

        Returns:
            True if cancellation was successful
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/queue"
        payload = {"delete": [prompt_id]}
        
        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info(f"Job {prompt_id} cancelled")
            return True
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"Failed to cancel job: {error_detail}")
            return False

    def interrupt_current_execution(self) -> bool:
        """
        Interrupt the currently executing workflow.

        Returns:
            True if interruption was successful
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/interrupt"
        
        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info("Current execution interrupted")
            return True
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"Failed to interrupt execution: {error_detail}")
            return False

    def get_object_info(self) -> Dict[str, Any]:
        """
        Retrieve available node definitions from ComfyUI Cloud.

        Returns:
            Object info dictionary with node definitions
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key is required.")

        url = f"{self.base_url}/api/object_info"
        
        try:
            response = httpx.get(
                url,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to ComfyUI Cloud at {self.base_url}. "
            error_msg += f"Please check that COMFYUI_CLOUD_BASE_URL is set correctly. "
            error_msg += f"Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"Failed to get object info: {error_detail}") from e

