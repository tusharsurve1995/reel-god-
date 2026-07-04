"""
REEL GOD — Style Manager
==========================
Manages anime style presets and ComfyUI workflow templates.
Handles model switching and style-specific SD parameters.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

import config
from brain.personality import STYLE_DESCRIPTIONS

console = Console()


class StyleManager:
    """
    Manages content styles and their corresponding ComfyUI workflows.
    
    Responsibilities:
    - Store and retrieve ComfyUI workflow templates per style
    - Map styles to SD parameters (CFG, steps, sampler, etc.)
    - Handle model switching (Animagine XL vs Anything V5)
    - Provide style-specific configuration for generation
    """
    
    def __init__(self):
        self.style_descriptions = STYLE_DESCRIPTIONS
        self.current_model = config.SD_MODEL
        
        # Style-specific SD parameters
        self.style_parameters = {
            "dark_cinematic": {
                "cfg_scale": 8.0,
                "steps": 30,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 0.75,
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT
            },
            "emotional": {
                "cfg_scale": 7.0,
                "steps": 25,
                "sampler_name": "euler_a",
                "scheduler": "normal",
                "denoise": 0.70,
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT
            },
            "epic_action": {
                "cfg_scale": 9.0,
                "steps": 35,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 0.80,
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT
            },
            "mystical": {
                "cfg_scale": 7.5,
                "steps": 28,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 0.72,
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT
            },
            "motivational": {
                "cfg_scale": 8.5,
                "steps": 32,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 0.78,
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT
            }
        }
        
        # Model-specific configurations
        self.model_configs = {
            "animagine-xl-4.0": {
                "type": "sdxl",
                "recommended_resolution": (1024, 1024),
                "min_vram": 8,  # GB
                "clip_skip": 1,
                "vae": "default"
            },
            "anything-v5": {
                "type": "sd15",
                "recommended_resolution": (512, 768),
                "min_vram": 4,  # GB
                "clip_skip": 2,
                "vae": "vae-ft-mse-840000"
            }
        }
        
        # Workflow templates directory
        self.templates_dir = Path(__file__).parent / "workflows"
        self.templates_dir.mkdir(exist_ok=True)
        
        console.print("[dim]Style Manager initialized[/dim]")
        console.print(f"[dim]Current model: {self.current_model}[/dim]")
    
    def get_style_parameters(self, style: str) -> Dict[str, Any]:
        """
        Get SD generation parameters for a specific style.
        
        Args:
            style: Content style name
        
        Returns:
            Dict of generation parameters (cfg, steps, sampler, etc.)
        """
        params = self.style_parameters.get(style, self.style_parameters["dark_cinematic"])
        console.print(f"[dim]Style parameters for {style}: CFG={params['cfg_scale']}, Steps={params['steps']}[/dim]")
        return params
    
    def get_style_info(self, style: str) -> Dict[str, str]:
        """
        Get full style information including description and keywords.
        
        Args:
            style: Content style name
        
        Returns:
            Dict with style metadata
        """
        return self.style_descriptions.get(style, self.style_descriptions["dark_cinematic"])
    
    def get_available_styles(self) -> list:
        """
        Get list of all available content styles.
        """
        return list(self.style_descriptions.keys())
    
    def set_model(self, model_name: str) -> bool:
        """
        Switch the active SD model.
        
        Args:
            model_name: Model identifier (animagine-xl-4.0 or anything-v5)
        
        Returns:
            True if successful, False otherwise
        """
        if model_name not in self.model_configs:
            console.print(f"[red]Unknown model: {model_name}[/red]")
            return False
        
        self.current_model = model_name
        console.print(f"[green]Model switched to: {model_name}[/green]")
        return True
    
    def get_current_model(self) -> str:
        """
        Get the currently active model.
        """
        return self.current_model
    
    def get_model_config(self, model: str = None) -> Dict[str, Any]:
        """
        Get configuration for a specific model.
        
        Args:
            model: Model name (uses current model if None)
        
        Returns:
            Dict with model configuration
        """
        if model is None:
            model = self.current_model
        return self.model_configs.get(model, self.model_configs["animagine-xl-4.0"])
    
    def check_model_compatibility(self, style: str, model: str = None) -> bool:
        """
        Check if a style is compatible with a model.
        
        Args:
            style: Content style
            model: Model name (uses current if None)
        
        Returns:
            True if compatible, False otherwise
        """
        if model is None:
            model = self.current_model
        
        # All styles are compatible with all models in our setup
        # This is a placeholder for future compatibility logic
        return True
    
    def get_workflow_template(self, style: str) -> Optional[Dict[str, Any]]:
        """
        Load ComfyUI workflow template for a specific style.
        
        Args:
            style: Content style name
        
        Returns:
            Workflow JSON dict if found, None otherwise
        """
        # Security check: Prevent path traversal by validating the style name
        if style not in self.get_available_styles():
            console.print(f"[red]Security Error: Invalid or untrusted style name '{style}'[/red]")
            return self._get_default_workflow()
            
        template_path = self.templates_dir / f"{style}_workflow.json"
        
        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                console.print(f"[dim]Loaded workflow template: {style}_workflow.json[/dim]")
                return workflow
            except Exception as e:
                console.print(f"[red]Error loading workflow template: {e}[/red]")
                return None
        else:
            console.print(f"[yellow]Workflow template not found: {template_path}[/yellow]")
            console.print("[yellow]Using default workflow structure[/yellow]")
            return self._get_default_workflow()
    
    def _get_default_workflow(self) -> Dict[str, Any]:
        """
        Return a basic default workflow structure.
        This is a simplified template that can be enhanced later.
        """
        return {
            "1": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 0,
                    "steps": 25,
                    "cfg": 7.5,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 0.75,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "2": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["1", 0],
                    "vae": ["4", 2]
                }
            },
            "3": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["2", 0],
                    "filename_prefix": "REEL_GOD"
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": self.current_model
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": config.IMAGE_WIDTH,
                    "height": config.IMAGE_HEIGHT,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "",
                    "clip": ["4", 1]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "",
                    "clip": ["4", 1]
                }
            }
        }
    
    def save_workflow_template(self, style: str, workflow: Dict[str, Any]) -> bool:
        """
        Save a workflow template for a style.
        
        Args:
            style: Content style name
            workflow: Workflow JSON dict
        
        Returns:
            True if successful, False otherwise
        """
        # Security check: Prevent path traversal by validating the style name
        if style not in self.get_available_styles():
            console.print(f"[red]Security Error: Invalid or untrusted style name '{style}'[/red]")
            return False
            
        template_path = self.templates_dir / f"{style}_workflow.json"
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2)
            console.print(f"[green]Saved workflow template: {style}_workflow.json[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error saving workflow template: {e}[/red]")
            return False
    
    def apply_style_to_workflow(
        self,
        workflow: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """
        Apply style-specific parameters to a workflow.
        
        Args:
            workflow: Base workflow JSON
            style: Content style to apply
        
        Returns:
            Modified workflow with style parameters
        """
        params = self.get_style_parameters(style)
        modified = json.loads(json.dumps(workflow))  # Deep copy
        
        # Apply parameters to KSampler nodes
        for node_id, node_data in modified.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                
                if "cfg" in inputs:
                    inputs["cfg"] = params["cfg_scale"]
                if "steps" in inputs:
                    inputs["steps"] = params["steps"]
                if "sampler_name" in inputs:
                    inputs["sampler_name"] = params["sampler_name"]
                if "scheduler" in inputs:
                    inputs["scheduler"] = params["scheduler"]
                if "denoise" in inputs:
                    inputs["denoise"] = params["denoise"]
            
            # Apply resolution to EmptyLatentImage nodes
            if node_data.get("class_type") == "EmptyLatentImage":
                inputs = node_data.get("inputs", {})
                inputs["width"] = params["width"]
                inputs["height"] = params["height"]
        
        console.print(f"[dim]Applied style parameters: {style}[/dim]")
        return modified
    
    def get_recommended_settings(self, vram_gb: int) -> Dict[str, Any]:
        """
        Get recommended settings based on available VRAM.
        
        Args:
            vram_gb: Available VRAM in GB
        
        Returns:
            Dict with recommended model and settings
        """
        if vram_gb >= 8:
            return {
                "model": "animagine-xl-4.0",
                "resolution": (1024, 1024),
                "batch_size": 1,
                "reason": "High VRAM - use SDXL model for best quality"
            }
        elif vram_gb >= 4:
            return {
                "model": "anything-v5",
                "resolution": (512, 768),
                "batch_size": 1,
                "reason": "Medium VRAM - use SD 1.5 model"
            }
        else:
            return {
                "model": "anything-v5",
                "resolution": (512, 512),
                "batch_size": 1,
                "reason": "Low VRAM - use SD 1.5 with lower resolution"
            }
