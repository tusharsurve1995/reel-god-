"""
REEL GOD — Configuration
========================
Edit this file with your API keys and personal settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists (optional — you can also set keys directly here)
load_dotenv()

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MUSIC_DIR = DATA_DIR / "music_library"
CONTENT_DIR = DATA_DIR / "content_archive"
DB_PATH = DATA_DIR / "memory.db"
COMFYUI_OUTPUT_DIR = DATA_DIR / "comfyui_output"

# Auto-create required directories
for d in [DATA_DIR, MUSIC_DIR, CONTENT_DIR, COMFYUI_OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
#  API KEYS  (set in .env or paste here)
# ─────────────────────────────────────────────
# Get your FREE Gemini key at: https://aistudio.google.com → "Get API Key"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "PASTE_YOUR_KEY_HERE")

# Instagram Graph API (obtained after Meta App Review)
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

# Jamendo Music API (free at: https://devportal.jamendo.com)
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")

# ─────────────────────────────────────────────
#  AGENT SETTINGS
# ─────────────────────────────────────────────
AGENT_NAME = "REEL GOD"
AGENT_VERSION = "1.0.0"

# How often the agent checks for work (seconds)
AGENT_TICK_INTERVAL = 60 * 30  # Every 30 minutes

# Content generation schedule (24-hour format)
DAILY_PLANNING_HOUR = 8       # Agent plans content at 8:00 AM
DAILY_POSTING_HOURS = [9, 12, 18, 21]  # Post at 9AM, 12PM, 6PM, 9PM

# Number of content ideas to generate per planning session
IDEAS_PER_SESSION = 5

# ─────────────────────────────────────────────
#  COMFYUI SETTINGS
# ─────────────────────────────────────────────
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

# Default image model (change based on your VRAM)
# Options: "animagine-xl-4.0" (SDXL, 8GB+), "anything-v5" (SD1.5, 4GB+)
SD_MODEL = "animagine-xl-4.0"

# Image generation settings
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920   # 9:16 portrait for Reels
IMAGE_STEPS = 25
IMAGE_CFG_SCALE = 7.5
IMAGES_PER_VIDEO = 8  # Number of scenes per Reel

# ─────────────────────────────────────────────
#  VIDEO SETTINGS
# ─────────────────────────────────────────────
VIDEO_FPS = 30
VIDEO_DURATION_PER_IMAGE = 3.5  # Seconds each image is shown
VIDEO_RESOLUTION = (1080, 1920)  # 9:16 portrait
VIDEO_BITRATE = "8000k"
VIDEO_CODEC = "libx264"

# ─────────────────────────────────────────────
#  CONTENT STYLE SETTINGS
# ─────────────────────────────────────────────
# Default anime styles REEL GOD will cycle through
CONTENT_STYLES = [
    "dark_cinematic",   # Dark, moody, atmospheric (AoT, Berserk vibes)
    "emotional",        # Sad, bittersweet, touching (Your Lie in April)
    "epic_action",      # High-energy battles (Demon Slayer, Jujutsu Kaisen)
    "mystical",         # Fantasy, magical, otherworldly (Frieren, Mushishi)
    "motivational",     # Uplifting, powerful quotes with visuals
]

# Gemini model to use (gemini-2.5-flash is fastest & free)
GEMINI_MODEL = "gemini-2.5-flash"

# ─────────────────────────────────────────────
#  INSTAGRAM SETTINGS
# ─────────────────────────────────────────────
INSTAGRAM_USERNAME = ""       # Your Instagram @handle (without @)
POST_WATERMARK = True         # Add subtle watermark to all content
WATERMARK_TEXT = ""           # Leave blank to use @username

# Default hashtag groups (agent will add trend-based ones automatically)
BASE_HASHTAGS = [
    "#anime", "#animeart", "#animeedit", "#animevideo",
    "#animeworld", "#animelover", "#animefan", "#animelife",
    "#aianime", "#aiart", "#aianimeart"
]

MAX_HASHTAGS = 30  # Instagram limit

# ─────────────────────────────────────────────
#  DASHBOARD SETTINGS
# ─────────────────────────────────────────────
DASHBOARD_HOST = "0.0.0.0"

DASHBOARD_PORT = 5000
DASHBOARD_SECRET_KEY = "reel-god-secret-key-change-this"

# ─────────────────────────────────────────────
#  VALIDATION
# ─────────────────────────────────────────────
def validate():
    """Check if required configuration is set."""
    issues = []
    
    if GEMINI_API_KEY == "PASTE_YOUR_KEY_HERE" or not GEMINI_API_KEY:
        issues.append("❌ GEMINI_API_KEY not set — get it FREE at https://aistudio.google.com")
    
    return issues
