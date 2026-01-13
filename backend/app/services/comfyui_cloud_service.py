"""Service for running workflows and downloading images from ComfyUI Cloud."""
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class ComfyUICloudService:
    """Service for running workflows and downloading images from ComfyUI Cloud."""

    def __init__(self) -> None:
        """Initialize the ComfyUI Cloud service."""
        self.base_url = settings.comfyui_cloud_base_url
        self.api_key = settings.comfyui_cloud_api_key
        self.timeout = settings.comfyui_cloud_timeout
        self.poll_interval = settings.comfyui_cloud_poll_interval
        
        if not self.api_key:
            logger.warning("ComfyUI Cloud API key not configured. Set COMFYUI_CLOUD_API_KEY environment variable.")
        
        # Create HTTP client with default headers
        # Note: httpx.Client follows redirects by default, but we set it explicitly
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            follow_redirects=True,  # Explicitly follow redirects for file downloads
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            } if self.api_key else {},
        )

    def submit_workflow(
        self,
        workflow: Dict,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a workflow to ComfyUI Cloud for execution.
        
        Args:
            workflow: ComfyUI workflow dictionary in API format (node IDs as keys)
            client_id: Optional client ID for tracking (auto-generated if not provided)
            
        Returns:
            Dictionary containing prompt_id (job ID) and other response data
            
        Raises:
            ValueError: If API key is not configured or workflow submission fails
            httpx.HTTPError: If HTTP request fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key not configured. Set COMFYUI_CLOUD_API_KEY environment variable.")
        
        if not client_id:
            client_id = str(uuid.uuid4())
        
        prompt_data = {
            "prompt": workflow,
            "client_id": client_id,
        }
        
        try:
            response = self.client.post(
                "/api/prompt",
                json=prompt_data,
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"ComfyUI Cloud API error ({response.status_code}): {error_detail}")
                logger.error(f"Workflow sent: {json.dumps(workflow, indent=2)}")
                raise ValueError(f"ComfyUI Cloud API error ({response.status_code}): {error_detail}")
            
            response.raise_for_status()
            result = response.json()
            
            # Check for errors in response
            if "error" in result:
                error_msg = result["error"]
                logger.error(f"ComfyUI Cloud workflow error: {error_msg}")
                raise ValueError(f"ComfyUI Cloud workflow error: {error_msg}")
            
            prompt_id = result.get("prompt_id")
            if not prompt_id:
                logger.error(f"Unexpected ComfyUI Cloud response: {result}")
                raise ValueError(f"ComfyUI Cloud did not return a prompt_id: {result}")
            
            logger.info(f"Submitted workflow to ComfyUI Cloud, prompt_id: {prompt_id}")
            return {
                "prompt_id": prompt_id,
                "client_id": client_id,
                "response": result,
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error submitting workflow to ComfyUI Cloud: {error_detail}")
            raise ValueError(f"ComfyUI Cloud HTTP error: {error_detail}") from e
        except Exception as e:
            logger.error(f"Failed to submit workflow to ComfyUI Cloud: {str(e)}", exc_info=True)
            raise

    def get_history_for_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get history for a specific prompt ID using the ComfyUI Cloud history_v2 endpoint.
        
        Uses the official history endpoint: GET /api/history_v2/{prompt_id}
        Reference: https://docs.comfy.org/api-reference/cloud/job/get-history-for-specific-prompt
        
        Args:
            prompt_id: The prompt ID (job ID) to retrieve history for
            
        Returns:
            Dictionary containing full history data for the prompt, including:
            - outputs: Dictionary of node outputs containing generated images
            - status: Execution status
            - prompt: The original prompt/workflow
            - etc.
            
        Raises:
            ValueError: If history retrieval fails or prompt not found
            httpx.HTTPError: If HTTP request fails
        """
        try:
            response = self.client.get(f"/api/history_v2/{prompt_id}")
            
            # Handle 404 - prompt/job not found
            if response.status_code == 404:
                raise ValueError(f"History not found for prompt_id: {prompt_id}")
            
            response.raise_for_status()
            history_data = response.json()
            
            # Response format: {prompt_id: {full_history_data}}
            if prompt_id in history_data:
                return history_data[prompt_id]
            elif history_data:
                # If response doesn't have prompt_id as key, use first entry
                first_key = next(iter(history_data.keys()))
                logger.warning(f"History response didn't contain expected prompt_id key, using {first_key}")
                return history_data[first_key]
            else:
                raise ValueError(f"Empty history response for prompt_id: {prompt_id}")
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error retrieving history for prompt {prompt_id}: {error_detail}")
            raise ValueError(f"Failed to retrieve history: {error_detail}") from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error retrieving history for prompt {prompt_id}: {str(e)}")
            raise ValueError(f"Failed to retrieve history: {str(e)}") from e

    def get_job_status(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get the status of a job using the ComfyUI Cloud job status API.
        
        Uses the official job status endpoint: GET /api/job/{job_id}/status
        Reference: https://docs.comfy.org/api-reference/cloud/job/get-job-status
        
        Args:
            prompt_id: The job ID (prompt_id) returned from submit_workflow
            
        Returns:
            Dictionary containing job status information:
            - id: Job ID (UUID)
            - status: "submitted", "preparing", "executing", "success", "error", "cancelled"
            - created_at: Job creation timestamp
            - updated_at: Job last update timestamp
            - last_state_update: When status last changed
            - assigned_inference: Inference instance assigned (if any)
            - error_message: Error message if status is "error"
            - history: Full history entry if completed (fetched separately when status is "success")
        """
        try:
            # Use the official job status endpoint
            response = self.client.get(f"/api/job/{prompt_id}/status")
            
            # Handle 404 - job not found
            if response.status_code == 404:
                return {
                    "id": prompt_id,
                    "status": "unknown",
                    "prompt_id": prompt_id,
                    "message": "Job not found",
                }
            
            response.raise_for_status()
            job_status = response.json()
            
            # Map the job status to a normalized format
            status = job_status.get("status", "unknown")
            
            result = {
                "id": job_status.get("id", prompt_id),
                "status": status,
                "prompt_id": prompt_id,
                "created_at": job_status.get("created_at"),
                "updated_at": job_status.get("updated_at"),
                "last_state_update": job_status.get("last_state_update"),
                "assigned_inference": job_status.get("assigned_inference"),
                "error_message": job_status.get("error_message"),
            }
            
            # If job is completed/successful, fetch history to get output information
            # Using history_v2 endpoint per ComfyUI Cloud API docs:
            # https://docs.comfy.org/api-reference/cloud/job/get-history-for-specific-prompt
            # Note: ComfyUI Cloud returns "success" status when job completes
            if status == "success":
                try:
                    history = self.get_history_for_prompt(prompt_id)
                    result["history"] = history
                except Exception as e:
                    logger.warning(f"Could not fetch history for completed job {prompt_id}: {str(e)}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error checking job status: {str(e)}")
            return {
                "id": prompt_id,
                "status": "error",
                "prompt_id": prompt_id,
                "error": str(e),
                "error_detail": e.response.text if e.response else None,
            }
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error checking job status: {str(e)}")
            return {
                "id": prompt_id,
                "status": "error",
                "prompt_id": prompt_id,
                "error": str(e),
            }

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Poll for job completion until finished or timeout.
        
        Args:
            prompt_id: The job ID to wait for
            timeout: Maximum time to wait in seconds (defaults to configured timeout)
            poll_interval: Time between polls in seconds (defaults to configured interval)
            
        Returns:
            Dictionary with job status and results if completed
            
        Raises:
            TimeoutError: If job doesn't complete within timeout
        """
        timeout = timeout or self.timeout
        poll_interval = poll_interval or self.poll_interval
        max_attempts = timeout // poll_interval
        
        logger.info(f"Waiting for job {prompt_id} to complete (timeout: {timeout}s, poll interval: {poll_interval}s)")
        
        for attempt in range(max_attempts):
            status_info = self.get_job_status(prompt_id)
            status = status_info.get("status")
            
            # Completed status (ComfyUI Cloud returns "success" when job completes)
            if status == "success":
                logger.info(f"Job {prompt_id} completed successfully")
                return status_info
            
            # Error or cancelled status
            elif status in ["error", "cancelled"]:
                error_msg = status_info.get("error_message") or status_info.get("error") or f"Job {status}"
                raise RuntimeError(f"Job {prompt_id} {status}: {error_msg}")
            
            # Job is still processing (waiting, pending, or in progress)
            elif status in ["preparing", "submitted", "executing"]:
                status_display = status.replace("_", " ").title()
                logger.debug(f"Job {prompt_id} is {status_display}, attempt {attempt + 1}/{max_attempts}")
                time.sleep(poll_interval)
            
            # Unknown or error status from API
            else:
                error_msg = status_info.get("error_message") or status_info.get("error")
                if error_msg:
                    raise RuntimeError(f"Job {prompt_id} has status '{status}': {error_msg}")
                # Wait and retry for unknown status
                logger.warning(f"Job {prompt_id} has unknown status: {status}, retrying...")
                time.sleep(poll_interval)
        
        # Final status check before timeout
        final_status = self.get_job_status(prompt_id)
        if final_status.get("status") == "success":
            logger.info(f"Job {prompt_id} completed on final check")
            return final_status
        
        raise TimeoutError(
            f"Job {prompt_id} did not complete within {timeout} seconds. "
            f"Last status: {final_status.get('status', 'unknown')}"
        )

    def download_output(
        self,
        filename: str,
        subfolder: str = "",
        output_type: str = "output",
        output_path: Optional[str] = None,
    ) -> str:
        """
        Download an output file from ComfyUI Cloud.
        
        Following the ComfyUI Cloud API documentation:
        https://docs.comfy.org/development/cloud/api-reference#downloading-outputs
        
        The /api/view endpoint returns a 302 redirect to a temporary signed URL.
        We need to:
        1. Make initial request with redirect: "manual" to get the signed URL
        2. Extract Location header from 302 response
        3. Fetch from signed URL WITHOUT auth headers (to avoid sending auth to storage)
        
        Args:
            filename: Name of the output file
            subfolder: Subfolder path (if any)
            output_type: Type of output ("output", "input", "temp")
            output_path: Optional local path to save the file (auto-generated if not provided)
            
        Returns:
            Path to the downloaded file
            
        Raises:
            ValueError: If download fails
        """
        # Build params - only include subfolder if it's not empty
        params = {
            "filename": filename,
            "type": output_type,
        }
        if subfolder:
            params["subfolder"] = subfolder
        
        try:
            # Step 1: Get redirect URL (don't follow to avoid sending auth to storage)
            # According to ComfyUI Cloud API docs, we should use redirect: "manual"
            view_url = f"{self.base_url}/api/view"
            logger.info(f"Getting signed URL for download: filename={filename}, type={output_type}, subfolder={subfolder or '(none)'}")
            
            # Make initial request without following redirects
            redirect_response = self.client.get(
                "/api/view",
                params=params,
                timeout=60.0,
                follow_redirects=False,  # Don't follow redirect - we'll handle it manually
            )
            
            # Check for errors on initial request
            if redirect_response.status_code >= 400:
                error_text = redirect_response.text if hasattr(redirect_response, 'text') else ""
                logger.error(
                    f"Failed to get signed URL: HTTP {redirect_response.status_code} - "
                    f"URL: {redirect_response.url}, Params: {params}, Response: {error_text[:500]}"
                )
                try:
                    error_json = redirect_response.json()
                    error_msg = error_json.get("error", error_json.get("message", str(error_json)))
                    raise ValueError(f"Failed to get signed URL: HTTP {redirect_response.status_code} - {error_msg}")
                except (ValueError, KeyError):
                    raise ValueError(
                        f"Failed to get signed URL: HTTP {redirect_response.status_code} - {error_text[:200] if error_text else 'No error message'}"
                    )
            
            # Step 2: Extract Location header from 302 redirect
            if redirect_response.status_code != 302:
                raise ValueError(
                    f"Expected 302 redirect, got HTTP {redirect_response.status_code}. "
                    f"Response: {redirect_response.text[:200] if redirect_response.text else 'No response body'}"
                )
            
            signed_url = redirect_response.headers.get("location")
            if not signed_url:
                raise ValueError(
                    f"302 redirect response missing Location header. "
                    f"Response headers: {dict(redirect_response.headers)}"
                )
            
            logger.debug(f"Got signed URL: {signed_url[:100]}...")
            
            # Step 3: Fetch from signed URL without auth headers
            # Create a new client without API key headers for the signed URL request
            # The signed URL already contains authentication in the URL itself
            logger.info(f"Downloading file from signed URL...")
            file_response = httpx.get(
                signed_url,
                timeout=60.0,
                follow_redirects=True,  # Signed URL might have additional redirects
            )
            
            file_response.raise_for_status()
            
            # Verify we got actual file content
            if not file_response.content:
                raise ValueError("Downloaded file is empty")
            
            content_type = file_response.headers.get("content-type", "")
            logger.debug(
                f"Downloaded file: Content-Type: {content_type}, "
                f"Size: {len(file_response.content)} bytes"
            )
            
            # Save the file
            if output_path:
                save_path = Path(output_path)
            else:
                storage_dir = Path(__file__).parent.parent.parent / "storage" / "generated_images"
                storage_dir.mkdir(parents=True, exist_ok=True)
                save_path = storage_dir / f"comfyui_cloud_{uuid.uuid4().hex[:8]}_{filename}"
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, "wb") as f:
                f.write(file_response.content)
            
            logger.info(f"Successfully downloaded output to {save_path} (size: {len(file_response.content)} bytes)")
            return str(save_path)
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            if e.response:
                status_code = e.response.status_code
                try:
                    error_text = e.response.text
                    if error_text:
                        error_detail = f"HTTP {status_code}: {error_text[:500]}"
                    else:
                        error_detail = f"HTTP {status_code}: (empty response body)"
                except Exception as parse_error:
                    error_detail = f"HTTP {status_code}: (could not read response: {str(parse_error)})"
            else:
                error_detail = f"HTTP error: {str(e)}"
            
            logger.error(
                f"HTTP error downloading output: {error_detail}, "
                f"Request URL: {self.base_url}/api/view, "
                f"Params: {params}"
            )
            raise ValueError(f"Failed to download output: {error_detail}") from e
        except httpx.HTTPError as e:
            error_detail = str(e) or f"{type(e).__name__} (no error message)"
            logger.error(
                f"HTTP error downloading output: {error_detail}, "
                f"Request URL: {self.base_url}/api/view, "
                f"Params: {params}"
            )
            raise ValueError(f"Failed to download output: {error_detail}") from e
        except Exception as e:
            error_detail = str(e) or f"{type(e).__name__} (no error message)"
            logger.error(
                f"Unexpected error downloading output: {type(e).__name__}: {error_detail}, "
                f"Params: {params}",
                exc_info=True
            )
            raise ValueError(f"Failed to download output: {type(e).__name__}: {error_detail}") from e

    def extract_outputs_from_history(self, history_entry: Dict) -> List[Dict[str, str]]:
        """
        Extract output file information from a history entry.
        
        Args:
            history_entry: History entry dictionary from get_history_for_prompt or get_job_status
            
        Returns:
            List of dictionaries with output file information:
            - filename: Name of the file
            - subfolder: Subfolder path
            - type: Output type ("output", "input", "temp")
            - node_id: ID of the node that produced this output
        """
        outputs = []
        
        if "outputs" not in history_entry:
            logger.debug("No 'outputs' key in history entry")
            return outputs
        
        for node_id, node_output in history_entry["outputs"].items():
            if "images" in node_output:
                for image_info in node_output["images"]:
                    outputs.append({
                        "filename": image_info["filename"],
                        "subfolder": image_info.get("subfolder", ""),
                        "type": image_info.get("type", "output"),
                        "node_id": node_id,
                    })
            
            # Also check for other output types (e.g., files, data)
            # Some nodes might output files in different formats
            if "files" in node_output:
                for file_info in node_output["files"]:
                    outputs.append({
                        "filename": file_info.get("filename") or file_info.get("name", ""),
                        "subfolder": file_info.get("subfolder", ""),
                        "type": file_info.get("type", "output"),
                        "node_id": node_id,
                    })
        
        return outputs

    def get_generated_images(self, prompt_id: str) -> List[Dict[str, str]]:
        """
        Get list of generated images for a completed prompt/job.
        
        This is a convenience method that fetches history and extracts image outputs.
        
        Args:
            prompt_id: The prompt ID (job ID) to retrieve images for
            
        Returns:
            List of dictionaries with image file information:
            - filename: Name of the image file
            - subfolder: Subfolder path
            - type: Output type
            - node_id: ID of the node that produced this image
            
        Raises:
            ValueError: If history retrieval fails or prompt not found
        """
        history = self.get_history_for_prompt(prompt_id)
        return self.extract_outputs_from_history(history)

    def run_workflow_and_download(
        self,
        workflow: Dict,
        output_path: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[str]:
        """
        Submit a workflow, wait for completion, and download all output images.
        
        This is a convenience method that combines submit, wait, and download.
        
        Args:
            workflow: ComfyUI workflow dictionary
            output_path: Optional base path for saving outputs (auto-generated if not provided)
            timeout: Optional timeout override
            
        Returns:
            List of paths to downloaded output files
            
        Raises:
            ValueError: If workflow submission or execution fails
            TimeoutError: If workflow doesn't complete within timeout
        """
        # Submit workflow
        submit_result = self.submit_workflow(workflow)
        prompt_id = submit_result["prompt_id"]
        
        # Wait for completion
        status_info = self.wait_for_completion(prompt_id, timeout=timeout)
        
        if status_info["status"] != "success":
            raise RuntimeError(f"Workflow did not complete successfully: {status_info}")
        
        # Extract output information
        # History should be fetched automatically when status is "success" in get_job_status
        # But if it's missing, try to fetch it explicitly
        if "history" not in status_info:
            logger.warning(f"History not found in status_info, fetching explicitly for {prompt_id}")
            try:
                status_info["history"] = self.get_history_for_prompt(prompt_id)
            except Exception as e:
                raise RuntimeError(
                    f"Workflow completed but could not retrieve history for {prompt_id}: {str(e)}"
                ) from e
        
        history_entry = status_info["history"]
        output_files = self.extract_outputs_from_history(history_entry)
        
        if not output_files:
            logger.warning(f"No output files found in completed workflow {prompt_id}")
            return []
        
        # Download all outputs
        downloaded_paths = []
        for i, output_info in enumerate(output_files):
            if output_path and len(output_files) == 1:
                # Single output, use provided path directly
                save_path = output_path
            elif output_path:
                # Multiple outputs, append index
                path_obj = Path(output_path)
                save_path = str(path_obj.parent / f"{path_obj.stem}_{i}{path_obj.suffix}")
            else:
                save_path = None
            
            try:
                downloaded_path = self.download_output(
                    filename=output_info["filename"],
                    subfolder=output_info["subfolder"],
                    output_type=output_info["type"],
                    output_path=save_path,
                )
                downloaded_paths.append(downloaded_path)
            except Exception as e:
                logger.error(f"Failed to download output {output_info['filename']}: {str(e)}")
                # Continue with other outputs even if one fails
        
        return downloaded_paths

    def upload_input(
        self,
        file_path: str,
        overwrite: bool = True,
    ) -> Dict[str, str]:
        """
        Upload an input file (image, mask, etc.) to ComfyUI Cloud.
        
        Args:
            file_path: Path to the file to upload
            overwrite: Whether to overwrite if file already exists
            
        Returns:
            Dictionary with upload result including filename
            
        Raises:
            ValueError: If upload fails
        """
        if not self.api_key:
            raise ValueError("ComfyUI Cloud API key not configured")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise ValueError(f"File not found: {file_path}")
        
        try:
            with open(file_path_obj, "rb") as f:
                files = {"image": (file_path_obj.name, f, "application/octet-stream")}
                data = {"overwrite": "true" if overwrite else "false"}
                
                response = self.client.post(
                    "/api/upload/image",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Uploaded file {file_path_obj.name} to ComfyUI Cloud")
                return result
                
        except httpx.HTTPError as e:
            error_detail = e.response.text if hasattr(e, "response") and e.response else str(e)
            logger.error(f"Failed to upload file: {error_detail}")
            raise ValueError(f"Failed to upload file: {error_detail}") from e

    def get_object_info(self) -> Dict:
        """
        Get information about available nodes and their definitions.
        
        Returns:
            Dictionary containing object/node information
        """
        try:
            response = self.client.get("/api/object_info")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get object info: {str(e)}")
            raise ValueError(f"Failed to get object info: {str(e)}") from e

    def get_user_info(self) -> Dict:
        """
        Get information about the authenticated user.
        
        Returns:
            Dictionary containing user information
        """
        try:
            response = self.client.get("/api/user")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise ValueError(f"Failed to get user info: {str(e)}") from e

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if hasattr(self, "client"):
            self.client.close()

