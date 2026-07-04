"""
REEL GOD — Mood Analyzer
========================
Analyzes story scripts and content to determine the appropriate music mood.
Uses Gemini AI for intelligent mood detection and maps to anime content styles.
"""

from typing import Optional
from rich.console import Console
import sys
from pathlib import Path

# Ensure the project root is importable regardless of cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from brain.personality import STYLE_DESCRIPTIONS
from brain.core import ReelGodBrain

console = Console()


class MoodAnalyzer:
    """
    Analyzes content to determine the appropriate music mood.
    
    Responsibilities:
    - Analyze story scripts for emotional tone
    - Map content to music mood categories
    - Use Gemini AI for intelligent mood detection
    - Provide fallback mood mapping based on keywords
    """
    
    # Direct keyword-to-mood mapping for quick analysis
    KEYWORD_MOOD_MAP = {
        "dark_cinematic": [
            "dark", "shadow", "tragedy", "loss", "death", "war", "battle",
            "epic", "cinematic", "dramatic", "serious", "grim", "foreboding",
            "apocalypse", "doom", "destiny", "fate", "sacrifice"
        ],
        "emotional": [
            "love", "heart", "tears", "sad", "loss", "nostalgia", "memory",
            "gentle", "soft", "warm", "touching", "bittersweet", "farewell",
            "goodbye", "miss", "yearning", "longing", "beautiful", "tender"
        ],
        "epic_action": [
            "fight", "battle", "power", "energy", "action", "speed", "fire",
            "explosive", "intense", "clash", "combat", "strength", "force",
            "rush", "adrenaline", "victory", "triumph", "conquer", "defeat"
        ],
        "mystical": [
            "magic", "fantasy", "dream", "mystery", "wonder", "ethereal",
            "ancient", "legend", "myth", "spirit", "soul", "enchanted",
            "celestial", "cosmic", "otherworldly", "mystical", "arcane"
        ],
        "motivational": [
            "rise", "overcome", "strength", "determination", "hope", "believe",
            "inspire", "motivate", "achieve", "success", "goal", "dream",
            "never give up", "persevere", "courage", "brave", "powerful"
        ]
    }
    
    def __init__(self, brain: Optional[ReelGodBrain] = None):
        """
        Initialize the mood analyzer.
        
        Args:
            brain: Optional ReelGodBrain instance for AI-powered analysis.
                   If None, uses keyword-based fallback.
        """
        self.brain = brain
        console.print("[dim]Mood Analyzer initialized[/dim]")
        
    def analyze_mood(self, story_text: str, style_hint: Optional[str] = None) -> str:
        """
        Analyze story text to determine the appropriate music mood.
        
        Args:
            story_text: The story script or content description.
            style_hint: Optional style hint from content planner.
            
        Returns:
            Mood string matching one of the 5 anime styles.
        """
        # If style hint is provided and valid, use it directly
        if style_hint and style_hint in STYLE_DESCRIPTIONS:
            console.print(f"[cyan]Using style hint:[/] {style_hint}")
            return style_hint
        
        # Try AI-powered analysis if brain is available
        if self.brain:
            try:
                ai_mood = self._ai_analyze_mood(story_text)
                if ai_mood:
                    console.print(f"[green]AI-detected mood:[/] {ai_mood}")
                    return ai_mood
            except Exception as e:
                console.print(f"[yellow]AI mood analysis failed: {e}. Using keyword fallback.[/yellow]")
        
        # Fallback to keyword-based analysis
        return self._keyword_analyze_mood(story_text)
    
    def _ai_analyze_mood(self, story_text: str) -> Optional[str]:
        """
        Use Gemini AI to analyze the mood of the story.
        
        Args:
            story_text: The story script.
            
        Returns:
            Detected mood string or None if analysis fails.
        """
        prompt = f"""Analyze the emotional tone of this story script and return ONLY one of these 5 moods:
dark_cinematic, emotional, epic_action, mystical, motivational

Story: {story_text}

Return ONLY the mood name, nothing else."""
        
        try:
            response = self.brain.think_fresh(prompt)
            # Clean up the response
            mood = response.strip().lower()
            if mood in STYLE_DESCRIPTIONS:
                return mood
        except Exception as e:
            console.print(f"[red]AI analysis error: {e}[/red]")
        
        return None
    
    def _keyword_analyze_mood(self, story_text: str) -> str:
        """
        Analyze mood based on keyword matching.
        
        Args:
            story_text: The story script.
            
        Returns:
            Best-matching mood string.
        """
        text_lower = story_text.lower()
        scores = {}
        
        # Score each mood based on keyword matches
        for mood, keywords in self.KEYWORD_MOOD_MAP.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[mood] = score
        
        # Return mood with highest score, default to dark_cinematic
        best_mood = max(scores, key=scores.get)
        if scores[best_mood] == 0:
            console.print("[yellow]No mood keywords found. Defaulting to dark_cinematic.[/yellow]")
            return "dark_cinematic"
        
        console.print(f"[cyan]Keyword-detected mood:[/] {best_mood} (score: {scores[best_mood]})")
        return best_mood
    
    def get_music_mood_description(self, mood: str) -> str:
        """
        Get the music mood description for a given style.
        
        Args:
            mood: The mood/style string.
            
        Returns:
            Music mood description from STYLE_DESCRIPTIONS.
        """
        style_info = STYLE_DESCRIPTIONS.get(mood, STYLE_DESCRIPTIONS["dark_cinematic"])
        return style_info.get("music_mood", "cinematic")
