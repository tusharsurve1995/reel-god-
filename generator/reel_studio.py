"""
REEL GOD - Reel Studio
======================
Central creator service that turns EITHER an anime source (fetched from the
internet) OR an uploaded photo/video into a finished Instagram Reel, Post, or
Story — with mood-matched music (any genre), animated subtitles, and a caption.

Used by the dashboard "Instagram Reel Creator" panel. Everything routes through
the existing AnimeFetcher / MusicFetcher / ReelComposer components and is saved
to SQLite via AgentMemory.
"""
import os
import re
import json
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

from rich.console import Console

import config

# ── Pillow 10+ compatibility monkeypatch for MoviePy 1.x ──
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

console = Console()

# Output format → aspect ratio understood by ReelComposer
FORMAT_TO_ASPECT = {
    "reel":  "9:16",   # 1080x1920 vertical
    "story": "9:16",   # 1080x1920 vertical (full-screen story)
    "post":  "1:1",    # 1080x1080 square feed post
}

# How many narrative beats (subtitle cuts) each format gets by default
FORMAT_BEATS = {"reel": 5, "story": 4, "post": 3}
FORMAT_BEAT_SECONDS = {"reel": 5.5, "story": 5.0, "post": 4.0}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def format_to_aspect(fmt: str) -> str:
    return FORMAT_TO_ASPECT.get((fmt or "reel").strip().lower(), "9:16")


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def image_to_base_video(image_path: Path, seconds: float = 26.0) -> Path:
    """Render a still image into a base MP4 that the composer can edit.

    Upscales the image to cover a 1080x1920 canvas so the composer's crop / Ken
    Burns effects always have enough pixels to work with.
    """
    from moviepy.editor import ImageClip

    with PIL.Image.open(image_path) as im:
        iw, ih = im.size

    scale = max(1080.0 / iw, 1920.0 / ih, 1.0)
    # x264 requires even width/height — round each dimension down to a multiple of 2
    new_size = (max(2, int(iw * scale) // 2 * 2), max(2, int(ih * scale) // 2 * 2))

    clip = ImageClip(str(image_path)).set_duration(seconds).resize(new_size)

    fd, tmp = tempfile.mkstemp(suffix="_base.mp4")
    os.close(fd)
    clip.write_videofile(
        tmp,
        fps=30,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        logger=None,
    )
    clip.close()
    return Path(tmp)


def _fallback_narrative(instruction: str, style: str, fmt: str) -> List[Dict[str, Any]]:
    """Build a reasonable narrative without the AI (used if Gemini is unavailable)."""
    beats = FORMAT_BEATS.get(fmt, 5)
    dur = FORMAT_BEAT_SECONDS.get(fmt, 5.0)

    # If the commander typed a directive, split it into short punchy lines
    text = (instruction or "").strip()
    lines: List[str] = []
    if text:
        parts = re.split(r"[.!?\n]+", text)
        lines = [p.strip() for p in parts if p.strip()]

    if not lines:
        DEFAULTS = {
            "epic_action":    ["They said it was over.", "He rose one more time.", "POWER HAS NO LIMIT.", "Witness the storm.", "Legends never fall."],
            "emotional":      ["Some goodbyes never heal.", "We were happy once.", "Please don't forget me.", "Even tears can be beautiful.", "Thank you for everything."],
            "romance":        ["The moment our eyes met.", "My heart knew your name.", "Stay with me forever.", "You are my whole world.", "This is our story."],
            "dark_cinematic": ["Darkness always finds you.", "There is no escape.", "The end was written.", "Fear the silence.", "Nothing remains."],
            "motivational":   ["Every fall is a lesson.", "Keep pushing forward.", "RISE ABOVE THE PAIN.", "Your time is now.", "Become unstoppable."],
            "mystical":       ["Beyond the veil of stars.", "Ancient magic awakens.", "A world unseen.", "Destiny is calling.", "Wonder never dies."],
        }
        lines = DEFAULTS.get(style, DEFAULTS["motivational"])

    lines = lines[:beats] or ["Set your heart ablaze."]
    return [{"text": t, "duration": dur} for t in lines]


def generate_narrative(brain, *, subject: str, style: str, instruction: str,
                       fmt: str) -> Dict[str, Any]:
    """Ask the REEL GOD brain (Gemini) for a title/caption/narrative in JSON.

    Falls back to a template narrative if the AI is unavailable or rate-limited.
    """
    beats = FORMAT_BEATS.get(fmt, 5)
    fallback = {
        "title": subject.replace("_", " ").title() if subject else "Reel God",
        "caption": "",
        "hashtags": " ".join(config.BASE_HASHTAGS),
        "narrative": _fallback_narrative(instruction, style, fmt),
        "music_query": "",
    }

    if brain is None:
        return fallback

    prompt = f"""
You are scripting an Instagram {fmt.upper()} in the "{style}" style.
Subject: {subject or 'anime edit'}.
Commander directive: {instruction or '(none — use your best creative judgement)'}

Return ONLY valid JSON (no markdown fences) with this exact shape:
{{
  "title": "<short punchy title>",
  "caption": "<1-2 line Instagram caption with 1-3 emojis>",
  "hashtags": "<8-15 space-separated #hashtags relevant to anime + the mood>",
  "narrative": [
    {{"text": "<on-screen subtitle line, max ~6 words>", "duration": 5.0}}
  ],
  "music_query": "<a short search phrase for the ideal background track>"
}}
The "narrative" array MUST have exactly {beats} lines that build to an emotional climax.
"""
    try:
        raw = brain.think_fresh(prompt)
        cleaned = raw.strip()
        # Strip code fences / stray text around the JSON object
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]
        data = json.loads(cleaned)

        narrative = data.get("narrative") or []
        norm: List[Dict[str, Any]] = []
        for item in narrative:
            if isinstance(item, dict) and item.get("text"):
                norm.append({
                    "text": str(item["text"]).strip(),
                    "duration": float(item.get("duration", FORMAT_BEAT_SECONDS.get(fmt, 5.0))),
                })
        if not norm:
            norm = fallback["narrative"]

        return {
            "title": (data.get("title") or fallback["title"]).strip(),
            "caption": (data.get("caption") or "").strip(),
            "hashtags": (data.get("hashtags") or fallback["hashtags"]).strip(),
            "narrative": norm,
            "music_query": (data.get("music_query") or "").strip(),
        }
    except Exception as e:  # rate limit, JSON error, etc. → graceful fallback
        console.print(f"[yellow]Narrative AI unavailable ({str(e)[:60]}), using template[/]")
        return fallback


def create_reel(
    brain,
    *,
    source: str,
    anime: Optional[str] = None,
    style: str = "epic_action",
    fmt: str = "reel",
    genre: str = "auto",
    instruction: str = "",
    media_path: Optional[Path] = None,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    """Create a Reel/Post/Story and persist it.

    source = "anime"  → fetch an anime clip from the internet for (anime, style)
    source = "upload" → use the provided media_path (photo or video)

    Returns {"post_id", "path", "title", "caption", "format"}.
    Raises RuntimeError on unrecoverable failure.
    """
    from generator.reel_composer import ReelComposer
    from music.music_fetcher import MusicFetcher

    fmt = (fmt or "reel").strip().lower()
    if fmt not in FORMAT_TO_ASPECT:
        fmt = "reel"
    aspect = format_to_aspect(fmt)
    style = style or "epic_action"

    def report(pct: int, stage: str):
        if progress_cb:
            progress_cb(pct, stage)
        console.print(f"[dim]  [{pct}%] {stage}[/]")

    # ── 1. Script / narrative ────────────────────────────────────────────────
    report(5, "Scripting the story...")
    subject = anime or (media_path.stem if media_path else "anime edit")
    meta = generate_narrative(brain, subject=subject, style=style,
                              instruction=instruction, fmt=fmt)

    # ── 2. Source video ──────────────────────────────────────────────────────
    tmp_base: Optional[Path] = None
    if source == "anime":
        report(20, "Fetching anime clip from the internet...")
        from generator.anime_fetcher import AnimeFetcher
        fetcher = AnimeFetcher()
        if anime:
            video_path = fetcher.fetch_for_anime_and_style(anime, style)
        else:
            video_path = fetcher.fetch_clip_for_style(style)
        if not video_path:
            raise RuntimeError(
                "Could not fetch an anime clip. On a server, YouTube may require "
                "cookies — set YTDLP_COOKIES_FILE or YTDLP_COOKIES_FROM_BROWSER."
            )
    elif source == "upload":
        if not media_path or not Path(media_path).exists():
            raise RuntimeError("No uploaded media found.")
        media_path = Path(media_path)
        if is_image(media_path):
            report(20, "Converting photo into a moving base clip...")
            tmp_base = image_to_base_video(media_path)
            video_path = tmp_base
        else:
            video_path = media_path
    else:
        raise RuntimeError(f"Unknown source '{source}'.")

    # ── 3. Music (any genre) ─────────────────────────────────────────────────
    report(45, f"Selecting {genre if genre and genre != 'auto' else 'mood-matched'} music...")
    music_path = None
    try:
        music_path = MusicFetcher().fetch_by_genre(genre, style, anime=anime)
    except Exception as e:
        console.print(f"[yellow]Music selection failed, continuing silent: {e}[/]")

    # ── 4. Compose ───────────────────────────────────────────────────────────
    report(55, "Composing your masterpiece...")
    reel_meta = {
        "style": style,
        "anime": anime or "upload",
        "title": meta["title"],
        "caption": meta["caption"],
        "aspect_ratio": aspect,
        "narrative": meta["narrative"],
    }
    output_name = f"{fmt}_{int(time.time())}.mp4"

    composer = ReelComposer(brain=brain)
    try:
        final_path = composer.compose_reel(
            Path(video_path), music_path, reel_meta, output_name, progress_cb=progress_cb
        )
    finally:
        if tmp_base and tmp_base.exists():
            try:
                tmp_base.unlink()
            except OSError:
                pass

    if not final_path:
        raise RuntimeError("Composer failed to render the video.")

    # ── 5. Persist ───────────────────────────────────────────────────────────
    report(96, "Saving to your library...")
    caption = meta["caption"]
    if meta.get("hashtags"):
        caption = (caption + "\n\n" + meta["hashtags"]).strip()

    music_track = music_path.name if music_path else ""
    post_id = None
    if brain is not None:
        with brain.memory._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO posts
                   (idea_id, title, style, video_path, caption, hashtags, music_track, posted_at)
                   VALUES (NULL, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                (meta["title"], f"{style} · {fmt}", str(final_path), caption,
                 meta.get("hashtags", ""), music_track),
            )
            post_id = cursor.lastrowid
        brain.log(f"Reel Studio: created {fmt} #{post_id} → {final_path.name}", style="green")

    report(100, "Done!")
    return {
        "post_id": post_id,
        "path": str(final_path),
        "filename": final_path.name,
        "title": meta["title"],
        "caption": caption,
        "format": fmt,
    }
