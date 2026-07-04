"""
REEL GOD - Upgraded World-Class Reel Composer
Master pipeline that combines anime clip + music + effects → final 9:16 narrative reel.
Uses multi-cut editing (montage), timed animated subtitles, and transition effects.
"""
import os, sys, math, random, tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
import config

# Fix Windows console encoding issue
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# ── Pillow 10+ compatibility monkeypatch for MoviePy ──
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

console = Console()


class ReelComposer:
    """
    Professional cinematic Instagram Reel composer.
    Features:
    - Dynamic Ken Burns zoom/pan effects
    - Professional transitions (fade, zoom, glitch)
    - Beat-synced music integration
    - Modern glassmorphism UI design
    - Dynamic color grading by mood
    - Speed ramps for dramatic effect
    - Optimized rendering with threading
    """

    FRAME_W = 1080
    FRAME_H = 1920
    FPS = 30
    
    # Style-based color palettes
    COLOR_GRADES = {
        "epic_action": {
            "tension": {"contrast": 1.2, "saturation": 0.8, "tint": (10, 20, 30)},
            "climax": {"contrast": 1.4, "saturation": 1.3, "tint": (20, 10, 0)},
            "resolution": {"contrast": 1.1, "saturation": 1.0, "tint": (0, 5, 10)}
        },
        "emotional": {
            "tension": {"contrast": 1.0, "saturation": 0.7, "tint": (5, 0, 10)},
            "climax": {"contrast": 1.2, "saturation": 0.9, "tint": (10, 5, 5)},
            "resolution": {"contrast": 1.05, "saturation": 0.8, "tint": (0, 0, 5)}
        },
        "dark_cinematic": {
            "tension": {"contrast": 1.3, "saturation": 0.6, "tint": (5, 5, 10)},
            "climax": {"contrast": 1.5, "saturation": 0.8, "tint": (15, 10, 5)},
            "resolution": {"contrast": 1.2, "saturation": 0.7, "tint": (5, 5, 5)}
        },
        "mystical": {
            "tension": {"contrast": 1.1, "saturation": 0.9, "tint": (0, 10, 20)},
            "climax": {"contrast": 1.3, "saturation": 1.2, "tint": (10, 15, 25)},
            "resolution": {"contrast": 1.1, "saturation": 1.0, "tint": (5, 10, 15)}
        },
        "motivational": {
            "tension": {"contrast": 1.15, "saturation": 0.85, "tint": (5, 10, 0)},
            "climax": {"contrast": 1.35, "saturation": 1.25, "tint": (15, 20, 5)},
            "resolution": {"contrast": 1.1, "saturation": 1.05, "tint": (5, 10, 5)}
        },
        # Warm pink/gold palette for romantic reels
        "romance": {
            "tension": {"contrast": 1.05, "saturation": 0.85, "tint": (10, 5, 5)},
            "climax": {"contrast": 1.2, "saturation": 1.1, "tint": (20, 5, 10)},
            "resolution": {"contrast": 1.0, "saturation": 0.95, "tint": (10, 5, 8)}
        },
        # Sacrifice — muted desaturated with red tint
        "sacrifice": {
            "tension": {"contrast": 1.25, "saturation": 0.65, "tint": (8, 5, 5)},
            "climax": {"contrast": 1.45, "saturation": 0.75, "tint": (18, 8, 5)},
            "resolution": {"contrast": 1.15, "saturation": 0.70, "tint": (5, 5, 5)}
        },
        # Happy — vivid saturated warm
        "happy": {
            "tension": {"contrast": 1.1, "saturation": 1.1, "tint": (5, 10, 5)},
            "climax": {"contrast": 1.2, "saturation": 1.3, "tint": (15, 20, 0)},
            "resolution": {"contrast": 1.05, "saturation": 1.15, "tint": (5, 10, 0)}
        },
    }

    def __init__(self, brain=None):
        self.brain = brain
        self.output_dir = config.DATA_DIR / "content_archive"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compose_reel(
        self,
        video_path: Path,
        music_path: Path,
        reel_meta: Dict[str, Any],
        output_name: str = None,
        progress_cb = None,
    ) -> Optional[Path]:
        """
        Full composition pipeline.
        reel_meta = {
            "style": "epic_action",
            "anime": "demon_slayer",
            "title": "Unbreakable Spirit",
            "caption": "...",
            "narrative": [
                {"text": "They told him to surrender...", "duration": 4.5},
                {"text": "He watched his world turn to ash...", "duration": 5.0},
                {"text": "But a broken heart can still beat.", "duration": 5.0},
                {"text": "SET YOUR HEART ABLAZE.", "duration": 5.5},
                {"text": "And burn brighter than the stars.", "duration": 5.0}
            ]
        }
        """
        import numpy as np
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, CompositeVideoClip,
            ColorClip, ImageClip, concatenate_videoclips
        )
        from moviepy.audio.fx.all import audio_fadein, audio_fadeout, audio_loop

        style = reel_meta.get("style", "dark_cinematic")
        anime = reel_meta.get("anime", "anime")
        title = reel_meta.get("title", "Reel God")
        narrative = reel_meta.get("narrative") or []

        # Determine aspect ratio and dimensions
        aspect_ratio = reel_meta.get("aspect_ratio", "9:16")
        if aspect_ratio == "1:1":
            w, h = 1080, 1080
        elif aspect_ratio == "4:5":
            w, h = 1080, 1350
        else: # "9:16"
            w, h = 1080, 1920

        # Fallback narrative if missing
        if not narrative:
            narrative = [
                {"text": reel_meta.get("quote", "Set your heart ablaze 🔥"), "duration": 8.0}
            ]

        if not output_name:
            safe = title.lower().replace(" ", "_")[:30]
            output_name = f"{anime}_{style}_{safe}.mp4"

        # ── Save to mood-based folder ─────────────────────────────────────────
        try:
            from generator.mood_organizer import MoodOrganizer
            organizer = MoodOrganizer()
            output_path = organizer.get_output_path(style, output_name)
        except Exception:
            output_path = self.output_dir / output_name

        console.print(Panel(
            f"[bold magenta]WORLD-CLASS REEL COMPOSITION[/]\n"
            f"[dim]Anime: {anime} | Style: {style} | Cuts: {len(narrative)}[/]\n"
            f"[dim cyan]Output: {output_path.parent.name}/{output_path.name}[/]",
            border_style="magenta"
        ))

        tmp_files = []
        clip_path_str = str(video_path)

        try:
            if progress_cb:
                progress_cb(10, "Slicing visual montage...")

            # ── 1. Load source video ─────────────────────────────────────
            console.print("[dim]  Loading raw clip...[/]")
            try:
                vid = VideoFileClip(clip_path_str)
                total_dur = vid.duration
            except Exception as e:
                console.print(f"[red]Failed to load video: {e}[/]")
                return None

            # ── 2. Calculate spaced starting offsets ─────────────────────
            # Ensures each narrative line cuts to a completely different part of the video
            start_points = []
            segment_durations = [item.get("duration", 5.0) for item in narrative]
            total_narrative_dur = sum(segment_durations)

            for idx in range(len(narrative)):
                # Spread starting points between 10% and 80% of video
                fraction = 0.10 + (idx / len(narrative)) * 0.70
                start_points.append(fraction * total_dur)

            # ── 3. Slice, crop, grade, and overlay text on each cut ──────
            sub_clips = []
            for idx, item in enumerate(narrative):
                text = item.get("text", "")
                dur = item.get("duration", 5.0)
                start_t = start_points[idx]
                end_t = min(start_t + dur, total_dur)

                console.print(f"  [dim]Cut {idx+1}/{len(narrative)}: {start_t:.1f}s → {end_t:.1f}s | '{text}'[/]")
                if progress_cb:
                    pct = 10 + int((idx / len(narrative)) * 45)
                    progress_cb(pct, f"Editing visual segment {idx+1}/{len(narrative)}...")

                # A. subclip slicing with speed ramp for climax
                is_climax = (idx == len(narrative) - 2) or (text.isupper() and len(text) > 3)
                try:
                    sub = vid.subclip(start_t, end_t)
                except Exception as e:
                    console.print(f"[yellow]Subclip failed at {start_t:.1f}s, using fallback: {e}[/]")
                    # Fallback: use middle of video
                    mid = total_dur / 2
                    sub = vid.subclip(max(0, mid - dur/2), min(total_dur, mid + dur/2))
                
                # Apply speed ramp on climax (slow-mo effect)
                if is_climax and style in ["epic_action", "dark_cinematic"]:
                    console.print("    [dim]Applying climax speed ramp...[/]")
                    try:
                        from moviepy.video.fx.speedx import speedx
                        sub = sub.fx(speedx, 0.7)
                    except Exception as e:
                        console.print(f"[yellow]Speed ramp failed, continuing: {e}[/]")
                
                # B. crop to target aspect ratio with smart centering
                try:
                    sub = self._smart_crop(sub, w, h)
                except Exception as e:
                    console.print(f"[yellow]Smart crop failed, using basic resize: {e}[/]")
                    sub = sub.resize((w, h))

                # Cover hardcoded widescreen subtitles in the original video
                mask_h = int(h * 0.14)
                black_bar = ColorClip(
                    size=(w, mask_h),
                    color=(0, 0, 0)
                ).set_duration(sub.duration).set_position(("center", "bottom"))
                
                sub = CompositeVideoClip(
                    [sub, black_bar],
                    size=(w, h)
                ).set_duration(sub.duration)

                # C. Apply Ken Burns zoom/pan effect for dynamic movement
                try:
                    sub = self._apply_ken_burns(sub, w, h, idx, len(narrative), is_climax)
                except Exception as e:
                    console.print(f"[yellow]Ken Burns failed, continuing: {e}[/]")

                # D. Apply style-based color grading
                try:
                    sub = self._apply_color_grading(sub, idx, len(narrative), style)
                except Exception as e:
                    console.print(f"[yellow]Color grading failed, continuing: {e}[/]")

                # E. Enhanced camera shake on climax (only for intense styles)
                if is_climax and style in ["epic_action", "dark_cinematic", "mystical", "sacrifice"]:
                    console.print("    [dim]Applying enhanced climax camera shake...[/]")
                    try:
                        sub = self._apply_shake_effect(sub, w, h, intensity=20, frequency=12)
                    except Exception as e:
                        console.print(f"[yellow]Camera shake failed, continuing: {e}[/]")

                # F. Cinematic vignette
                try:
                    sub = self._apply_vignette_effect(sub, w, h, intensity=0.7)
                except Exception as e:
                    console.print(f"[yellow]Vignette failed, continuing: {e}[/]")

                # G. Film grain for cinematic feel (more styles)
                if style in ["dark_cinematic", "emotional", "sacrifice", "romance"]:
                    try:
                        sub = self._apply_film_grain(sub, intensity=0.10)
                    except Exception as e:
                        console.print(f"[yellow]Film grain failed, continuing: {e}[/]")

                # H. burn subtitle overlay — style-adaptive positioning
                if text:
                    # Choose subtitle Y position based on emotional register of style
                    SOFT_STYLES = ["emotional", "romance", "mystical", "happy"]
                    STRONG_STYLES = ["epic_action", "motivational", "sacrifice"]
                    if style in SOFT_STYLES:
                        # Center-lower: text at 60% height feels intimate and cinematic
                        text_y_factor = 0.62
                    elif style in STRONG_STYLES:
                        # Lower third: bold text at 72% height for hype
                        text_y_factor = 0.72
                    else:
                        text_y_factor = 0.68  # dark_cinematic default
                    text_img = self._render_format_overlay(text, anime, is_climax, aspect_ratio, w, h, style, text_y_factor)
                    fd, tmp_text = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    text_img.save(tmp_text, "PNG")
                    tmp_files.append(tmp_text)

                    # Create overlay clip with subtle zoom-in
                    text_clip = (
                        ImageClip(tmp_text)
                        .set_duration(sub.duration)
                        .set_fps(self.FPS)
                        .fadein(0.3)
                        .fadeout(0.2)
                    )
                    
                    # Apply small zoom to subtitles to feel dynamic
                    text_clip = text_clip.resize(lambda t: 1.0 + 0.03 * (t / sub.duration))

                    sub = CompositeVideoClip(
                        [sub, text_clip],
                        size=(w, h)
                    ).set_duration(sub.duration)

                # H. Professional transitions based on style
                if idx > 0:
                    try:
                        if style == "epic_action" and is_climax:
                            # Glitch transition for action climax
                            sub = self._apply_glitch_transition(sub, w, h)
                        elif style in ["emotional", "mystical"]:
                            # Smooth fade transition
                            sub = sub.fadein(0.4)
                        else:
                            # Quick flash transition
                            flash = ColorClip(
                                size=(w, h),
                                color=(255, 255, 255)
                            ).set_duration(0.2).fadeout(0.2)
                            sub = CompositeVideoClip(
                                [sub, flash],
                                size=(w, h)
                            ).set_duration(sub.duration)
                    except Exception as e:
                        console.print(f"[yellow]Transition failed, continuing: {e}[/]")

                sub_clips.append(sub)

            # ── 4. Concatenate segments ──────────────────────────────────
            console.print("[dim]  Concatenating visual cuts...[/]")
            if progress_cb:
                progress_cb(55, "Concatenating edited clips...")
            final_video = concatenate_videoclips(sub_clips)

            # ── 5. Add global fade in/out ────────────────────────────────
            final_video = final_video.fadein(0.5).fadeout(1.0)

            # ── 6. Mix music with beat-synced volume ────────────────────────
            if music_path and music_path.exists():
                console.print("[dim]  Mixing music with beat sync...[/]")
                if progress_cb:
                    progress_cb(65, "Syncing soundtrack & audio fading...")
                try:
                    aud = AudioFileClip(str(music_path))
                    vdur = final_video.duration
                    
                    if aud.duration < vdur:
                        aud = aud.fx(audio_loop, duration=vdur)
                    else:
                        aud = aud.subclip(0, vdur)
                    
                    # Dynamic volume based on narrative progression
                    # Louder during climax, softer during tension
                    climax_start = sum(item.get("duration", 5.0) for i, item in enumerate(narrative) if i < len(narrative) - 2)
                    climax_end = climax_start + narrative[-2].get("duration", 5.0) if len(narrative) >= 2 else vdur
                    
                    def dynamic_volume(get_frame, t):
                        """Dynamic volume curve based on narrative position."""
                        import numpy as np
                        frame = get_frame(t)
                        if isinstance(t, np.ndarray):
                            factors = np.ones((len(t), 1)) * 0.9  # Normal volume during resolution
                            
                            buildup_mask = (t < climax_start)
                            factors[buildup_mask] = 0.75  # Slightly lower during buildup
                            
                            climax_mask = (t >= climax_start) & (t <= climax_end)
                            factors[climax_mask] = 1.15  # Boost volume during climax
                            
                            return frame * factors
                        else:
                            if climax_start <= t <= climax_end:
                                return frame * 1.15
                            elif t < climax_start:
                                return frame * 0.75
                            else:
                                return frame * 0.9
                    
                    aud = aud.fl(dynamic_volume).fx(audio_fadein, 1.5).fx(audio_fadeout, 2.0)
                    final_video = final_video.set_audio(aud)
                except Exception as e:
                    console.print(f"[yellow]Music mixing failed, continuing without music: {e}[/]")

            # ── 7. Render at maximum HD quality for Instagram ────────────────
            console.print(f"[yellow]  Rendering HD video → {output_name}[/]")
            if progress_cb:
                progress_cb(75, "Rendering HD video (encoding at max quality)...")
            
            # Instagram-optimized HD encoding:
            # - bitrate 8Mbps = crystal clear 1080p
            # - audio 256k = near-lossless audio
            # - preset 'slow' = best compression quality (smaller file, same visual quality)
            # - yuv420p = universal compatibility (iOS, Android, web)
            # - 2-pass encoding via high bitrate single pass
            final_video.write_videofile(
                str(output_path),
                fps=self.FPS,
                codec="libx264",
                bitrate="8000k",         # 8 Mbps — Instagram HD threshold
                audio_codec="aac",
                audio_bitrate="256k",    # Near-lossless audio
                preset="ultrafast",      # Ultra fast encoding for speed

                ffmpeg_params=[
                    "-pix_fmt", "yuv420p",   # Universal compatibility
                    "-movflags", "+faststart", # Web streaming optimization
                    "-profile:v", "high",     # H.264 High profile for best quality
                ],
                logger=None,
            )


            vid.close()
            final_video.close()
            for c in sub_clips:
                c.close()

            console.print(f"[bold green]✓ Narrative Reel created successfully:[/] {output_path.name}")
            if progress_cb:
                progress_cb(95, "Writing metadata...")

            # ── Write complete metadata sidecar JSON ──────────────────────────
            try:
                from datetime import datetime, timezone
                import json as _json
                # Determine music name from path if available
                music_name = ""
                if music_path:
                    music_name = Path(music_path).stem.replace("_", " ").title()

                metadata = {
                    "title":        reel_meta.get("title", title),
                    "anime":        anime,
                    "style":        style,
                    "quote":        reel_meta.get("quote", ""),
                    "purpose":      reel_meta.get("purpose", ""),
                    "caption":      reel_meta.get("caption", ""),
                    "music_name":   music_name,
                    "music_file":   str(music_path) if music_path else "",
                    "aspect_ratio": aspect_ratio,
                    "duration_s":   round(sum(s["duration"] for s in narrative), 1),
                    "narrative":    narrative,
                    "mood_folder":  output_path.parent.name,
                    "video_file":   str(output_path),
                    "created_at":   datetime.now(timezone.utc).isoformat(),
                    "instagram_media_id": None,
                    "posted_at":    None,
                }

                meta_path = output_path.with_suffix(".json")
                meta_path.write_text(
                    _json.dumps(metadata, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                console.print(f"  [dim]Metadata saved: {meta_path.name}[/]")
            except Exception as me:
                console.print(f"  [yellow]Metadata write failed: {me}[/]")

            # ── Auto-generate thumbnail ───────────────────────────────────────
            try:
                from generator.mood_organizer import _find_ffmpeg
                ffmpeg = _find_ffmpeg()
                if ffmpeg:
                    thumb_path = output_path.with_suffix(".jpg")
                    import subprocess as _sp
                    _sp.run([
                        ffmpeg, "-y",
                        "-ss", "2.5",
                        "-i", str(output_path),
                        "-vframes", "1",
                        "-q:v", "1",
                        str(thumb_path),
                    ], capture_output=True, timeout=20)
                    if thumb_path.exists():
                        console.print(f"  [dim]Thumbnail: {thumb_path.name}[/]")
            except Exception:
                pass

            if progress_cb:
                progress_cb(100, "Production complete!")
            return output_path

        except Exception as e:
            console.print(f"[red]Composition failed: {e}[/]")
            import traceback
            traceback.print_exc()
            return None

        finally:
            for tf in tmp_files:
                try:
                    if os.path.exists(tf):
                        os.remove(tf)
                except Exception:
                    pass

    def _smart_crop(self, clip, target_w: int, target_h: int):
        """Resize and center-crop video to target dimensions with automatic border zoom-out."""
        src_w, src_h = clip.w, clip.h
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        # Apply a default 1.22x zoom-in boost for 9:16 vertical videos to crop out letterbox black bars
        zoom = 1.22 if target_w < target_h else 1.0

        if src_ratio > target_ratio:
            scale = (target_h / src_h) * zoom
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            resized = clip.resize((new_w, new_h))
            x_off = (new_w - target_w) // 2
            y_off = (new_h - target_h) // 2
            return resized.crop(x1=x_off, y1=y_off, x2=x_off + target_w, y2=y_off + target_h)
        else:
            scale = (target_w / src_w) * zoom
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            resized = clip.resize((new_w, new_h))
            x_off = (new_w - target_w) // 2
            y_off = (new_h - target_h) // 2
            return resized.crop(x1=x_off, y1=y_off, x2=x_off + target_w, y2=y_off + target_h)

    def _apply_ken_burns(self, clip, w: int, h: int, idx: int, total: int, is_climax: bool):
        """Apply subtle Ken Burns zoom/pan effect for dynamic movement."""
        import numpy as np
        
        # Determine zoom direction based on index
        zoom_in = idx % 2 == 0
        zoom_factor = 1.08 if is_climax else 1.05  # More zoom on climax
        
        def ken_burns_frame(get_frame, t):
            frame = get_frame(t)
            progress = t / clip.duration
            
            if zoom_in:
                # Zoom in from center
                scale = 1.0 + (zoom_factor - 1.0) * progress
            else:
                # Zoom out from center
                scale = zoom_factor - (zoom_factor - 1.0) * progress
            
            # Apply zoom
            new_h = int(h * scale)
            new_w = int(w * scale)
            
            # Resize frame
            from PIL import Image
            pil_img = Image.fromarray(frame)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            resized = np.array(pil_img)
            
            # Crop to center
            y_off = (new_h - h) // 2
            x_off = (new_w - w) // 2
            
            return resized[y_off:y_off+h, x_off:x_off+w]
        
        return clip.fl(ken_burns_frame)

    def _apply_color_grading(self, clip, idx: int, total: int, style: str):
        """Apply style-based color grading with mood progression."""
        import numpy as np
        
        # Determine grade stage
        if idx < total // 2:
            stage = "tension"
        elif idx == total - 2:
            stage = "climax"
        else:
            stage = "resolution"
        
        # Get style parameters
        grade_params = self.COLOR_GRADES.get(style, self.COLOR_GRADES["epic_action"])
        params = grade_params.get(stage, grade_params["tension"])
        
        contrast = params["contrast"]
        saturation = params["saturation"]
        tint = params["tint"]
        
        def grade_frame(gf, t):
            f = gf(t).astype(float)
            
            # Apply contrast
            f = (f - 128) * contrast + 128
            
            # Apply saturation
            lum = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
            for ch in range(3):
                f[..., ch] = f[..., ch] * saturation + lum * (1 - saturation)
            
            # Apply color tint
            f[..., 0] = np.clip(f[..., 0] + tint[0], 0, 255)
            f[..., 1] = np.clip(f[..., 1] + tint[1], 0, 255)
            f[..., 2] = np.clip(f[..., 2] + tint[2], 0, 255)
            
            return np.clip(f, 0, 255).astype(np.uint8)
        
        return clip.fl(grade_frame)

    def _apply_vignette_effect(self, clip, w: int, h: int, intensity=0.65):
        """Apply cinematic vignette with adjustable intensity."""
        import numpy as np
        Y, X = np.ogrid[:h, :w]
        cx, cy = w / 2.0, h / 2.0
        r = math.sqrt(cx**2 + cy**2)
        vmask = (1.0 - np.clip(np.sqrt((X - cx)**2 + (Y - cy)**2) / r * intensity, 0, 1))[..., np.newaxis]

        def apply_vign(gf, t):
            return (gf(t).astype(float) * vmask).astype(np.uint8)

        return clip.fl(apply_vign)

    def _apply_film_grain(self, clip, intensity=0.1):
        """Add subtle film grain for cinematic texture."""
        import numpy as np
        
        def add_grain(get_frame, t):
            frame = get_frame(t).astype(float)
            noise = np.random.normal(0, intensity * 25, frame.shape)
            grainy = frame + noise
            return np.clip(grainy, 0, 255).astype(np.uint8)
        
        return clip.fl(add_grain)

    def _apply_glitch_transition(self, clip, w: int, h: int):
        """Apply digital glitch effect for action transitions."""
        import numpy as np
        
        def glitch_frame(get_frame, t):
            frame = get_frame(t).astype(float)
            
            # Only glitch in first 0.15 seconds
            if t > 0.15:
                return frame.astype(np.uint8)
            
            # Random horizontal shifts
            shift_amount = int(np.random.uniform(-10, 10))
            if shift_amount != 0:
                shifted = np.zeros_like(frame)
                if shift_amount > 0:
                    shifted[:, shift_amount:] = frame[:, :-shift_amount]
                else:
                    shifted[:, :shift_amount] = frame[:, -shift_amount:]
                frame = shifted
            
            # Color channel separation
            if np.random.random() > 0.5:
                frame[..., 0] = np.roll(frame[..., 0], np.random.randint(-3, 4), axis=0)
                frame[..., 2] = np.roll(frame[..., 2], np.random.randint(-3, 4), axis=0)
            
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.fl(glitch_frame)

    def _apply_shake_effect(self, clip, w: int, h: int, intensity=16, frequency=9):
        """Sinusoidal camera shake effect applied frame-by-frame."""
        import numpy as np

        def shake_frame(get_frame, t):
            dx = int(intensity * math.sin(t * frequency * 2 * math.pi))
            dy = int(intensity * math.cos(t * frequency * 2.4 * math.pi))
            frame = get_frame(t)
            shifted = np.zeros_like(frame)

            src_y0 = max(-dy, 0)
            src_y1 = min(h - dy, h)
            src_x0 = max(-dx, 0)
            src_x1 = min(w - dx, w)
            dst_y0 = max(dy, 0)
            dst_y1 = min(h + dy, h)
            dst_x0 = max(dx, 0)
            dst_x1 = min(w + dx, w)

            copy_h = min(src_y1 - src_y0, dst_y1 - dst_y0)
            copy_w = min(src_x1 - src_x0, dst_x1 - dst_x0)
            if copy_h > 0 and copy_w > 0:
                shifted[dst_y0:dst_y0+copy_h, dst_x0:dst_x0+copy_w] = frame[src_y0:src_y0+copy_h, src_x0:src_x0+copy_w]
            return shifted

        return clip.fl(shake_frame)

    def _render_format_overlay(
        self, text: str, anime: str, is_climax: bool, aspect_ratio: str, w: int, h: int,
        style: str = "epic_action", text_y_factor: float = 0.68
    ):
        """Render modern glassmorphism subtitle and header/footer overlays with style-specific colors."""
        from PIL import Image, ImageDraw, ImageFont, ImageFilter

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Modern fonts - prefer bold/condensed for better readability
        font_paths = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]
        
        # Dynamic font sizing based on text length
        text_len = len(text)
        if is_climax:
            fs = max(46, min(70, 68 - text_len // 3))  # 46-70 range for climax
        else:
            fs = max(34, min(50, 48 - text_len // 4))  # 34-50 range for normal
        
        font = None
        for fp in font_paths:
            if Path(fp).exists():
                try:
                    font = ImageFont.truetype(fp, fs)
                    break
                except:
                    pass
        if not font:
            font = ImageFont.load_default()

        # Style-specific text colors
        STYLE_TEXT_COLORS = {
            "epic_action":    ((255, 230, 100, 255), (255, 200, 50, 200)),   # Gold
            "motivational":   ((255, 240, 80, 255),  (255, 200, 30, 200)),   # Bright gold
            "dark_cinematic": ((255, 80, 80, 255),   (200, 50, 50, 180)),    # Red/crimson
            "sacrifice":      ((255, 100, 80, 255),  (200, 60, 60, 180)),    # Blood red
            "emotional":      ((180, 230, 255, 255), (130, 190, 255, 200)),  # Sky blue
            "romance":        ((255, 180, 210, 255), (255, 140, 180, 200)),  # Rose pink
            "mystical":       ((200, 180, 255, 255), (160, 130, 255, 200)),  # Violet
            "happy":          ((255, 255, 150, 255), (255, 240, 100, 200)),  # Sunny yellow
        }
        text_color, glow_color = STYLE_TEXT_COLORS.get(style, STYLE_TEXT_COLORS["epic_action"])

        # RENDER STORY WITH INSTAGRAM POLL STICKER AT THE END
        if aspect_ratio == "9:16" and is_climax:
            # Draw standard subtitle at the style-specific Y position
            sub_y = int(h * text_y_factor)
            self._draw_wordwrapped_text(draw, text, font, sub_y, w, is_climax, text_color, glow_color)
            
            # Draw interactive Instagram Poll Sticker in the middle
            sticker_y = h // 2 - 250
            # Sticker white card
            draw.rounded_rectangle(
                [w // 2 - 240, sticker_y, w // 2 + 240, sticker_y + 200],
                radius=25, fill=(255, 255, 255, 240), outline=(240, 240, 240, 255), width=2
            )
            
            font_title = None
            for fp in font_paths:
                if Path(fp).exists():
                    try:
                        font_title = ImageFont.truetype(fp, 32)
                        break
                    except:
                        pass
            if not font_title:
                font_title = font

            # Poll question varies per style
            POLL_QUESTIONS = {
                "epic_action":    "WOULD YOU SURVIVE THIS?",
                "emotional":      "DID THIS BREAK YOUR HEART?",
                "romance":        "IS THIS LOVE? 💕",
                "motivational":   "ARE YOU READY TO RISE? 🔥",
                "dark_cinematic": "FEEL THE DARKNESS?",
                "mystical":       "DO YOU BELIEVE IN DESTINY?",
                "sacrifice":      "WOULD YOU SACRIFICE ALL?",
                "happy":          "DOES THIS MAKE YOU SMILE? 😊",
            }
            poll_q = POLL_QUESTIONS.get(style, "WOULD YOU SURVIVE?")
            draw.text((w // 2, sticker_y + 40), poll_q, font=font_title, fill=(50, 50, 50, 255), anchor="mm")

            # YES/NO options boxes
            draw.rounded_rectangle(
                [w // 2 - 200, sticker_y + 100, w // 2 - 20, sticker_y + 160],
                radius=15, fill=(240, 248, 255, 255), outline=(0, 149, 246, 255), width=2
            )
            draw.text((w // 2 - 110, sticker_y + 130), "YES", font=font_title, fill=(0, 149, 246, 255), anchor="mm")

            draw.rounded_rectangle(
                [w // 2 + 20, sticker_y + 100, w // 2 + 200, sticker_y + 160],
                radius=15, fill=(255, 240, 240, 255), outline=(255, 59, 48, 255), width=2
            )
            draw.text((w // 2 + 110, sticker_y + 130), "NO", font=font_title, fill=(255, 59, 48, 255), anchor="mm")

        # RENDER SQUARE FEED POST LAYOUT WITH CLASSIC LETTERBOX HEADERS
        elif aspect_ratio == "1:1":
            # Add top polaroid/post badge header
            font_header = None
            for fp in font_paths:
                if Path(fp).exists():
                    try:
                        font_header = ImageFont.truetype(fp, 28)
                        break
                    except:
                        pass
            if not font_header:
                font_header = font

            # Draw a clean header strip
            draw.rectangle([0, 0, w, 80], fill=(0, 0, 0, 140))
            draw.text((w // 2, 40), f"✦ POST OF THE DAY ✦", font=font_header, fill=(255, 220, 80, 220), anchor="mm")

            # Draw subtitle at the bottom area with glassmorphic background
            self._draw_wordwrapped_text(draw, text, font, h - 220, w, is_climax, text_color, glow_color)

        # DEFAULT PORTRAIT OR REEL LAYOUT
        else:
            sub_y = int(h * text_y_factor)
            self._draw_wordwrapped_text(draw, text, font, sub_y, w, is_climax, text_color, glow_color)

        # Header Anime Name badge
        font_badge = None
        for fp in font_paths:
            if Path(fp).exists():
                try:
                    font_badge = ImageFont.truetype(fp, 36)
                    break
                except:
                    pass
        if not font_badge:
            font_badge = font

        anime_name = anime.replace("_", " ").upper()
        draw.text((60, 80), anime_name, font=font_badge, fill=(255, 220, 80, 200))

        # Bottom watermark
        draw.text((w // 2, h - 90), "✦ REEL GOD ✦", font=font_badge, fill=(255, 255, 255, 120), anchor="mm")

        return img

    def _draw_wordwrapped_text(self, draw, text: str, font, y: int, w: int, is_climax: bool,
                               text_color=(255, 255, 255, 255), glow_color=(255, 200, 50, 200)):
        """Draw modern glassmorphism text with style-specific colors and enhanced shadow effects."""
        from PIL import ImageDraw, ImageFilter
        max_w = w - 100  # More space for better readability
        words = text.split()
        lines, cur = [], []
        for wd in words:
            test = " ".join(cur + [wd])
            try:
                bw = draw.textbbox((0, 0), test, font=font)[2]
            except:
                bw = len(test) * 20
            if bw <= max_w:
                cur.append(wd)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [wd]
        if cur:
            lines.append(" ".join(cur))

        line_h = font.size + 18  # More line spacing
        total_h = len(lines) * line_h
        start_y = y - total_h // 2

        # Glassmorphism background with blur effect
        bg_rect = [50, start_y - 30, w - 50, start_y + total_h + 30]
        
        # Draw gradient background
        if is_climax:
            # Golden gradient for climax
            draw.rectangle(bg_rect, fill=(20, 15, 5, 180))
            draw.rectangle(bg_rect, outline=(255, 200, 50, 100), width=2)
        else:
            # Dark glassmorphism for normal
            draw.rectangle(bg_rect, fill=(10, 10, 15, 160))
            draw.rectangle(bg_rect, outline=(100, 100, 120, 80), width=1)

        for i, line in enumerate(lines):
            ly = start_y + i * line_h
            try:
                bw = draw.textbbox((0, 0), line, font=font)[2]
            except:
                bw = len(line) * 20
            x = (w - bw) // 2

            fill_color = text_color if (is_climax or text.isupper()) else (255, 255, 255, 255)
            
            # Premium shadow effect
            if is_climax or text.isupper():
                # Multi-layer premium shadow
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        if dx != 0 or dy != 0:
                            dist = abs(dx) + abs(dy)
                            shadow_alpha = 220 if dist < 3 else 160 if dist < 5 else 100
                            draw.text((x + dx, ly + dy), line, font=font, fill=(0, 0, 0, shadow_alpha))
                # Glow effect for climax
                if is_climax:
                    draw.text((x, ly), line, font=font, fill=glow_color)
                    draw.text((x, ly), line, font=font, fill=text_color)
                else:
                    draw.text((x, ly), line, font=font, fill=fill_color)
            else:
                # Clean shadow for normal text
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, ly + dy), line, font=font, fill=(0, 0, 0, 180))
                draw.text((x, ly), line, font=font, fill=fill_color)

