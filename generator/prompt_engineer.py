"""
REEL GOD — Prompt Engineer
============================
Converts story scripts into optimized Stable Diffusion prompts.
Uses Gemini AI for intelligent prompt crafting.
"""

import json
from typing import Dict, List, Optional
from rich.console import Console

import config
from brain.personality import STYLE_DESCRIPTIONS

console = Console()


class PromptEngineer:
    """
    Converts story scripts and content ideas into Stable Diffusion prompts.
    
    Responsibilities:
    - Parse story scripts into scene-by-scene prompts
    - Apply style-specific visual keywords from personality.py
    - Add quality-enhancing negative prompts
    - Use Gemini AI for intelligent prompt optimization
    - Ensure prompts are optimized for anime models (Animagine XL, Anything V5)
    """
    
    def __init__(self, brain=None):
        """
        Initialize prompt engineer.
        
        Args:
            brain: Optional ReelGodBrain instance for Gemini-powered prompt crafting
        """
        self.brain = brain
        self.style_descriptions = STYLE_DESCRIPTIONS
        
        # Quality negative prompts (what to avoid in anime generation)
        self.negative_prompts = [
            "blurry, low quality, distorted, deformed, ugly, bad anatomy",
            "bad hands, missing fingers, extra fingers, fused fingers",
            "bad eyes, crossed eyes, asymmetrical eyes",
            "text, watermark, signature, logo",
            "cropped, out of frame, cut off",
            "jpeg artifacts, compression artifacts, pixelated",
            "worst quality, low resolution, grainy",
            "mutation, mutated, disfigured",
            "bad proportions, long neck, bad body proportions",
            "oversaturated, washed out, dull colors"
        ]
        
        console.print("[dim]Prompt Engineer initialized[/dim]")
    
    def craft_prompt(
        self,
        story_scene: str,
        style: str = "dark_cinematic",
        use_ai: bool = True
    ) -> Dict[str, str]:
        """
        Craft an optimized SD prompt from a story scene description.
        
        Args:
            story_scene: The story scene text to convert
            style: Content style (dark_cinematic, emotional, epic_action, etc.)
            use_ai: Whether to use Gemini for intelligent crafting
        
        Returns:
            Dict with 'positive' and 'negative' prompts
        """
        # Get style-specific visual keywords
        style_info = self.style_descriptions.get(style, self.style_descriptions["dark_cinematic"])
        visual_keywords = style_info.get("visual_keywords", "")
        
        # Base prompt construction
        base_prompt = f"{story_scene}, {visual_keywords}"
        
        # Add anime-specific quality boosters
        quality_boosters = [
            "masterpiece, best quality, high resolution, highly detailed",
            "anime style, cel shading, clean lines, vibrant colors",
            "professional art, illustration, digital art",
            "4k, 8k, sharp focus, detailed background"
        ]
        
        positive_prompt = f"{base_prompt}, {', '.join(quality_boosters)}"
        
        # Use AI for intelligent optimization if brain is available
        if use_ai and self.brain:
            try:
                ai_prompt = self._ai_optimize_prompt(
                    story_scene, 
                    style, 
                    positive_prompt
                )
                if ai_prompt:
                    positive_prompt = ai_prompt
            except Exception as e:
                console.print(f"[yellow]AI optimization failed, using base prompt: {e}[/yellow]")
        
        # Construct negative prompt
        negative_prompt = ", ".join(self.negative_prompts)
        
        return {
            "positive": positive_prompt,
            "negative": negative_prompt,
            "style": style
        }
    
    def _ai_optimize_prompt(
        self,
        story_scene: str,
        style: str,
        base_prompt: str
    ) -> Optional[str]:
        """
        Use Gemini AI to optimize the prompt for better SD results.
        """
        if not self.brain:
            return None
        
        style_info = self.style_descriptions.get(style, {})
        style_desc = style_info.get("description", "")
        emotion = style_info.get("emotion", "")
        
        prompt = f"""
You are an expert Stable Diffusion prompt engineer specializing in anime art.

TASK: Optimize this prompt for high-quality anime image generation.

Story scene: {story_scene}
Content style: {style}
Style description: {style_desc}
Target emotion: {emotion}

Current base prompt: {base_prompt}

Your job:
1. Enhance the prompt with specific anime visual language
2. Add composition details (camera angle, lighting, framing)
3. Include character details if implied (expression, pose, clothing)
4. Add environmental details that match the mood
5. Ensure the prompt is optimized for anime models (Animagine XL / Anything V5)
6. Keep it under 200 words for best SD performance
7. Focus on visual elements only (no story text)

Return ONLY the optimized prompt, nothing else.
"""
        
        try:
            optimized = self.brain.think_fresh(prompt)
            if optimized and len(optimized) > 20:
                console.print("[dim]AI-optimized prompt generated[/dim]")
                return optimized.strip()
        except Exception as e:
            console.print(f"[yellow]AI prompt optimization error: {e}[/yellow]")
        
        return None
    
    def craft_scene_prompts(
        self,
        story_script: str,
        style: str = "dark_cinematic",
        scene_count: int = 8
    ) -> List[Dict[str, str]]:
        """
        Convert a full story script into scene-by-scene prompts.
        
        Args:
            story_script: Full story with multiple scenes
            style: Content style for all scenes
            scene_count: Number of scenes to generate
        
        Returns:
            List of prompt dicts (one per scene)
        """
        console.print(f"[dim]Crafting {scene_count} scene prompts...[/dim]")
        
        # Parse story into scenes (assuming script has scene markers or we split intelligently)
        scenes = self._parse_scenes(story_script, scene_count)
        
        prompts = []
        for i, scene in enumerate(scenes, 1):
            prompt_dict = self.craft_prompt(scene, style)
            prompt_dict["scene_number"] = i
            prompts.append(prompt_dict)
            console.print(f"[dim]  Scene {i}/{len(scenes)}: {scene[:50]}...[/dim]")
        
        return prompts
    
    def _parse_scenes(self, story_script: str, scene_count: int) -> List[str]:
        """
        Parse story script into individual scenes.
        This is a simple implementation - can be enhanced with AI parsing.
        """
        # Try to split by common scene markers
        scene_markers = ["SCENE", "Scene", "scene", "---", "•", "- "]
        
        scenes = []
        current_scene = ""
        
        lines = story_script.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a scene marker
            is_marker = any(marker in line for marker in scene_markers)
            
            if is_marker and current_scene:
                scenes.append(current_scene.strip())
                current_scene = line
            else:
                current_scene += " " + line
        
        if current_scene:
            scenes.append(current_scene.strip())
        
        # If no scene markers found, split by sentence count
        if len(scenes) <= 1:
            sentences = [s.strip() for s in story_script.split('.') if s.strip()]
            scenes_per_section = max(1, len(sentences) // scene_count)
            scenes = []
            for i in range(0, len(sentences), scenes_per_section):
                scene = '. '.join(sentences[i:i+scenes_per_section])
                scenes.append(scene)
        
        # Ensure we have exactly scene_count scenes
        while len(scenes) < scene_count:
            # Duplicate last scene or add variation
            if scenes:
                scenes.append(scenes[-1])
            else:
                scenes.append(story_script)
        
        return scenes[:scene_count]
    
    def enhance_for_model(
        self,
        prompt: str,
        model: str = "animagine-xl-4.0"
    ) -> str:
        """
        Enhance prompt for specific SD model.
        Different models respond better to different prompt structures.
        """
        if model == "animagine-xl-4.0":
            # SDXL models prefer natural language
            enhancers = [
                "detailed anime illustration",
                "vibrant anime art style",
                "high quality anime artwork"
            ]
            return f"{prompt}, {', '.join(enhancers)}"
        
        elif model == "anything-v5":
            # SD 1.5 models prefer tag-based prompts
            enhancers = [
                "anime, masterpiece, best quality",
                "1girl, solo, detailed",
                "highly detailed, beautiful"
            ]
            return f"{prompt}, {', '.join(enhancers)}"
        
        else:
            # Default enhancement
            return f"{prompt}, high quality anime art"
    
    def get_style_prompt_suggestions(self, style: str) -> Dict[str, str]:
        """
        Get prompt suggestions for a specific style.
        Useful for manual prompt crafting or debugging.
        """
        style_info = self.style_descriptions.get(style, {})
        
        return {
            "style": style,
            "visual_keywords": style_info.get("visual_keywords", ""),
            "music_mood": style_info.get("music_mood", ""),
            "emotion": style_info.get("emotion", ""),
            "suggested_positive": f"{style_info.get('visual_keywords', '')}, masterpiece, best quality, anime style",
            "suggested_negative": ", ".join(self.negative_prompts)
        }
