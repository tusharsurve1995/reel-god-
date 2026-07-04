"""
REEL GOD — Cinematic Effects Engine
====================================
Transforms raw video clips into cinematic, anime-styled content with
professional-grade visual effects. Each effect is composable and can be
applied individually or as a curated preset bundle via `apply_style_effects`.

Supported effects:
  • Ken Burns (zoom + pan on stills)
  • Cinematic letterbox (widescreen bars)
  • Color grading (dark_cinematic / emotional / epic_action / mystical / motivational)
  • Fade in / fade out
  • Vignette
  • Particle overlays (dust, rain, snow, sparkle)
  • Camera shake

Dependencies: moviepy, Pillow, numpy, rich
"""

from __future__ import annotations

import math
import random
from typing import Callable, Literal

import numpy as np
from moviepy.editor import (
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    vfx,
)
from PIL import Image, ImageDraw, ImageFilter
from rich.console import Console

# ── Project imports ────────────────────────────────────────────────
import sys
from pathlib import Path

# Ensure the project root is importable regardless of cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import (
    CONTENT_STYLES,
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    VIDEO_DURATION_PER_IMAGE,
    VIDEO_FPS,
    VIDEO_RESOLUTION,
)

# ── Module-level logger ───────────────────────────────────────────
console = Console()

