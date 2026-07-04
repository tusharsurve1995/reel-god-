"""
REEL GOD — ComfyUI Client
==========================
HTTP API wrapper for ComfyUI (Stable Diffusion interface).
Connects to localhost:8188 for image generation.
"""

import json
import time
import uuid
import requests
import websocket
from pathlib import Path
from typing import Optional, Dict, List, Any
from rich.console import Console

import config

console = Console()


class ComfyUIClient:
    """
    Client for interacting with ComfyUI's HTTP API and WebSocket.
    
    Responsibilities:
    - Queue generation jobs via POST /prompt
    - Monitor progress via WebSocket
    - Retrieve generated images via GET /view
    - Upload images for img2img via POST /upload/image
    - Load and modify workflow JSON templates
    """
    
    def __init__(self):
        self.base_url = config.COMFYUI_URL
        self.host = config.COMFYUI_HOST
        self.port = config.COMFYUI_PORT
        self.client_id = str(uuid.uuid4())
        self._connected = False
        
        console.print(
            f"[dim]ComfyUI Client initialized → {self.base_url}[/dim]"
        )
    
    def check_connection(self) -> bool:
        """
        Check if ComfyUI server is running and accessible.
        Returns True if connection successful, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            if response.status_code == 200:
                self._connected = True
                console.print("[green]✓ ComfyUI server connected[/green]")
                return True
        except Exception as e:
            console.print(f"[red]✗ ComfyUI connection failed: {e}[/red]")
            console.print(
                "[yellow]Ensure ComfyUI is running at "
                f"{self.base_url}[/yellow]"
            )
            self._connected = False
            return False
    
    def _load_workflow_template(self, template_path: str) -> Dict[str, Any]:
        """
        Load a ComfyUI workflow JSON template from file.
        """
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                console.print(f"[red]Workflow template not found: {template_path}[/red]")
                return {}
            
            with open(template_file, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            console.print(f"[dim]Loaded workflow template: {template_path}[/dim]")
            return workflow
        except Exception as e:
            console.print(f"[red]Error loading workflow template: {e}[/red]")
            return {}
    
    def _modify_workflow_prompt(
        self, 
        workflow: Dict[str, Any], 
        prompt_text: str,
        negative_prompt: str = "",
        seed: int = -1
    ) -> Dict[str, Any]:
        """
        Modify workflow JSON with custom prompt, negative prompt, and seed.
        Searches for KSampler and CLIPTextEncode nodes to modify.
        """
        modified = json.loads(json.dumps(workflow))  # Deep copy
        
        for node_id, node_data in modified.items():
            # Modify positive prompt (CLIP Text Encode node)
            if node_data.get("class_type") == "CLIPTextEncode":
                if "text" in node_data.get("inputs", {}):
                    # Check if this is the positive prompt (usually has "positive" in inputs)
                    inputs = node_data.get("inputs", {})
                    if "text" in inputs and negative_prompt not in inputs.get("text", ""):
                        inputs["text"] = prompt_text
            
            # Modify negative prompt
            if node_data.get("class_type") == "CLIPTextEncode":
                inputs = node_data.get("inputs", {})
                if "text" in inputs and negative_prompt:
                    # If this looks like a negative prompt slot
                    if "negative" in str(inputs).lower() or "clip" in str(inputs).lower():
                        inputs["text"] = negative_prompt
            
            # Modify seed in KSampler
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                if "seed" in inputs:
                    inputs["seed"] = seed if seed > 0 else int(time.time() * 1000) % 1000000000
        
        return modified
    
    def queue_prompt(
        self,
        workflow: Dict[str, Any],
        prompt_text: str,
        negative_prompt: str = "",
        seed: int = -1
    ) -> Optional[str]:
        """
        Queue a generation job in ComfyUI.
        
        Args:
            workflow: ComfyUI workflow JSON template
            prompt_text: Positive prompt for generation
            negative_prompt: Negative prompt (what to avoid)
            seed: Random seed (-1 for random)
        
        Returns:
            prompt_id if successful, None otherwise
        """
        if not self._connected and not self.check_connection():
            return None
        
        try:
            # Modify workflow with our parameters
            modified_workflow = self._modify_workflow_prompt(
                workflow, prompt_text, negative_prompt, seed
            )
            
            # Prepare the prompt payload
            payload = {
                "prompt": modified_workflow,
                "client_id": self.client_id
            }
            
            # Queue the prompt
            response = requests.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                console.print(f"[green]✓ Job queued: {prompt_id}[/green]")
                return prompt_id
            else:
                console.print(
                    f"[red]Failed to queue prompt: {response.status_code}[/red]"
                )
                return None
                
        except Exception as e:
            console.print(f"[red]Error queueing prompt: {e}[/red]")
            return None
    
    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the history/status of a queued prompt.
        
        Args:
            prompt_id: The prompt ID returned from queue_prompt()
        
        Returns:
            History dict if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                console.print(
                    f"[red]Failed to get history: {response.status_code}[/red]"
                )
                return None
                
        except Exception as e:
            console.print(f"[red]Error getting history: {e}[/red]")
            return None
    
    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: int = 300,
        progress_callback = None
    ) -> bool:
        """
        Wait for a prompt to complete generation.
        
        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum seconds to wait
            progress_callback: Optional function to call with progress updates
        
        Returns:
            True if completed successfully, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            
            if history and prompt_id in history:
                prompt_data = history[prompt_id]
                status = prompt_data.get("status", {})
                
                # Check if completed
                if status.get("completed", False):
                    console.print(f"[green]✓ Generation completed: {prompt_id}[/green]")
                    return True
                
                # Report progress if callback provided
                if progress_callback:
                    progress = status.get("progress", {})
                    value = progress.get("value", 0)
                    max_value = progress.get("max", 1)
                    progress_callback(value, max_value)
            
            time.sleep(1)
        
        console.print(f"[red]Timeout waiting for prompt: {prompt_id}[/red]")
        return False
    
    def get_output_images(self, prompt_id: str) -> List[str]:
        """
        Retrieve output image filenames for a completed prompt.
        
        Args:
            prompt_id: The completed prompt ID
        
        Returns:
            List of image filenames
        """
        try:
            history = self.get_history(prompt_id)
            
            if not history or prompt_id not in history:
                console.print(f"[red]No history found for prompt: {prompt_id}[/red]")
                return []
            
            prompt_data = history[prompt_id]
            outputs = prompt_data.get("outputs", {})
            
            image_filenames = []
            
            # Extract image filenames from outputs
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for image_info in node_output["images"]:
                        filename = image_info.get("filename")
                        if filename:
                            image_filenames.append(filename)
                            console.print(f"[dim]Found output: {filename}[/dim]")
            
            return image_filenames
            
        except Exception as e:
            console.print(f"[red]Error getting output images: {e}[/red]")
            return []
    
    def download_image(self, filename: str, save_path: Path) -> bool:
        """
        Download an image from ComfyUI's /view endpoint.
        
        Args:
            filename: The image filename (from get_output_images)
            save_path: Where to save the image locally
        
        Returns:
            True if successful, False otherwise
        """
        # Security check: Prevent directory traversal
        if not filename or "/" in filename or "\\" in filename or filename.startswith(".."):
            console.print(f"[red]Security Error: Invalid image filename '{filename}'[/red]")
            return False
            
        try:
            url = f"{self.base_url}/view?filename={filename}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                console.print(f"[green]✓ Downloaded: {save_path.name}[/green]")
                return True
            else:
                console.print(
                    f"[red]Failed to download image: {response.status_code}[/red]"
                )
                return False
                
        except Exception as e:
            console.print(f"[red]Error downloading image: {e}[/red]")
            return False
    
    def upload_image(self, image_path: Path, overwrite: bool = True) -> Optional[str]:
        """
        Upload an image to ComfyUI for img2img workflows.
        
        Args:
            image_path: Path to the image to upload
            overwrite: Whether to overwrite if exists
        
        Returns:
            Filename if successful, None otherwise
        """
        try:
            if not image_path.exists():
                console.print(f"[red]Image not found: {image_path}[/red]")
                return None
            
            with open(image_path, 'rb') as f:
                files = {"image": (image_path.name, f, "image/png")}
                data = {"overwrite": str(overwrite).lower()}
                
                response = requests.post(
                    f"{self.base_url}/upload/image",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    filename = result.get("name")
                    console.print(f"[green]✓ Uploaded: {filename}[/green]")
                    return filename
                else:
                    console.print(
                        f"[red]Failed to upload image: {response.status_code}[/red]"
                    )
                    return None
                    
        except Exception as e:
            console.print(f"[red]Error uploading image: {e}[/red]")
            return None
    
    def generate_image(
        self,
        workflow: Dict[str, Any],
        prompt_text: str,
        negative_prompt: str = "",
        seed: int = -1,
        output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Complete workflow: queue, wait, download.
        
        Args:
            workflow: ComfyUI workflow JSON template
            prompt_text: Positive prompt
            negative_prompt: Negative prompt
            seed: Random seed
            output_dir: Where to save the image (defaults to config.COMFYUI_OUTPUT_DIR)
        
        Returns:
            Path to downloaded image if successful, None otherwise
        """
        if output_dir is None:
            output_dir = config.COMFYUI_OUTPUT_DIR
        
        # Queue the prompt
        prompt_id = self.queue_prompt(workflow, prompt_text, negative_prompt, seed)
        if not prompt_id:
            return None
        
        # Wait for completion
        if not self.wait_for_completion(prompt_id):
            return None
        
        # Get output filenames
        image_filenames = self.get_output_images(prompt_id)
        if not image_filenames:
            return None
        
        # Download the first image
        filename = image_filenames[0]
        
        # Security check: Prevent directory traversal
        if not filename or "/" in filename or "\\" in filename or filename.startswith(".."):
            console.print(f"[red]Security Error: Invalid image filename '{filename}'[/red]")
            return None
            
        save_path = output_dir / filename
        
        if self.download_image(filename, save_path):
            return save_path
        
        return None
