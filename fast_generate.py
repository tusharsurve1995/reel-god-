import os, sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

"""
REEL GOD -- Fast Reel Generator v2 (FFmpeg Direct)
===================================================
Fixes applied vs v1:
  ✅ Text wrapping  — no more side cutoff, auto line-break
  ✅ Volume boost   — loudnorm to -14 LUFS (Instagram standard)
  ✅ Better music   — mood-matched OST tracks downloaded via yt-dlp
  ✅ Higher quality — CRF 20, preset medium for sharper output
  ✅ Larger text    — font 60px with proper safe-zone margins

Usage:
    py fast_generate.py              # epic + emotional + motivational
    py fast_generate.py --all        # all 6 moods
    py fast_generate.py --mood epic_action
    py fast_generate.py --list
"""

import os, sys, subprocess, shutil, json, argparse, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

CLIPS_DIR = ROOT / "data" / "anime_clips"
MUSIC_DIR = ROOT / "data" / "music_library"
ARCHIVE   = ROOT / "data" / "content_archive"

# ─────────────────────────────────────────────────────────────────────────────
#  FFMPEG
# ─────────────────────────────────────────────────────────────────────────────
def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        if ff and Path(ff).exists():
            return ff
    except Exception:
        pass
    local = ROOT / "data" / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)
    raise RuntimeError("FFmpeg not found. pip install imageio-ffmpeg")

FFMPEG = find_ffmpeg()
console.print(f"[dim]FFmpeg: {Path(FFMPEG).name}[/]")


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def find_clips(anime: str, style: str) -> list:
    clips = [f for f in CLIPS_DIR.glob("*.mp4")
             if anime.lower() in f.name.lower() and style.lower() in f.name.lower()]
    if not clips:
        clips = [f for f in CLIPS_DIR.glob("*.mp4") if anime.lower() in f.name.lower()]
    return sorted(clips, key=lambda x: x.stat().st_size, reverse=True)


def find_music(preferred_file: str, style: str) -> Path | None:
    """Try preferred file first, then style-matched, then any mp3."""
    # 1. Preferred specific file (e.g. newly downloaded OST)
    pref = MUSIC_DIR / preferred_file
    if pref.exists() and pref.stat().st_size > 50_000:
        return pref
    # 2. Style-name match
    for f in sorted(MUSIC_DIR.glob("*.mp3"), key=lambda x: x.stat().st_size):
        if style.lower() in f.name.lower() and f.stat().st_size > 50_000:
            return f
    # 3. Any mp3
    mp3s = [f for f in MUSIC_DIR.glob("*.mp3") if f.stat().st_size > 50_000]
    return mp3s[0] if mp3s else None


def video_duration(path: Path) -> float:
    """Get video duration via ffprobe / ffmpeg."""
    try:
        ffprobe = FFMPEG.replace("ffmpeg", "ffprobe")
        r = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
            capture_output=True, text=True, timeout=10
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        pass
    try:
        r = subprocess.run([FFMPEG, "-i", str(path)],
                           capture_output=True, text=True, timeout=10)
        import re
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    except Exception:
        pass
    return 60.0


# ─────────────────────────────────────────────────────────────────────────────
#  TEXT WRAPPING  — prevents side cutoff
# ─────────────────────────────────────────────────────────────────────────────
def wrap_for_ffmpeg(text: str, max_chars: int = 24) -> str:
    """
    Wrap subtitle text so it never overflows the 1080px canvas.
    Returns a string with literal \\n separators for FFmpeg drawtext.
    font_size=60 → ~32px/char → max ~34 chars in 1080px with 5% margins (1080*0.90/32≈30)
    We use 24 chars for safety — two comfortable lines for any text.
    """
    if len(text) <= max_chars:
        return text
    # Try smart wrap first
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip() if cur else w
        if len(test) <= max_chars:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # FFmpeg uses literal \n in text= parameter
    return r"\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR GRADES
