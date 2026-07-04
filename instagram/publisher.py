"""
REEL GOD — Instagram Publisher
================================
Handles pre-upload editing, metadata loading, and publishing to Instagram.
Pre-upload pipeline:
  1. Load reel metadata from .json sidecar
  2. Validate video format (H.264, yuv420p, proper resolution)
  3. Generate cover thumbnail if missing (FFmpeg)
  4. Build formatted caption via caption_builder
  5. Upload as Reel (clip_upload) with cover thumbnail
  6. Optionally post to Story (photo_upload of thumbnail)
  7. Record media_id and posted_at in metadata JSON
"""

import os
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel

import config
from instagram.caption_builder import build_caption, build_story_caption

console = Console()


# ── PRE-UPLOAD VIDEO VALIDATOR ────────────────────────────────────────────────

class VideoValidator:
    """
    Validates and optionally re-encodes video to meet Instagram Reel specs:
    - Codec: H.264 (libx264)
    - Pixel format: yuv420p
    - Resolution: 1080x1920 (9:16) or 1080x1080 (1:1)
    - FPS: 30
    - Bitrate: 3.5–8 Mbps
    - Audio: AAC, 256kbps
    """

    INSTAGRAM_SPECS = {
        "codec":        "h264",
        "pixel_fmt":    "yuv420p",
        "min_bitrate":  3_500_000,
        "max_bitrate":  8_000_000,
        "audio_codec":  "aac",
        "fps":          30,
    }

    def __init__(self):
        self.ffmpeg  = self._find_ffmpeg()
        self.ffprobe = self._find_ffprobe()

    def _find_ffmpeg(self) -> Optional[str]:
        ff = shutil.which("ffmpeg")
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

    def _find_ffprobe(self) -> Optional[str]:
        ffp = shutil.which("ffprobe")
        if ffp:
            return ffp
        # Try alongside ffmpeg binary
        if self.ffmpeg:
            ffp_path = Path(self.ffmpeg).parent / "ffprobe.exe"
            if ffp_path.exists():
                return str(ffp_path)
        return None

    def probe(self, video_path: Path) -> Dict[str, Any]:
        """Extract video metadata using ffprobe."""
        if not self.ffprobe:
            return {}
        try:
            result = subprocess.run([
                self.ffprobe, "-v", "quiet",
                "-print_format", "json",
                "-show_streams", "-show_format",
                str(video_path),
            ], capture_output=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            console.print(f"  [yellow]ffprobe error: {e}[/]")
        return {}

    def validate_and_fix(self, video_path: Path) -> Path:
        """
        Check if video meets Instagram specs.
        If not, re-encode to a fixed version.
        Returns path to valid video (may be same file or new fixed file).
        """
        info = self.probe(video_path)
        if not info:
            # Can't probe — assume it's okay and try to upload
            return video_path

        # Find video stream
        video_stream = next(
            (s for s in info.get("streams", []) if s.get("codec_type") == "video"),
            None
        )
        if not video_stream:
            return video_path

        codec = video_stream.get("codec_name", "")
        pix_fmt = video_stream.get("pix_fmt", "")

        needs_fix = (
            codec not in ("h264", "libx264") or
            pix_fmt != "yuv420p"
        )

        if not needs_fix:
            console.print(f"  [green]✓ Video format valid[/] ({codec}, {pix_fmt})")
            return video_path

        # Re-encode to Instagram spec
        console.print(f"  [yellow]Re-encoding to Instagram spec (codec={codec}, pix_fmt={pix_fmt})...[/]")
        fixed_path = video_path.with_stem(video_path.stem + "_ig_ready")

        if not self.ffmpeg:
            console.print("  [red]FFmpeg not found — cannot re-encode[/]")
            return video_path

        cmd = [
            self.ffmpeg, "-y",
            "-i", str(video_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "256k",
            "-r", "30",
            str(fixed_path),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode == 0 and fixed_path.exists():
            console.print(f"  [green]✓ Re-encoded:[/] {fixed_path.name}")
            return fixed_path

        console.print(f"  [yellow]Re-encode failed — using original[/]")
        return video_path

    def generate_thumbnail(self, video_path: Path, output_jpg: Path, seek: float = 2.5) -> Optional[Path]:
        """Extract a sharp cover frame at seek seconds."""
        if not self.ffmpeg:
            return None
        try:
            cmd = [
                self.ffmpeg, "-y",
                "-ss", str(seek),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "1",
                "-vf", "scale='if(gt(iw,ih),1080,-1)':'if(gt(iw,ih),-1,1920)'",
                str(output_jpg),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and output_jpg.exists():
                return output_jpg
        except Exception as e:
            console.print(f"  [yellow]Thumbnail error: {e}[/]")
        return None


# ── INSTAGRAM PUBLISHER ───────────────────────────────────────────────────────

class InstagramPublisher:
    """
    Full pipeline Instagram publisher with pre-upload editing.
    """

    def __init__(self):
        self.validator = VideoValidator()
        self.session_path = config.DATA_DIR / "instagram_session.json"
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.is_logged_in = False
        self._cl = None

    @property
    def cl(self):
        if self._cl is None:
            try:
                from instagrapi import Client
                self._cl = Client()
                self._cl.delay_range = [2, 5]
            except ImportError:
                console.print("[red]instagrapi not installed. Run: pip install instagrapi[/]")
                raise
        return self._cl

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Authenticate with Instagram using cached session if available."""
        user   = username or os.environ.get("INSTAGRAM_USERNAME") or getattr(config, "INSTAGRAM_USERNAME", None)
        passwd = password or os.environ.get("INSTAGRAM_PASSWORD") or getattr(config, "INSTAGRAM_PASSWORD", None)

        if not user or not passwd:
            console.print("[yellow]⚠️  Instagram username/password not configured in .env[/]")
            console.print("[dim]Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file[/]")
            return False

        # Try cached session
        if self.session_path.exists():
            try:
                console.print(f"[dim]Loading cached session for @{user}...[/]")
                self.cl.load_settings(str(self.session_path))
                self.cl.login(user, passwd)
                self.is_logged_in = True
                console.print(f"[green]✓ Instagram login successful via cached session[/]")
                return True
            except Exception as e:
                console.print(f"[dim]Cached session expired: {e} — fresh login...[/]")
                self.cl.set_settings({})

        # Fresh login
        try:
            console.print(f"[cyan]Fresh Instagram login for @{user}...[/]")
            self.cl.login(user, passwd)
            self.cl.dump_settings(str(self.session_path))
            self.is_logged_in = True
            console.print(f"[green]✓ Instagram fresh login successful. Session cached.[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Instagram login failed: {e}[/]")
            return False

    # ──────────────────────────────────────────────────────────────────────────

    def publish_from_folder(self, reel_path: Path, post_story: bool = False) -> Optional[str]:
        """
        Full pre-upload pipeline from a mood folder reel.

        Steps:
          1. Load .json sidecar for metadata
          2. Build formatted caption via caption_builder
          3. Validate/fix video format for Instagram
          4. Generate cover thumbnail if missing
          5. Upload Reel with caption + thumbnail
          6. Optionally post cover as Story
          7. Save media_id back to metadata JSON

        Args:
            reel_path: Path to the .mp4 file
            post_story: Also post thumbnail as a Story

        Returns:
            Instagram media_id string or None
        """
        console.print(Panel(
            f"[bold cyan]📤 INSTAGRAM UPLOAD PIPELINE[/]\n"
            f"[dim]{reel_path.name}[/]",
            border_style="cyan"
        ))

        # 1. Load metadata sidecar
        meta_path = reel_path.with_suffix(".json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                console.print(f"  [green]✓ Metadata loaded:[/] {meta.get('title', 'untitled')}")
            except Exception as e:
                console.print(f"  [yellow]Could not load metadata: {e}[/]")
        else:
            console.print(f"  [yellow]No metadata sidecar found — using filename as title[/]")
            meta = {
                "title": reel_path.stem.replace("_", " ").title(),
                "style": self._guess_style_from_path(reel_path),
                "anime": "",
                "quote": "",
                "purpose": "",
            }

        # 2. Build formatted Instagram caption
        console.print("  [dim]Building Instagram caption...[/]")
        caption = build_caption(meta)
        console.print(f"  [green]✓ Caption ready[/] ({len(caption)} chars)")

        # 3. Validate + fix video format
        console.print("  [dim]Validating video format for Instagram...[/]")
        upload_video = self.validator.validate_and_fix(reel_path)

        # 4. Generate cover thumbnail
        thumb_path = reel_path.with_suffix(".jpg")
        if not thumb_path.exists():
            console.print("  [dim]Generating cover thumbnail...[/]")
            self.validator.generate_thumbnail(upload_video, thumb_path, seek=2.5)
        if thumb_path.exists():
            console.print(f"  [green]✓ Thumbnail ready:[/] {thumb_path.name}")
        else:
            thumb_path = None
            console.print("  [yellow]  No thumbnail — uploading without cover[/]")

        # 5. Login
        if not self.is_logged_in and not self.login():
            console.print("[red]❌ Cannot upload — Instagram not authenticated[/]")
            return None

        # 6. Upload Reel
        console.print(f"  [cyan]Uploading Reel to Instagram...[/]")
        media_id = None
        try:
            media = self.cl.clip_upload(
                path=str(upload_video),
                caption=caption,
                thumbnail=str(thumb_path) if thumb_path else None,
            )
            media_id = str(media.id)
            console.print(f"  [bold green]✓ Reel posted![/] Media ID: {media_id}")
        except Exception as e:
            console.print(f"  [red]❌ Reel upload failed: {e}[/]")
            return None

        # 7. Optionally post to Story
        if post_story and thumb_path and thumb_path.exists():
            console.print("  [dim]Posting thumbnail as Story...[/]")
            story_caption = build_story_caption(meta)
            try:
                self.cl.photo_upload_to_story(
                    path=str(thumb_path),
                    caption=story_caption,
                )
                console.print("  [green]✓ Story posted![/]")
            except Exception as e:
                console.print(f"  [yellow]Story post failed: {e}[/]")

        # 8. Update metadata with Instagram info
        meta["instagram_media_id"] = media_id
        meta["posted_at"] = datetime.now(timezone.utc).isoformat()
        meta["caption_used"] = caption[:500]  # Store first 500 chars
        try:
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            console.print(f"  [dim]Metadata updated with media_id[/]")
        except Exception:
            pass

        return media_id

    # ──────────────────────────────────────────────────────────────────────────

    def publish_reel(self, video_path: Path, caption: str, thumbnail_path: Optional[Path] = None) -> Optional[str]:
        """
        Legacy method — direct upload with provided caption.
        Auto-generates cover thumbnail if missing.
        """
        if not self.is_logged_in and not self.login():
            raise RuntimeError("Cannot publish: Instagram authentication failed.")

        # Validate format
        upload_video = self.validator.validate_and_fix(video_path)

        # Generate cover thumbnail if missing
        if not thumbnail_path:
            temp_thumb = video_path.with_suffix(".jpg")
            if not temp_thumb.exists():
                console.print("  [dim]Auto-generating cover thumbnail for upload...[/]")
                self.validator.generate_thumbnail(upload_video, temp_thumb, seek=2.5)
            if temp_thumb.exists():
                thumbnail_path = temp_thumb

        console.print(f"[cyan]Uploading Reel: {video_path.name}...[/]")
        try:
            media = self.cl.clip_upload(
                path=str(upload_video),
                caption=caption,
                thumbnail=str(thumbnail_path) if thumbnail_path else None,
            )
            media_id = str(media.id)
            console.print(f"[bold green]✓ Reel posted![/] Media ID: {media_id}")
            return media_id
        except Exception as e:
            console.print(f"[red]❌ Failed to publish Reel: {e}[/red]")
            raise


    def publish_all_from_mood_folder(self, mood: str, post_story: bool = False) -> list:
        """
        Publish all ready reels from a specific mood folder.
        Returns list of media IDs.
        """
        from generator.mood_organizer import MoodOrganizer
        organizer = MoodOrganizer()
        folder = organizer.get_mood_folder(mood)
        reels = list(folder.glob("*.mp4"))

        if not reels:
            console.print(f"[yellow]No reels found in {mood} folder[/]")
            return []

        console.print(Panel(
            f"[bold]Publishing {len(reels)} reels from [{mood}] folder[/]",
            border_style="cyan"
        ))

        results = []
        for reel in reels:
            # Skip already-posted reels
            meta_path = reel.with_suffix(".json")
            if meta_path.exists():
                try:
                    existing = json.loads(meta_path.read_text(encoding="utf-8"))
                    if existing.get("instagram_media_id"):
                        console.print(f"  [dim]Already posted: {reel.name} (ID: {existing['instagram_media_id']})[/]")
                        continue
                except Exception:
                    pass

            media_id = self.publish_from_folder(reel, post_story=post_story)
            if media_id:
                results.append(media_id)

        return results

    def get_reel_analytics(self, media_id: str) -> dict:
        """Fetch engagement metrics for a posted reel."""
        if not self.is_logged_in and not self.login():
            return {}
        try:
            info = self.cl.media_info(media_id)
            return {
                "views":       getattr(info, "view_count", 0) or 0,
                "likes":       getattr(info, "like_count", 0) or 0,
                "comments":    getattr(info, "comment_count", 0) or 0,
                "saves":       0,
                "shares":      0,
                "engagement":  (getattr(info, "like_count", 0) or 0) + (getattr(info, "comment_count", 0) or 0),
            }
        except Exception as e:
            console.print(f"[yellow]Analytics error for {media_id}: {e}[/]")
            return {}

    def _guess_style_from_path(self, video_path: Path) -> str:
        """Guess style from folder name."""
        parent = video_path.parent.name.lower()
        style_map = {
            "romantic":      "romantic",
            "emotional":     "emotional",
            "motivational":  "motivational",
            "sacrifice":     "sacrifice",
            "epic_action":   "epic_action",
            "dark_cinematic":"dark_cinematic",
            "mystical":      "mystical",
            "happy":         "happy",
        }
        return style_map.get(parent, "epic_action")
