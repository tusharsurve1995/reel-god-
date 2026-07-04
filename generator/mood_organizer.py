"""
REEL GOD — Mood Organizer
=========================
Creates and manages the mood-based folder structure for content archive.
Each style/mood gets its own folder with organized metadata, thumbnails, and videos.
"""
import shutil, subprocess
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

import config

console = Console()

# ── MOOD FOLDER MAP ───────────────────────────────────────────────────────────
MOOD_FOLDERS = {
    "romantic":      "romantic",
    "romance":       "romantic",       # alias
    "emotional":     "emotional",
    "motivational":  "motivational",
    "sacrifice":     "sacrifice",
    "epic_action":   "epic_action",
    "dark_cinematic":"dark_cinematic",
    "mystical":      "mystical",
    "happy":         "happy",
}

# Emoji badges per mood for filenames and display
MOOD_EMOJI = {
    "romantic":      "💕",
    "emotional":     "💙",
    "motivational":  "🔥",
    "sacrifice":     "🗡️",
    "epic_action":   "⚔️",
    "dark_cinematic":"🌑",
    "mystical":      "✨",
    "happy":         "🌸",
}

MOOD_DISPLAY_NAMES = {
    "romantic":      "Love & Romance",
    "emotional":     "Emotional & Sad",
    "motivational":  "Motivational & Rise",
    "sacrifice":     "Sacrifice & Heroic",
    "epic_action":   "Epic Action",
    "dark_cinematic":"Dark Cinematic",
    "mystical":      "Mystical & Fantasy",
    "happy":         "Joy & Happiness",
}


class MoodOrganizer:
    """
    Manages the mood-based content archive folder structure.
    - Creates subdirectories per mood
    - Generates JPG thumbnails from videos
    - Returns organized paths for reel files
    """

    def __init__(self):
        self.archive_root = config.CONTENT_DIR
        self._create_mood_folders()

    def _create_mood_folders(self):
        """Create all mood subdirectories."""
        for mood in set(MOOD_FOLDERS.values()):
            folder = self.archive_root / mood
            folder.mkdir(parents=True, exist_ok=True)
        console.print("[dim]  Mood folder structure ready[/]")

    def get_mood_folder(self, style: str) -> Path:
        """Get the folder path for a given style/mood."""
        folder_name = MOOD_FOLDERS.get(style, style)
        folder = self.archive_root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_output_path(self, style: str, filename: str) -> Path:
        """Get full output path for a reel in the correct mood folder."""
        folder = self.get_mood_folder(style)
        return folder / filename

    def generate_thumbnail(self, video_path: Path, output_jpg: Path, seek_seconds: float = 3.0) -> Optional[Path]:
        """
        Extract a cover frame from the video at seek_seconds using FFmpeg.
        Returns path to thumbnail JPG, or None if FFmpeg not available.
        """
        try:
            ffmpeg = _find_ffmpeg()
            if not ffmpeg:
                console.print("[yellow]  FFmpeg not found — skipping thumbnail[/]")
                return None

            cmd = [
                ffmpeg,
                "-y",                          # Overwrite output
                "-ss", str(seek_seconds),      # Seek to timestamp
                "-i", str(video_path),         # Input video
                "-vframes", "1",               # Extract exactly 1 frame
                "-q:v", "2",                   # Quality 2 = near-lossless JPEG
                "-vf", "scale=1080:-1",        # Ensure 1080px width
                str(output_jpg),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and output_jpg.exists():
                console.print(f"  [green]✓ Thumbnail generated:[/] {output_jpg.name}")
                return output_jpg
            else:
                console.print(f"  [yellow]Thumbnail generation failed: {result.stderr.decode()[:100]}[/]")
                return None
        except Exception as e:
            console.print(f"  [yellow]Thumbnail error: {e}[/]")
            return None

    def clean_archive(self):
        """Delete all files in the content archive (fresh start)."""
        count = 0
        for f in self.archive_root.rglob("*"):
            if f.is_file():
                f.unlink(missing_ok=True)
                count += 1
        console.print(f"[dim]  Cleaned {count} files from content archive[/]")

    def list_reels_by_mood(self) -> Dict[str, list]:
        """Return a dict of mood → list of reel files."""
        result = {}
        for mood_folder in self.archive_root.iterdir():
            if mood_folder.is_dir():
                reels = list(mood_folder.glob("*.mp4"))
                if reels:
                    result[mood_folder.name] = reels
        return result

    def print_archive_summary(self):
        """Print a rich summary of what's in the archive."""
        from rich.table import Table
        from rich.panel import Panel

        t = Table(title="📁 Content Archive by Mood", border_style="cyan")
        t.add_column("Mood", style="bold")
        t.add_column("Emoji")
        t.add_column("Videos", justify="right")
        t.add_column("Files")

        total = 0
        for mood_name, folder_key in sorted(set(MOOD_FOLDERS.items()), key=lambda x: x[1]):
            folder = self.archive_root / folder_key
            if not folder.exists():
                continue
            videos = list(folder.glob("*.mp4"))
            if not videos:
                continue
            emoji = MOOD_EMOJI.get(folder_key, "🎬")
            display = MOOD_DISPLAY_NAMES.get(folder_key, folder_key)
            names = ", ".join(v.stem[:20] for v in videos[:3])
            if len(videos) > 3:
                names += f" +{len(videos)-3} more"
            t.add_row(display, emoji, str(len(videos)), names)
            total += len(videos)

        console.print(t)
        console.print(f"[bold green]Total reels ready: {total}[/]")


def _find_ffmpeg() -> Optional[str]:
    """Find FFmpeg binary."""
    import shutil as sh
    ff = sh.which("ffmpeg")
    if ff:
        return ff
    local = config.DATA_DIR / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
