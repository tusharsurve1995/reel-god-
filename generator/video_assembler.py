"""
REEL GOD — Video Assembler Module

Assembles anime images into Instagram Reel videos (9:16 portrait, 1080x1920)
using MoviePy for composition and PIL/Pillow for image processing.

Supports crossfade transitions, text overlays, intro/outro frames,
and configurable slideshow creation with H.264 encoding.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
    TextClip,
    ColorClip,
    concatenate_videoclips,
    vfx,
)
from PIL import Image, ImageFilter
from rich.console import Console

from config import (
    VIDEO_FPS,
    VIDEO_DURATION_PER_IMAGE,
    VIDEO_RESOLUTION,
    VIDEO_BITRATE,
    VIDEO_CODEC,
    CONTENT_DIR,
)

console = Console()

# Unpack resolution for convenience
WIDTH, HEIGHT = VIDEO_RESOLUTION


class VideoAssembler:
    """Assembles a sequence of images into a polished Instagram Reel video.

    Handles image resizing to 1080x1920, crossfade transitions,
    text overlays, and intro/outro frame generation.  All heavy
    lifting is delegated to MoviePy; Pillow is used only for
    pre-processing individual frames.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """Initialise the assembler.

        Args:
            output_dir: Directory where finished videos are written.
                        Defaults to ``CONTENT_DIR`` from config.
        """
        self.output_dir = output_dir or str(CONTENT_DIR)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.use_pillow_fallback = False
        try:
            test = TextClip("test", fontsize=10)
            test.close()
        except Exception:
            console.log("[yellow]⚠️  ImageMagick not found. Enabling Pillow-based text rendering fallback.[/yellow]")
            self.use_pillow_fallback = True
            
        self._temp_files_to_cleanup = []
        console.log(f"[bold green]VideoAssembler[/] initialised → output: {self.output_dir}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble_reel(
        self,
        image_paths: list[str],
        output_filename: str,
        story_text: Optional[str] = None,
        intro_title: Optional[str] = None,
        intro_subtitle: Optional[str] = None,
        outro_text: Optional[str] = None,
        duration_per_image: float = VIDEO_DURATION_PER_IMAGE,
        crossfade_duration: float = 0.6,
    ) -> str:
        """Build a complete Reel from a list of images.

        Args:
            image_paths:        Ordered list of image file paths.
            output_filename:    Name of the output MP4 (e.g. ``reel_01.mp4``).
            story_text:         Optional quote/text overlaid on every frame.
            intro_title:        Title shown on the intro card.
            intro_subtitle:     Subtitle shown on the intro card.
            outro_text:         Text shown on the outro card.
            duration_per_image: Seconds each image is displayed.
            crossfade_duration: Seconds for crossfade between images.

        Returns:
            Absolute path to the rendered MP4 file.
        """
        if not image_paths:
            console.log("[bold red]No images provided — aborting.[/]")
            raise ValueError("image_paths must contain at least one path.")

        console.log(f"[cyan]Assembling reel from {len(image_paths)} image(s)…[/]")

        self._temp_files_to_cleanup = []
        resized_paths = []
        try:
            # 1. Resize images ----------------------------------
            resized_paths = [self._resize_image(p) for p in image_paths]
            
            # 2. Optional text overlay ------------------------------------------
            if story_text:
                if self.use_pillow_fallback:
                    text_resized_paths = []
                    for p in resized_paths:
                        overlay_path = self._draw_text_pillow(p, story_text, position_y_ratio=0.8)
                        text_resized_paths.append(overlay_path)
                        self._temp_files_to_cleanup.append(overlay_path)
                        # Clean up intermediate resized path if it was temp
                        if p.startswith(tempfile.gettempdir()) and os.path.exists(p):
                            os.remove(p)
                    resized_paths = text_resized_paths
            
            clips = [
                ImageClip(p).set_duration(duration_per_image).set_fps(VIDEO_FPS)
                for p in resized_paths
            ]
            
            if story_text and not self.use_pillow_fallback:
                clips = [self.add_text_overlay(c, story_text) for c in clips]

            # 3. Crossfade transitions ------------------------------------------
            if len(clips) > 1:
                clips = self.add_crossfade(clips, duration=crossfade_duration)

            # 4. Intro / outro --------------------------------------------------
            segments: list = []
            if intro_title:
                segments.append(self.add_intro(intro_title, intro_subtitle or ""))
            segments.extend(clips if isinstance(clips, list) else [clips])
            if outro_text:
                segments.append(self.add_outro(outro_text))

            # 5. Concatenate & render -------------------------------------------
            final = concatenate_videoclips(segments, method="compose")
            output_path = os.path.join(self.output_dir, output_filename)

            console.log(f"[yellow]Rendering → {output_path}[/]")
            final.write_videofile(
                output_path,
                fps=VIDEO_FPS,
                codec=VIDEO_CODEC,
                bitrate=VIDEO_BITRATE,
                audio=False,
                logger="bar",
            )
            console.log(f"[bold green]✔ Reel saved:[/] {output_path}")
            return output_path
            
        finally:
            # Clean up all temp files
            for p in resized_paths:
                if p and p.startswith(tempfile.gettempdir()) and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            for p in self._temp_files_to_cleanup:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            self._temp_files_to_cleanup = []

    def add_crossfade(
        self,
        clips: list,
        duration: float = 0.6,
    ) -> list:
        """Apply crossfade transitions between consecutive clips.

        Each clip except the first is overlapped with the previous one
        by ``duration`` seconds, creating a smooth dissolve effect.

        Args:
            clips:    Ordered list of MoviePy video clips.
            duration: Length of each crossfade in seconds.

        Returns:
            A new list of clips with adjusted start times and opacity
            for crossfade compositing.
        """
        if len(clips) < 2:
            return clips

        faded: list = []
        for idx, clip in enumerate(clips):
            start_time = max(0, idx * (clip.duration - duration))
            clip = clip.set_start(start_time).crossfadein(duration) if idx > 0 else clip.set_start(0)
            faded.append(clip)

        total_duration = faded[-1].start + faded[-1].duration
        composite = CompositeVideoClip(faded, size=VIDEO_RESOLUTION).set_duration(total_duration)
        return [composite]

    def add_text_overlay(
        self,
        clip,
        text: str,
        position: str = "center",
        font_size: int = 48,
        color: str = "white",
        font: str = "Arial-Bold",
        stroke_color: str = "black",
        stroke_width: int = 2,
    ):
        """Overlay styled text onto a clip.

        Args:
            clip:          Base video/image clip.
            text:          The string to display.
            position:      MoviePy position descriptor (default ``"center"``).
            font_size:     Font size in pixels.
            color:         Text fill colour.
            font:          Font name (must be available on the system).
            stroke_color:  Outline colour for readability.
            stroke_width:  Outline thickness in pixels.

        Returns:
            A ``CompositeVideoClip`` with the text burned in.
        """
        txt_clip = (
            TextClip(
                text,
                fontsize=font_size,
                color=color,
                font=font,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method="caption",
                size=(WIDTH - 120, None),  # horizontal padding
                align="center",
            )
            .set_position(position)
            .set_duration(clip.duration)
        )
        return CompositeVideoClip([clip, txt_clip], size=VIDEO_RESOLUTION)

    def add_intro(
        self,
        title: str,
        subtitle: str = "",
        duration: float = 3.0,
    ):
        """Generate a branded intro frame.

        Creates a dark background card with a centred title and
        optional subtitle.

        Args:
            title:    Main title text.
            subtitle: Secondary text shown below the title.
            duration: How long the intro is displayed (seconds).

        Returns:
            A ``CompositeVideoClip`` representing the intro card.
        """
        if self.use_pillow_fallback:
            # Create dark background image via Pillow
            from PIL import Image
            img = Image.new("RGB", VIDEO_RESOLUTION, (10, 10, 10))
            
            # Temporary file
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(tmp_fd)
            img.save(tmp_path)
            
            tmp_path2 = self._draw_text_pillow(tmp_path, title, font_size=64, color="white", position_y_ratio=0.4)
            os.remove(tmp_path)
            
            if subtitle:
                tmp_path3 = self._draw_text_pillow(tmp_path2, subtitle, font_size=36, color="#cccccc", stroke_width=1, position_y_ratio=0.55)
                os.remove(tmp_path2)
                final_path = tmp_path3
            else:
                final_path = tmp_path2
                
            self._temp_files_to_cleanup.append(final_path)
            return ImageClip(final_path).set_duration(duration).set_fps(VIDEO_FPS)

        bg = ColorClip(size=VIDEO_RESOLUTION, color=(10, 10, 10)).set_duration(duration).set_fps(VIDEO_FPS)

        title_clip = (
            TextClip(
                title,
                fontsize=64,
                color="white",
                font="Arial-Bold",
                method="caption",
                size=(WIDTH - 160, None),
                align="center",
            )
            .set_position(("center", HEIGHT // 2 - 120))
            .set_duration(duration)
        )

        layers = [bg, title_clip]

        if subtitle:
            sub_clip = (
                TextClip(
                    subtitle,
                    fontsize=36,
                    color="#cccccc",
                    font="Arial",
                    method="caption",
                    size=(WIDTH - 200, None),
                    align="center",
                )
                .set_position(("center", HEIGHT // 2 + 20))
                .set_duration(duration)
            )
            layers.append(sub_clip)

        return CompositeVideoClip(layers, size=VIDEO_RESOLUTION)

    def add_outro(
        self,
        text: str = "Follow for more 🔥",
        duration: float = 3.0,
    ):
        """Generate an outro frame.

        Args:
            text:     Call-to-action or closing text.
            duration: How long the outro is displayed (seconds).

        Returns:
            A ``CompositeVideoClip`` representing the outro card.
        """
        if self.use_pillow_fallback:
            from PIL import Image
            img = Image.new("RGB", VIDEO_RESOLUTION, (10, 10, 10))
            
            # Temporary file
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(tmp_fd)
            img.save(tmp_path)
            
            final_path = self._draw_text_pillow(tmp_path, text, font_size=52, color="white", position_y_ratio=0.5)
            os.remove(tmp_path)
            
            self._temp_files_to_cleanup.append(final_path)
            return ImageClip(final_path).set_duration(duration).set_fps(VIDEO_FPS)

        bg = ColorClip(size=VIDEO_RESOLUTION, color=(10, 10, 10)).set_duration(duration).set_fps(VIDEO_FPS)

        txt_clip = (
            TextClip(
                text,
                fontsize=52,
                color="white",
                font="Arial-Bold",
                method="caption",
                size=(WIDTH - 160, None),
                align="center",
            )
            .set_position("center")
            .set_duration(duration)
        )

        return CompositeVideoClip([bg, txt_clip], size=VIDEO_RESOLUTION)

    def _draw_text_pillow(
        self,
        image_path: str,
        text: str,
        font_size: int = 48,
        color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 2,
        position_y_ratio: float = 0.5
    ) -> str:
        """Draw text on an image using Pillow and return the path to the new temp image."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size
        
        font = None
        try:
            font_names = ["arial.ttf", "calibri.ttf", "msyh.ttc", "Helvetica.ttf", "times.ttf"]
            for fn in font_names:
                try:
                    font = ImageFont.truetype(fn, font_size)
                    break
                except IOError:
                    continue
            if not font:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Word wrap
        max_width = w - 160
        lines = []
        words = text.split()
        current_line = []
        
        def get_text_width(txt):
            if hasattr(font, 'getbbox'):
                return font.getbbox(txt)[2] - font.getbbox(txt)[0]
            else:
                return draw.textsize(txt, font=font)[0]
                
        def get_text_height(txt):
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(txt)
                return bbox[3] - bbox[1]
            else:
                return draw.textsize(txt, font=font)[1]

        for word in words:
            test_line = " ".join(current_line + [word])
            if get_text_width(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        if not lines:
            lines = [text]

        line_height = get_text_height("A") + 10
        total_height = len(lines) * line_height
        start_y = int(h * position_y_ratio - total_height / 2)

        # Draw glassmorphism backing bar (erase/dark backing strip)
        bg_rect = [60, start_y - 25, w - 60, start_y + total_height + 25]
        draw.rectangle(bg_rect, fill=(10, 10, 12, 160))
        draw.rectangle(bg_rect, outline=(120, 120, 140, 75), width=1)

        for i, line in enumerate(lines):
            line_w = get_text_width(line)
            x = (w - line_w) // 2
            y = start_y + i * line_height
            
            # Draw premium layered shadow (instead of basic hard outline)
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    if dx != 0 or dy != 0:
                        dist = abs(dx) + abs(dy)
                        shadow_alpha = 200 if dist < 3 else 120 if dist < 5 else 60
                        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, shadow_alpha))
                            
            draw.text((x, y), line, fill=color, font=font)

        # Save to temp file
        suffix = Path(image_path).suffix or ".png"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        img.save(tmp_path, quality=95)
        return tmp_path

    def create_slideshow(
        self,
        image_paths: list[str],
        durations: Optional[list[float]] = None,
        transitions: Optional[list[float]] = None,
    ):
        """Build a slideshow clip from images with per-slide timing.

        This is a lower-level helper — ``assemble_reel`` calls it
        internally when you need fine-grained control over individual
        slide durations and transition lengths.

        Args:
            image_paths:  Ordered image file paths.
            durations:    Per-image display durations.  Defaults to
                          ``VIDEO_DURATION_PER_IMAGE`` for every image.
            transitions:  Per-transition crossfade durations (length
                          must be ``len(image_paths) - 1``).  Defaults
                          to 0.6 s each.

        Returns:
            A single composed clip representing the slideshow.
        """
        n = len(image_paths)
        if durations is None:
            durations = [VIDEO_DURATION_PER_IMAGE] * n
        if transitions is None:
            transitions = [0.6] * max(0, n - 1)

        if len(durations) != n:
            raise ValueError(f"Expected {n} durations, got {len(durations)}.")
        if len(transitions) != max(0, n - 1):
            raise ValueError(
                f"Expected {max(0, n - 1)} transitions, got {len(transitions)}."
            )

        resized = [self._resize_image(p) for p in image_paths]
        clips = [
            ImageClip(rp).set_duration(d).set_fps(VIDEO_FPS)
            for rp, d in zip(resized, durations)
        ]

        if len(clips) == 1:
            return clips[0]

        # Layer clips with per-pair crossfade durations
        composed: list = [clips[0].set_start(0)]
        current_time = 0.0
        for i in range(1, len(clips)):
            cf = transitions[i - 1]
            current_time += durations[i - 1] - cf
            composed.append(clips[i].set_start(current_time).crossfadein(cf))

        total = current_time + durations[-1]
        return CompositeVideoClip(composed, size=VIDEO_RESOLUTION).set_duration(total)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resize_image(self, image_path: str) -> str:
        """Resize and letterbox/crop an image to exactly 1080×1920.

        If the source aspect ratio differs from 9:16 the image is
        scaled to *cover* the target area and then centre-cropped,
        ensuring no black bars appear in the final video.

        Args:
            image_path: Path to the source image file.

        Returns:
            Path to the resized image (a temp file if modification was
            needed, otherwise the original path).
        """
        img = Image.open(image_path).convert("RGB")

        if img.size == (WIDTH, HEIGHT):
            return image_path

        # Scale to cover ---------------------------------------------------
        src_w, src_h = img.size
        scale = max(WIDTH / src_w, HEIGHT / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Centre-crop to target --------------------------------------------
        left = (new_w - WIDTH) // 2
        top = (new_h - HEIGHT) // 2
        img = img.crop((left, top, left + WIDTH, top + HEIGHT))

        # Save to temp file ------------------------------------------------
        suffix = Path(image_path).suffix or ".png"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        img.save(tmp_path, quality=95)

        console.log(f"[dim]Resized {Path(image_path).name} → {WIDTH}×{HEIGHT}[/]")
        return tmp_path
