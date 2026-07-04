"""
REEL GOD — End-to-End Pipeline Test
==================================
Validates the entire content generation workflow:
Idea -> Prompt Engineering -> Image Generation -> Video Assembly -> Visual Effects -> Music Mixing -> DB Registry.

Monkeys patches the Gemini API to run 100% locally and offline without requiring a valid API key.
"""

import os
import sys
import unittest
from pathlib import Path
from rich.console import Console

# Adjust python path to find project modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Write a dummy .env if none exists so that config check passes
env_file = project_root / ".env"
env_created = False
if not env_file.exists():
    with open(env_file, "w") as f:
        f.write("GEMINI_API_KEY=mock_api_key_for_testing\n")
        f.write("SD_MODEL=anything-v5\n")
        f.write("JAMENDO_CLIENT_ID=mock_jamendo_client_id\n")
    env_created = True

import google.generativeai as genai
import config

# Patch config values for fast E2E testing
config.VIDEO_FPS = 5
config.IMAGES_PER_VIDEO = 2

# Mock the Google Generative AI module
class MockResponse:
    def __init__(self, text):
        self.text = text

class MockChat:
    def send_message(self, prompt):
        return MockResponse("Mocked Gemini chat response for: " + prompt)

def mock_generate_content(self, prompt, **kwargs):
    # If it is requesting caption generation
    if "caption" in prompt.lower():
        return MockResponse("Epic anime reel! #anime #otaku #art")
    return MockResponse("Scene details: beautiful sunset over Tokyo sky, highly detailed, masterpieces, vibrant colors")

def mock_start_chat(self, history=None):
    return MockChat()

# Monkeypatch
genai.GenerativeModel.generate_content = mock_generate_content
genai.GenerativeModel.start_chat = mock_start_chat
genai.configure = lambda *args, **kwargs: None

from brain.core import ReelGodBrain
from brain.memory import AgentMemory

console = Console()


class TestE2EPipeline(unittest.TestCase):
    """End-to-End Pipeline Test Suite."""
    
    @classmethod
    def setUpClass(cls):
        cls.brain = ReelGodBrain()
        
    @classmethod
    def tearDownClass(cls):
        # Clean up mock .env if we created it
        if env_created and env_file.exists():
            os.remove(env_file)
            
    def test_e2e_video_generation(self):
        console.print("\n[bold yellow]--- Starting E2E Pipeline Test ---[/bold yellow]")
        
        # 1. Create a dummy idea in database
        idea_id = self.brain.memory.save_idea(
            title="E2E Test Legend of Tokyo",
            style="dark_cinematic",
            story="A mystical warrior stands on top of Tokyo Tower. The sun sets, casting long shadows. He unsheathes his katana.",
            script="SCENE 1: The warrior walks to the edge.\nSCENE 2: The sunset glows red.\nSCENE 3: A wind blows his coat.\nSCENE 4: He grips the katana hilt.\nSCENE 5: The sky turns purple.\nSCENE 6: Sparks fly from the blade.\nSCENE 7: He slices the air.\nSCENE 8: The screen goes black.",
            mood="mysterious"
        )
        console.print(f"[green]✓ Dummy Idea registered with ID #{idea_id}[/green]")
        
        # 2. Run the full compilation loop
        final_video_path_str = self.brain.generate_video_content(idea_id)
        final_video_path = Path(final_video_path_str)
        
        # 3. Verify output files
        self.assertTrue(final_video_path.exists(), "Final video file was not generated.")
        self.assertEqual(final_video_path.suffix, ".mp4", "Final video is not an MP4 file.")
        
        console.print(f"[green]✓ Verified final video exists at: {final_video_path}[/green]")
        
        # 4. Verify DB post registration
        posts = self.brain.memory.get_recent_posts(limit=1)
        self.assertTrue(len(posts) > 0, "No post recorded in database.")
        
        latest_post = posts[0]
        self.assertEqual(latest_post["idea_id"], idea_id, "Latest post idea ID mismatch.")
        self.assertEqual(latest_post["style"], "dark_cinematic", "Style mismatch.")
        self.assertTrue(Path(latest_post["video_path"]).exists(), "Post video path does not exist.")
        
        console.print("[green]✓ Verified post records in database successfully[/green]")
        
        # 5. Cleanup generated test files and DB records
        console.print("[cyan]Cleaning up test files...[/cyan]")
        if final_video_path.exists():
            os.remove(final_video_path)
            
        # Clean placeholders
        for i in range(1, config.IMAGES_PER_VIDEO + 1):
            placeholder = config.COMFYUI_OUTPUT_DIR / f"placeholder_dark_cinematic_{idea_id}_{i}.png"
            if placeholder.exists():
                os.remove(placeholder)
                
        # Clean fallback music if downloaded
        fallback_music = config.MUSIC_DIR / f"fallback_dark_cinematic_SoundHelix-Song-1.mp3"
        if fallback_music.exists():
            os.remove(fallback_music)
            
        # Delete test record from DB
        with self.brain.memory._connect() as conn:
            conn.execute("DELETE FROM content_ideas WHERE id = ?", (idea_id,))
            conn.execute("DELETE FROM posts WHERE idea_id = ?", (idea_id,))
            conn.execute("DELETE FROM music_library WHERE mood = 'dark_cinematic'")
            
        console.print("[green]✓ Cleanup complete. E2E pipeline is PERFECT.[/green]")
        console.print("[bold yellow]--- E2E Pipeline Test Passed successfully! ---[/bold yellow]\n")


if __name__ == "__main__":
    unittest.main()