# ─────────────────────────────────────────────────────────────────────────────
GRADE_FILTERS = {
    "epic_action":    "eq=contrast=1.25:saturation=0.85:brightness=-0.02,curves=r='0/0 0.5/0.58 1/1':b='0/0 0.5/0.42 1/1'",
    "emotional":      "eq=contrast=1.08:saturation=0.70:brightness=0.01,curves=b='0/0 0.5/0.54 1/1'",
    "motivational":   "eq=contrast=1.2:saturation=1.15:brightness=0.02,curves=r='0/0 0.5/0.52 1/1'",
    "dark_cinematic": "eq=contrast=1.35:saturation=0.55:brightness=-0.06,curves=r='0/0 0.5/0.48 1/0.92'",
    "romance":        "eq=contrast=1.08:saturation=1.1:brightness=0.03,curves=r='0/0 0.5/0.58 1/1':g='0/0 0.5/0.52 1/1'",
    "sacrifice":      "eq=contrast=1.30:saturation=0.60:brightness=-0.05,curves=r='0/0 0.5/0.52 1/0.96'",
}


# ─────────────────────────────────────────────────────────────────────────────
#  DRAWTEXT FILTER BUILDER  — safe margins, wrapped text
# ─────────────────────────────────────────────────────────────────────────────
def build_drawtext_filter(subtitles: list, w: int, h: int, style: str) -> str:
    """
    Build chained drawtext filter with:
    - Wrapped text (no side overflow)
    - Bold font, large size
    - Shadow + semi-transparent box
    - Safe vertical position (72% for strong styles, 65% for soft)
    - Horizontal margins (text centred within safe zone)
    """
    is_strong = style in ("epic_action", "motivational", "sacrifice", "dark_cinematic")

    # Font size: big and readable
    font_size  = 62 if is_strong else 56
    font_color = "white"
    shadow_x, shadow_y = 3, 3

    # Vertical position
    y_pct = 0.73 if is_strong else 0.65
    y_pos = int(h * y_pct)

    # Max chars per line based on canvas width and font size
    # At 62px, avg char width ≈ 33px. Safe width = w * 0.88 = 950px → ~28 chars
    # At 56px, avg char width ≈ 30px. Safe width = w * 0.88 = 950px → ~31 chars
    max_chars = 26 if is_strong else 28

    parts = []
    for (t_start, t_end, raw_text) in subtitles:
        wrapped = wrap_for_ffmpeg(raw_text, max_chars=max_chars)

        # Escape special chars FFmpeg drawtext cannot handle
        safe = (wrapped
                .replace("\\", "\\\\")  # backslash must be first
                .replace("'",  "\u2019")  # curly apostrophe (safe)
                .replace(":",  "\\:")
                .replace(",",  "\\,")
                .replace("[",  "\\[")
                .replace("]",  "\\]")
                .replace("%",  "\\%"))

        part = (
            f"drawtext=text='{safe}'"
            f":fontsize={font_size}"
            f":fontcolor={font_color}"
            f":shadowcolor=black@0.9:shadowx={shadow_x}:shadowy={shadow_y}"
            f":x=(w-text_w)/2"            # centred horizontally
            f":y={y_pos}"
            f":enable='between(t\\,{t_start}\\,{t_end})'"
            f":box=1:boxcolor=black@0.50:boxborderw=14"
            f":line_spacing=8"
        )
        parts.append(part)

    return ",".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  PLANS  — mood, clips, music, subtitles (pre-checked length)