# ── Type aliases ──────────────────────────────────────────────────
PanDirection = Literal["left", "right", "up", "down"]
ParticleType = Literal["dust", "rain", "snow", "sparkle"]
StyleName = Literal[
    "dark_cinematic", "emotional", "epic_action", "mystical", "motivational"
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Cinematic Effects
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class CinematicEffects:
    """Composable cinematic post-processing effects for video clips.

    All public methods accept a MoviePy ``VideoClip`` and return a new
    ``VideoClip`` with the effect applied, keeping the pipeline
    functional and side-effect-free.
    """

    def __init__(self) -> None:
        """Initialise the effects engine with project defaults."""
        self.width: int = VIDEO_RESOLUTION[0]
        self.height: int = VIDEO_RESOLUTION[1]
        self.fps: int = VIDEO_FPS
        console.log("[bold green]✨ CinematicEffects engine initialised[/]")

    # ── 1. Ken Burns ──────────────────────────────────────────────

    def ken_burns(
        self,
        clip: VideoClip,
        zoom_start: float = 1.0,
        zoom_end: float = 1.2,
        pan_direction: PanDirection = "right",
    ) -> VideoClip:
        """Apply a slow zoom + pan (Ken Burns) to a clip.

        Best used on static images converted to ``ImageClip``. The
        camera will smoothly zoom from *zoom_start* → *zoom_end* while
        panning in the given direction.

        Args:
            clip: Source video/image clip.
            zoom_start: Initial zoom factor (1.0 = no zoom).
            zoom_end: Final zoom factor.
            pan_direction: Direction of the pan — ``left``, ``right``,
                ``up``, or ``down``.

        Returns:
            A new ``VideoClip`` with the Ken Burns effect applied.
        """
        console.log(
            f"[cyan]🎥 Ken Burns:[/] zoom {zoom_start}→{zoom_end}, "
            f"pan={pan_direction}"
        )
        w, h = clip.size
        duration = clip.duration

        def _make_frame(get_frame: Callable, t: float) -> np.ndarray:
            """Compute the zoomed & panned frame at time *t*."""
            progress = t / duration if duration > 0 else 0
            zoom = zoom_start + (zoom_end - zoom_start) * progress

            # Crop dimensions inside the (possibly up-scaled) frame
            crop_w = int(w / zoom)
            crop_h = int(h / zoom)

            # Pan offsets
            max_x = w - crop_w
            max_y = h - crop_h

            if pan_direction == "right":
                x = int(max_x * progress)
                y = max_y // 2
            elif pan_direction == "left":
                x = int(max_x * (1 - progress))
                y = max_y // 2
            elif pan_direction == "down":
                x = max_x // 2
                y = int(max_y * progress)
            elif pan_direction == "up":
                x = max_x // 2
                y = int(max_y * (1 - progress))
            else:
                x, y = max_x // 2, max_y // 2

            frame = get_frame(t)
            cropped = frame[y : y + crop_h, x : x + crop_w]

            # Resize back to original dimensions
            pil_img = Image.fromarray(cropped)
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
            return np.array(pil_img)

        return clip.fl(_make_frame)

    # ── 2. Cinematic Letterbox ────────────────────────────────────

    def letterbox(
        self,
        clip: VideoClip,
        bar_ratio: float = 0.12,
    ) -> VideoClip:
        """Add cinematic widescreen black bars (top + bottom).

        Args:
            clip: Source clip.
            bar_ratio: Fraction of the frame height occupied by *each*
                bar (0.12 = 12 % top + 12 % bottom).

        Returns:
            Clip with opaque black bars composited.
        """
        console.log(f"[cyan]🎬 Letterbox:[/] bar_ratio={bar_ratio}")
        w, h = clip.size
        bar_h = int(h * bar_ratio)

        def _add_bars(get_frame: Callable, t: float) -> np.ndarray:
            frame = get_frame(t).copy()
            frame[:bar_h, :] = 0          # top bar
            frame[h - bar_h :, :] = 0     # bottom bar
            return frame

        return clip.fl(_add_bars)

    # ── 3. Color Grading ─────────────────────────────────────────

    def color_grade(self, clip: VideoClip, style: StyleName) -> VideoClip:
        """Apply an anime-inspired colour grade.

        Available styles:
            * ``dark_cinematic`` — desaturated, blue-tinted shadows,
              high contrast.
            * ``emotional`` — warm golden tones, soft, slightly blown
              highlights.
            * ``epic_action`` — vibrant, high saturation, strong
              contrast.
            * ``mystical`` — cool purple/blue tones, ethereal glow.
            * ``motivational`` — warm orange tones, bright, energetic.

        Args:
            clip: Source clip.
            style: One of the five preset names.

        Returns:
            Colour-graded clip.
        """
        graders: dict[str, Callable[[np.ndarray], np.ndarray]] = {
            "dark_cinematic": self._grade_dark_cinematic,
            "emotional": self._grade_emotional,
            "epic_action": self._grade_epic_action,
            "mystical": self._grade_mystical,
            "motivational": self._grade_motivational,
        }
        grader = graders.get(style)
        if grader is None:
            console.log(
                f"[yellow]⚠ Unknown colour grade '{style}', skipping[/]"
            )
            return clip

        console.log(f"[cyan]🎨 Colour grade:[/] {style}")

        def _apply(get_frame: Callable, t: float) -> np.ndarray:
            return grader(get_frame(t))

        return clip.fl(_apply)

    # ·· grade helpers ·········································

    @staticmethod
    def _grade_dark_cinematic(frame: np.ndarray) -> np.ndarray:
        """Desaturated, blue-tinted shadows, crushed blacks."""
        img = frame.astype(np.float64)

        # Desaturate by blending towards luminance
        lum = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
        for c in range(3):
            img[..., c] = img[..., c] * 0.55 + lum * 0.45

        # Blue-tint shadows (pixels below mid-tone)
        shadow_mask = (lum < 100).astype(np.float64)
        img[..., 2] = np.minimum(img[..., 2] + shadow_mask * 25, 255)

        # Boost contrast via simple S-curve
        img = _s_curve(img, strength=1.3)

        # Crush blacks slightly
        img = np.clip(img - 8, 0, 255)
        return img.astype(np.uint8)

    @staticmethod
    def _grade_emotional(frame: np.ndarray) -> np.ndarray:
        """Warm golden tones, softened, blown highlights."""
        img = frame.astype(np.float64)

        # Warm shift: boost red & green slightly
        img[..., 0] = np.minimum(img[..., 0] * 1.08, 255)  # R
        img[..., 1] = np.minimum(img[..., 1] * 1.04, 255)  # G
        img[..., 2] = img[..., 2] * 0.90                    # B ↓

        # Blow highlights — push bright values closer to 255
        bright = img > 200
        img[bright] = img[bright] + (255 - img[bright]) * 0.35

        # Gentle contrast reduction (soften)
        img = img * 0.9 + 25
        return np.clip(img, 0, 255).astype(np.uint8)

    @staticmethod
    def _grade_epic_action(frame: np.ndarray) -> np.ndarray:
        """Vibrant, high saturation, punchy contrast."""
        img = frame.astype(np.float64)

        # Boost saturation via HSV
        pil_img = Image.fromarray(frame)
        hsv = np.array(pil_img.convert("HSV")).astype(np.float64)
        hsv[..., 1] = np.minimum(hsv[..., 1] * 1.4, 255)  # Saturation ↑
        pil_img = Image.fromarray(hsv.astype(np.uint8), mode="HSV").convert("RGB")
        img = np.array(pil_img).astype(np.float64)

        # Strong S-curve contrast
        img = _s_curve(img, strength=1.5)
        return np.clip(img, 0, 255).astype(np.uint8)

    @staticmethod
    def _grade_mystical(frame: np.ndarray) -> np.ndarray:
        """Cool purple/blue tones with an ethereal bloom."""
        img = frame.astype(np.float64)

        # Purple/blue tint
        img[..., 0] = img[..., 0] * 0.92                    # R ↓
        img[..., 2] = np.minimum(img[..., 2] * 1.15, 255)   # B ↑

        # Slight magenta lift in mid-tones
        lum = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
        mid = ((lum > 60) & (lum < 200)).astype(np.float64)
        img[..., 0] = np.minimum(img[..., 0] + mid * 12, 255)

        # Ethereal bloom (simulate with PIL blur blend)
        pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        bloom = pil_img.filter(ImageFilter.GaussianBlur(radius=12))
        bloom_arr = np.array(bloom).astype(np.float64)
        img = img * 0.75 + bloom_arr * 0.25

        return np.clip(img, 0, 255).astype(np.uint8)

    @staticmethod
    def _grade_motivational(frame: np.ndarray) -> np.ndarray:
        """Warm orange tones, bright and energetic."""
        img = frame.astype(np.float64)

        # Orange warmth
        img[..., 0] = np.minimum(img[..., 0] * 1.12, 255)  # R ↑
        img[..., 1] = np.minimum(img[..., 1] * 1.04, 255)  # G slight ↑
        img[..., 2] = img[..., 2] * 0.85                    # B ↓

        # Overall brightness lift
        img = img * 1.08 + 10

        # Mild contrast
        img = _s_curve(img, strength=1.15)
        return np.clip(img, 0, 255).astype(np.uint8)

    # ── 4. Fade In / Out ─────────────────────────────────────────

    def fade_in(self, clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """Smoothly fade a clip in from black.

        Args:
            clip: Source clip.
            duration: Fade duration in seconds.

        Returns:
            Clip with a leading fade-in.
        """
        console.log(f"[cyan]🌅 Fade in:[/] {duration}s")
        return clip.fadein(duration)

    def fade_out(self, clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """Smoothly fade a clip out to black.

        Args:
            clip: Source clip.
            duration: Fade duration in seconds.

        Returns:
            Clip with a trailing fade-out.
        """
        console.log(f"[cyan]🌆 Fade out:[/] {duration}s")
        return clip.fadeout(duration)

    # ── 5. Vignette ──────────────────────────────────────────────

    def vignette(
        self,
        clip: VideoClip,
        intensity: float = 0.5,
    ) -> VideoClip:
        """Darken the edges of each frame to draw focus to the centre.

        Args:
            clip: Source clip.
            intensity: 0.0 = no vignette, 1.0 = heavy darkening.

        Returns:
            Vignetted clip.
        """
        console.log(f"[cyan]🔲 Vignette:[/] intensity={intensity}")
        w, h = clip.size

        # Pre-compute a vignette mask (0–1 float, same shape as frame)
        Y, X = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        radius = math.sqrt(cx**2 + cy**2)
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / radius
        mask = 1.0 - np.clip(dist * intensity, 0, 1)
        mask = mask[..., np.newaxis]  # broadcast over RGB channels

        def _apply(get_frame: Callable, t: float) -> np.ndarray:
            frame = get_frame(t).astype(np.float64)
            return (frame * mask).astype(np.uint8)

        return clip.fl(_apply)

    # ── 6. Particle Overlay ──────────────────────────────────────

    def add_particles(
        self,
        clip: VideoClip,
        particle_type: ParticleType = "dust",
        density: int = 50,
    ) -> VideoClip:
        """Overlay animated particles (dust, rain, snow, sparkle).

        Particles are procedurally generated with PIL so no external
        assets are needed.

        Args:
            clip: Source clip.
            particle_type: Kind of particle to render.
            density: Approximate number of particles per frame.

        Returns:
            Clip with particle overlay composited.
        """
        console.log(
            f"[cyan]✨ Particles:[/] type={particle_type}, density={density}"
        )
        w, h = clip.size
        duration = clip.duration

        # Seed a deterministic particle field
        rng = random.Random(42)
        particles = [
            {
                "x": rng.randint(0, w),
                "y": rng.randint(-h, h),
                "speed": rng.uniform(0.5, 3.0),
                "size": rng.randint(1, 4),
                "alpha": rng.randint(80, 200),
                "drift": rng.uniform(-0.5, 0.5),
            }
            for _ in range(density)
        ]

        def _render_particles(t: float) -> np.ndarray:
            """Draw particles for a single frame at time *t*."""
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            for p in particles:
                # Vertical motion: particles fall / rise over time
                if particle_type == "rain":
                    y = (p["y"] + t * p["speed"] * 600) % (h + 40) - 20
                    x = (p["x"] + t * p["drift"] * 30) % w
                    # Rain streaks
                    draw.line(
                        [(int(x), int(y)), (int(x) - 1, int(y) + 12)],
                        fill=(200, 210, 255, p["alpha"]),
                        width=1,
                    )
                elif particle_type == "snow":
                    y = (p["y"] + t * p["speed"] * 80) % (h + 20) - 10
                    x = (
                        p["x"]
                        + math.sin(t * 2 + p["drift"] * 10) * 20
                    ) % w
                    r = p["size"]
                    draw.ellipse(
                        [int(x) - r, int(y) - r, int(x) + r, int(y) + r],
                        fill=(255, 255, 255, p["alpha"]),
                    )
                elif particle_type == "sparkle":
                    y = (p["y"] + t * p["speed"] * 40) % h
                    x = (p["x"] + math.sin(t * 3 + p["y"]) * 15) % w
                    # Pulsating brightness
                    pulse = int(
                        abs(math.sin(t * 5 + p["alpha"])) * 200 + 55
                    )
                    r = p["size"]
                    draw.ellipse(
                        [int(x) - r, int(y) - r, int(x) + r, int(y) + r],
                        fill=(255, 255, 220, min(pulse, 255)),
                    )
                    # Cross sparkle lines
                    if p["size"] >= 3:
                        line_len = r * 3
                        center = (int(x), int(y))
                        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                            draw.line(
                                [
                                    (center[0] - dx * line_len,
                                     center[1] - dy * line_len),
                                    (center[0] + dx * line_len,
                                     center[1] + dy * line_len),
                                ],
                                fill=(255, 255, 200, min(pulse // 2, 255)),
                                width=1,
                            )
                else:  # dust (default)
                    y = (p["y"] + t * p["speed"] * 30) % h
                    x = (
                        p["x"]
                        + math.sin(t * 1.5 + p["drift"] * 8) * 10
                    ) % w
                    r = p["size"]
                    draw.ellipse(
                        [int(x) - r, int(y) - r, int(x) + r, int(y) + r],
                        fill=(230, 220, 200, p["alpha"] // 2),
                    )

            return np.array(overlay.convert("RGB"))

        # Composite particles directly onto base clip using fl()
        def _composite(get_frame: Callable, t: float) -> np.ndarray:
            base = get_frame(t).astype(np.int16)
            overlay_frame = _render_particles(t).astype(np.int16)
            blended = np.clip(base + overlay_frame, 0, 255)
            return blended.astype(np.uint8)

        return clip.fl(_composite)

    # ── 7. Camera Shake ──────────────────────────────────────────

    def camera_shake(
        self,
        clip: VideoClip,
        intensity: int = 3,
        frequency: int = 15,
    ) -> VideoClip:
        """Add subtle camera shake for action / impact scenes.

        The shake is generated with layered sine waves to feel organic
        rather than purely random.

        Args:
            clip: Source clip.
            intensity: Maximum pixel offset per axis.
            frequency: Shake oscillations per second.

        Returns:
            Clip with camera-shake displacement applied.
        """
        console.log(
            f"[cyan]📳 Camera shake:[/] intensity={intensity}, "
            f"freq={frequency}"
        )
        w, h = clip.size

        def _shake(get_frame: Callable, t: float) -> np.ndarray:
            # Layered sinusoidal offsets for organic motion
            dx = int(
                intensity
                * (
                    math.sin(t * frequency * 2 * math.pi)
                    + 0.5 * math.sin(t * frequency * 3.7 * math.pi)
                )
                / 1.5
            )
            dy = int(
                intensity
                * (
                    math.cos(t * frequency * 2.3 * math.pi)
                    + 0.5 * math.cos(t * frequency * 4.1 * math.pi)
                )
                / 1.5
            )
            frame = get_frame(t)
            shifted = np.zeros_like(frame)

            # Source / destination slicing with boundary clamping
            src_y0 = max(-dy, 0)
            src_y1 = min(h - dy, h)
            src_x0 = max(-dx, 0)
            src_x1 = min(w - dx, w)
            dst_y0 = max(dy, 0)
            dst_y1 = min(h + dy, h)
            dst_x0 = max(dx, 0)
            dst_x1 = min(w + dx, w)

            # Ensure shapes match (handle edge rounding)
            copy_h = min(src_y1 - src_y0, dst_y1 - dst_y0)
            copy_w = min(src_x1 - src_x0, dst_x1 - dst_x0)
            if copy_h > 0 and copy_w > 0:
                shifted[
                    dst_y0 : dst_y0 + copy_h, dst_x0 : dst_x0 + copy_w
                ] = frame[
                    src_y0 : src_y0 + copy_h, src_x0 : src_x0 + copy_w
                ]

            return shifted

        return clip.fl(_shake)

    # ── 8. Unified Style Applicator ──────────────────────────────

    def apply_style_effects(
        self,
        clip: VideoClip,
        style: StyleName,
    ) -> VideoClip:
        """Apply a curated bundle of effects for a given anime style.

        Each style activates a specific combination of colour grading,
        vignette, particles, Ken Burns, fade, and letterbox — tuned
        to match the mood of the content.

        Args:
            clip: Source clip.
            style: One of ``dark_cinematic``, ``emotional``,
                ``epic_action``, ``mystical``, ``motivational``.

        Returns:
            Fully-styled clip ready for export.
        """
        console.log(f"[bold magenta]🎬 Applying style bundle:[/] {style}")

        if style == "dark_cinematic":
            clip = self.color_grade(clip, "dark_cinematic")
            clip = self.vignette(clip, intensity=0.7)
            clip = self.letterbox(clip, bar_ratio=0.10)
            clip = self.add_particles(clip, particle_type="dust", density=35)
            clip = self.ken_burns(clip, zoom_start=1.0, zoom_end=1.15, pan_direction="left")
            clip = self.fade_in(clip, duration=1.2)
            clip = self.fade_out(clip, duration=1.5)

        elif style == "emotional":
            clip = self.color_grade(clip, "emotional")
            clip = self.vignette(clip, intensity=0.4)
            clip = self.letterbox(clip, bar_ratio=0.12)
            clip = self.add_particles(clip, particle_type="dust", density=20)
            clip = self.ken_burns(clip, zoom_start=1.0, zoom_end=1.10, pan_direction="right")
            clip = self.fade_in(clip, duration=1.5)
            clip = self.fade_out(clip, duration=2.0)

        elif style == "epic_action":
            clip = self.color_grade(clip, "epic_action")
            clip = self.vignette(clip, intensity=0.5)
            clip = self.letterbox(clip, bar_ratio=0.08)
            clip = self.camera_shake(clip, intensity=4, frequency=18)
            clip = self.add_particles(clip, particle_type="sparkle", density=40)
            clip = self.ken_burns(clip, zoom_start=1.0, zoom_end=1.25, pan_direction="right")
            clip = self.fade_in(clip, duration=0.8)
            clip = self.fade_out(clip, duration=1.0)

        elif style == "mystical":
            clip = self.color_grade(clip, "mystical")
            clip = self.vignette(clip, intensity=0.45)
            clip = self.letterbox(clip, bar_ratio=0.10)
            clip = self.add_particles(clip, particle_type="snow", density=45)
            clip = self.ken_burns(clip, zoom_start=1.0, zoom_end=1.12, pan_direction="up")
            clip = self.fade_in(clip, duration=1.5)
            clip = self.fade_out(clip, duration=1.8)

        elif style == "motivational":
            clip = self.color_grade(clip, "motivational")
            clip = self.vignette(clip, intensity=0.35)
            clip = self.letterbox(clip, bar_ratio=0.06)
            clip = self.add_particles(clip, particle_type="sparkle", density=30)
            clip = self.ken_burns(clip, zoom_start=1.0, zoom_end=1.18, pan_direction="right")
            clip = self.fade_in(clip, duration=1.0)
            clip = self.fade_out(clip, duration=1.2)

        else:
            console.log(
                f"[yellow]⚠ Unknown style '{style}' — applying minimal "
                f"defaults[/]"
            )
            clip = self.vignette(clip, intensity=0.3)
            clip = self.letterbox(clip, bar_ratio=0.10)
            clip = self.fade_in(clip, duration=1.0)
            clip = self.fade_out(clip, duration=1.0)

        console.log(f"[bold green]✅ Style '{style}' applied successfully[/]")
        return clip


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Private Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _s_curve(img: np.ndarray, strength: float = 1.3) -> np.ndarray:
    """Apply a simple S-curve contrast adjustment.

    Maps pixel values through a sigmoid centred at 128 to increase or
    decrease midtone contrast.

    Args:
        img: Float64 image array (0–255 range).
        strength: >1 increases contrast, <1 flattens it.

    Returns:
        Contrast-adjusted float64 array (clipped 0–255).
    """
    normalised = img / 255.0
    curved = 1.0 / (1.0 + np.exp(-strength * 6 * (normalised - 0.5)))
    return curved * 255.0