# ─────────────────────────────────────────────────────────────────────────────
PLANS = [
    {
        "name":           "EPIC — Demon Slayer",
        "mood":           "epic_action",
        "anime":          "demon_slayer",
        "style":          "epic_action",
        "w": 1080, "h": 1920,
        "music_file":     "epic_action_Rmtx9slmodw.mp3",   # user-approved ✅
        "subtitles": [
            (0.0,  4.5,  "They called him weak."),
            (4.5,  9.5,  "He came back with Total Concentration."),
            (9.5,  14.5, "Every breath. Every strike. Pure fire."),
            (14.5, 20.0, "SET YOUR HEART ABLAZE"),
            (20.0, 25.0, "This is where legends are born."),
        ],
        "caption": "Set your heart ablaze and burn brighter than the sun\n#DemonSlayer #AnimeEdit #EpicAnime #KimetsuNoYaiba #AnimeReels #TanjiroKamado",
    },
    {
        "name":           "EMOTIONAL — Violet Evergarden",
        "mood":           "emotional",
        "anime":          "violet_evergarden",
        "style":          "emotional",
        "w": 1080, "h": 1920,
        "music_file":     "emotional_violet_evergarden_ost.mp3",  # newly downloaded
        "subtitles": [
            (0.0,  4.5,  "She was a weapon. Taught only to fight."),
            (4.5,  9.5,  "Then she learned what words truly are."),
            (9.5,  14.5, "Each letter she wrote held a soul."),
            (14.5, 20.0, "THANK YOU FOR A LIFE TO LOVE"),
            (20.0, 25.0, "Some goodbyes take a lifetime to write."),
        ],
        "caption": "Thank you for giving me a life to love\n#VioletEvergarden #AnimeEdit #EmotionalAnime #AnimeReels #TearJerker",
    },
    {
        "name":           "MOTIVATIONAL — Naruto",
        "mood":           "motivational",
        "anime":          "naruto",
        "style":          "motivational",
        "w": 1080, "h": 1920,
        "music_file":     "motivational_naruto_departure.mp3",  # Departure OST
        "subtitles": [
            (0.0,  4.5,  "Every village laughed at him."),
            (4.5,  9.5,  "He trained while others slept."),
            (9.5,  14.5, "He cried alone. He rose alone."),
            (14.5, 20.0, "NEVER GIVE UP. THATS MY NINJA WAY"),
            (20.0, 25.0, "Your story is not over. Keep going."),
        ],
        "caption": "I never give up. That's my ninja way\n#Naruto #NarutoShippuden #AnimeEdit #Motivational #NeverGiveUp #BelieveIt",
    },
    {
        "name":           "SACRIFICE — Attack on Titan",
        "mood":           "sacrifice",
        "anime":          "attack_on_titan",
        "style":          "sacrifice",
        "w": 1080, "h": 1920,
        "music_file":     "sacrifice_aot_ost.mp3",  # Vogel Im Kafig / Call of Silence
        "subtitles": [
            (0.0,  4.5,  "He knew they would not survive."),
            (4.5,  9.5,  "He led them anyway."),
            (9.5,  14.5, "Not for glory. For those who could not."),
            (14.5, 20.0, "GIVE YOUR HEARTS"),
            (20.0, 25.0, "Some heroes are remembered in silence."),
        ],
        "caption": "Give your hearts for the future we believe in\n#AttackOnTitan #AOT #ErwinSmith #AnimeEdit #ShingekiNoKyojin",
    },
    {
        "name":           "ROMANCE — Your Lie in April",
        "mood":           "romantic",
        "anime":          "your_lie_in_april",
        "style":          "romance",
        "w": 1080, "h": 1920,
        "music_file":     "romance_ylia_ost.mp3",  # Watashi no Uso piano
        "subtitles": [
            (0.0,  4.5,  "He never believed in love."),
            (4.5,  9.5,  "Until she played her piano for him."),
            (9.5,  14.5, "She was slowly fading away..."),
            (14.5, 20.0, "YOUR MELODY LIVES IN MY HEART"),
            (20.0, 25.0, "Some love stories never truly end."),
        ],
        "caption": "Your melody lives in my heart\n#YourLieInApril #ShigatsuWaKimiNoUso #AnimeEdit #Romance #EmotionalAnime",
    },
    {
        "name":           "DARK — FMA Brotherhood",
        "mood":           "dark_cinematic",
        "anime":          "fullmetal_alchemist",
        "style":          "dark_cinematic",
        "w": 1080, "h": 1920,
        "music_file":     "dark_fma_brotherhood_ost.mp3",  # Lapis Philosophorum
        "subtitles": [
            (0.0,  4.5,  "They broke the only rule that mattered."),
            (4.5,  9.5,  "And paid a price beyond imagination."),
            (9.5,  14.5, "But they never stopped moving forward."),
            (14.5, 20.0, "TO OBTAIN — EQUAL MUST BE LOST"),
            (20.0, 25.0, "That is the price of becoming great."),
        ],
        "caption": "To obtain, something of equal value must be lost\n#FMABrotherhood #FullmetalAlchemist #AnimeEdit #DarkAnime #EquivalentExchange",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  CORE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def generate_reel(plan: dict) -> Path | None:
    anime   = plan["anime"]
    style   = plan["style"]
    mood    = plan["mood"]
    w, h    = plan["w"], plan["h"]
    subs    = plan["subtitles"]
    total_dur = subs[-1][1]

    # ── Resources
    clips = find_clips(anime, style)
    if not clips:
        console.print(f"  [red]No clips for {anime}[/]")
        return None
    src_video = clips[0]
    music     = find_music(plan["music_file"], style)

    console.print(f"  Clip : [cyan]{src_video.name}[/]")
    if music:
        console.print(f"  Music: [green]{music.name}[/]")
    else:
        console.print("  Music: [red]none found[/]")

    src_dur = video_duration(src_video)
    start_offset = max(0, src_dur * 0.10)
    if src_dur - start_offset < total_dur:
        start_offset = max(0, src_dur - total_dur - 2)

    # ── Output
    out_dir = ARCHIVE / mood
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{mood}_{anime}_{style}.mp4"

    # ── Build video filter
    grade  = GRADE_FILTERS.get(style, "eq=contrast=1.1:saturation=1.0")
    dtexts = build_drawtext_filter(subs, w, h, style)

    # Scale to fill → crop to target → grade → subtitles
    if w == h:
        scale_str = (f"scale='if(gt(iw/ih,1),{h}*iw/ih,{w})':"
                     f"'if(gt(iw/ih,1),{h},{w}*ih/iw)'")
    else:
        # 9:16: fill while preserving ratio, then centre-crop
        scale_str = (f"scale='if(gt(iw/ih,9/16),{h}*iw/ih,{w})':"
                     f"'if(gt(iw/ih,9/16),{h},{w}*ih/iw)'")

    vf = f"{scale_str},crop={w}:{h},{grade},{dtexts}"

    # ── FFmpeg command
    cmd = [FFMPEG, "-y",
           "-ss", str(start_offset),
           "-i",  str(src_video)]

    if music:
        cmd += ["-i", str(music)]

    cmd += ["-vf", vf, "-t", str(total_dur)]

    # Video encoding — higher quality
    cmd += [
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",            # sharper than before (was 23)
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]

    # Audio — volume boost + loudnorm to -14 LUFS (Instagram standard)
    if music:
        cmd += [
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:a", "aac",
            "-b:a", "192k",
            # Boost volume 4x then normalize to -14 LUFS
            "-af", "volume=4.0,loudnorm=I=-14:LRA=11:TP=-1.5",
            "-shortest",
        ]
    else:
        cmd += ["-an"]

    cmd.append(str(out_path))

    # ── Run FFmpeg
    console.print("  [dim]Running FFmpeg...[/]")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            console.print(f"  [red]FFmpeg error (code {result.returncode}):[/]")
            for line in result.stderr.strip().split("\n")[-25:]:
                if any(k in line.lower() for k in ["error", "invalid", "unable", "cannot", "failed"]):
                    console.print(f"  [dim red]{line}[/]")
            return None

        if not out_path.exists() or out_path.stat().st_size < 50_000:
            console.print(f"  [red]Output missing or too small ({out_path.stat().st_size if out_path.exists() else 0} bytes)[/]")
            return None

        size_mb = out_path.stat().st_size / 1_000_000
        console.print(f"  [bold green]DONE: {out_path.name} ({size_mb:.1f} MB)[/]")

        # Metadata JSON
        out_path.with_suffix(".json").write_text(
            json.dumps({
                "title": plan["name"], "anime": anime, "style": style, "mood": mood,
                "music": str(music) if music else None,
                "caption": plan["caption"],
                "subtitles": [{"start": s, "end": e, "text": t} for s, e, t in subs],
                "resolution": f"{w}x{h}",
            }, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Thumbnail
        try:
            thumb = out_path.with_suffix(".jpg")
            subprocess.run([
                FFMPEG, "-y", "-ss", "3", "-i", str(out_path),
                "-vframes", "1", "-q:v", "2", str(thumb)
            ], capture_output=True, timeout=15)
            if thumb.exists():
                console.print(f"  [dim]Thumbnail: {thumb.name}[/]")
        except Exception:
            pass

        return out_path

    except subprocess.TimeoutExpired:
        console.print("  [red]FFmpeg timed out (5 min)[/]")
        return None
    except Exception as ex:
        console.print(f"  [red]{ex}[/]")
        return None


# ─────────────────────────────────────────────────────────────────────────────
def print_inventory():
    t = Table(title="Clip & Music Inventory", border_style="cyan")
    t.add_column("Plan", style="bold"); t.add_column("Clips"); t.add_column("Music File")
    for p in PLANS:
        clips = find_clips(p["anime"], p["style"])
        music = find_music(p["music_file"], p["style"])
        t.add_row(
            p["name"],
            f"[green]YES ({len(clips)})[/]" if clips else "[red]NONE[/]",
            f"[green]{music.name[:40]}[/]" if music else "[red]MISSING[/]"
        )
    console.print(t)


def main():
    parser = argparse.ArgumentParser(description="REEL GOD — Fast Generate v2")
    parser.add_argument("--mood",    type=str, default=None)
    parser.add_argument("--all",     action="store_true")
    parser.add_argument("--list",    action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]REEL GOD — FAST GENERATE v2[/]\n"
        "[dim]Fixed: text wrapping | volume boost | mood-matched music[/]",
        border_style="cyan"
    ))

    if args.list:
        print_inventory(); return

    if args.all:
        selected = PLANS
    elif args.mood:
        selected = [p for p in PLANS if p["mood"] == args.mood or p["style"] == args.mood]
        if not selected:
            console.print(f"[red]Unknown mood: {args.mood}[/]")
            console.print(f"Choices: {', '.join(p['mood'] for p in PLANS)}")
            return
    else:
        selected = [p for p in PLANS if p["mood"] in ("epic_action", "emotional", "motivational")]

    print_inventory()
    console.print()

    if args.dry_run:
        console.print("[yellow]DRY RUN — no generation[/]")
        return

    results, failed = [], []
    for i, plan in enumerate(selected, 1):
        console.print(f"\n{'='*60}")
        console.print(Panel(
            f"[bold]{plan['name']}[/]",
            border_style="magenta"
        ))
        console.print(f"  Reel {i}/{len(selected)} | {plan['mood']} | {plan['w']}x{plan['h']}")
        r = generate_reel(plan)
        if r:
            results.append(r)
        else:
            failed.append(plan["name"])

    console.print(f"\n{'='*60}")
    lines = [f"[bold green]{len(results)}/{len(selected)} reels ready[/]"]
    if failed:
        lines.append(f"[red]Failed: {', '.join(failed)}[/]")
    lines.append(f"\nAll files in: {ARCHIVE}")
    for r in results:
        lines.append(f"  OK: {r.parent.name}/{r.name}  ({r.stat().st_size/1e6:.1f} MB)")
    console.print(Panel("\n".join(lines), title="COMPLETE", border_style="green"))


if __name__ == "__main__":
    main()
