"""
REEL GOD — Quick Generate (Uses Local Clips)
============================================
Generates reels using already-downloaded anime clips + music in data/.
No internet required. Runs immediately.

Usage:
    py quick_generate.py                    # Generate 3 reels (epic, emotional, motivational)
    py quick_generate.py --mood epic_action # Only one mood
    py quick_generate.py --all              # All 6 moods
    py quick_generate.py --list             # Show available clips
"""

import os, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Pillow compat monkeypatch ──────────────────────────────────────────────────
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

# ── FFmpeg setup ───────────────────────────────────────────────────────────────
def _setup_ffmpeg():
    import shutil
    if shutil.which("ffmpeg"):
        return True
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and Path(ffmpeg_path).exists():
            local_bin = ROOT / "data" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)
            local_ff = local_bin / "ffmpeg.exe"
            if not local_ff.exists():
                import shutil as sh
                sh.copy2(ffmpeg_path, local_ff)
            os.environ["PATH"] = str(local_bin) + os.pathsep + os.environ.get("PATH", "")
            os.environ["FFMPEG_BINARY"] = str(local_ff)
            try:
                import moviepy.config as mpy_cfg
                mpy_cfg.FFMPEG_BINARY = str(local_ff)
            except Exception:
                pass
            return True
    except Exception as e:
        print(f"[WARN] FFmpeg setup: {e}")
    return False

_setup_ffmpeg()

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
#  LOCAL RESOURCE DIRS
# ─────────────────────────────────────────────────────────────────────────────

CLIPS_DIR = ROOT / "data" / "anime_clips"
MUSIC_DIR = ROOT / "data" / "music_library"
ARCHIVE   = ROOT / "data" / "content_archive"


def find_clips_for(anime: str, style: str) -> list:
    results = []
    for f in CLIPS_DIR.glob("*.mp4"):
        name = f.name.lower()
        if anime.lower() in name and style.lower() in name:
            results.append(f)
    return sorted(results, key=lambda x: x.stat().st_size, reverse=True)


def find_music_for(style: str) -> Path | None:
    for f in MUSIC_DIR.glob("*.mp3"):
        if style.lower() in f.name.lower():
            return f
    mp3s = list(MUSIC_DIR.glob("*.mp3"))
    return mp3s[0] if mp3s else None


# ─────────────────────────────────────────────────────────────────────────────
#  REEL PLANS
# ─────────────────────────────────────────────────────────────────────────────

PLANS = [
    {
        "name":         "EPIC — Demon Slayer",
        "mood":         "epic_action",
        "anime":        "demon_slayer",
        "style":        "epic_action",
        "aspect_ratio": "9:16",
        "title":        "Set Your Heart Ablaze",
        "purpose":      "For when you need to feel unstoppable",
        "narrative": [
            {"text": "They called him weak.",                   "duration": 4.5},
            {"text": "He came back with Total Concentration.",  "duration": 5.0},
            {"text": "Every breath. Every strike. Pure fire.",  "duration": 5.0},
            {"text": "SET YOUR HEART ABLAZE",                   "duration": 5.5},
            {"text": "This is where legends are born.",         "duration": 5.0},
        ],
        "caption": "Set your heart ablaze and burn brighter than the sun\n#DemonSlayer #AnimeEdit #EpicAnime #KimetsuNoYaiba #AnimeReels #TanjiroKamado #AnimeMotivation #Unstoppable",
    },
    {
        "name":         "EMOTIONAL — Violet Evergarden",
        "mood":         "emotional",
        "anime":        "violet_evergarden",
        "style":        "emotional",
        "aspect_ratio": "9:16",
        "title":        "The Last Letter",
        "purpose":      "For people who never got to say goodbye",
        "narrative": [
            {"text": "She was a weapon. Taught only to fight.", "duration": 4.5},
            {"text": "Then she learned what words truly are.",  "duration": 5.0},
            {"text": "Each letter she wrote... held a soul.",   "duration": 5.0},
            {"text": "THANK YOU FOR A LIFE TO LOVE",            "duration": 5.5},
            {"text": "Some goodbyes take a lifetime to write.", "duration": 5.0},
        ],
        "caption": "Thank you for giving me a life to love\n#VioletEvergarden #AnimeEdit #EmotionalAnime #AnimeReels #TearJerker #AnimeStory #LoveLetters #AnimeFeels",
    },
    {
        "name":         "MOTIVATIONAL — Naruto",
        "mood":         "motivational",
        "anime":        "naruto",
        "style":        "motivational",
        "aspect_ratio": "9:16",
        "title":        "Believe It",
        "purpose":      "For everyone who feels like giving up today",
        "narrative": [
            {"text": "Every village laughed at him.",           "duration": 4.5},
            {"text": "He trained while others slept.",          "duration": 5.0},
            {"text": "He cried alone. He rose alone.",          "duration": 5.0},
            {"text": "NEVER GIVE UP. THATS MY NINJA WAY",       "duration": 5.5},
            {"text": "Your story is not over. Keep going.",     "duration": 5.0},
        ],
        "caption": "I never give up. That's my ninja way\n#Naruto #NarutoShippuden #AnimeEdit #Motivational #NeverGiveUp #BelieveIt #AnimeReels #NinjaWay #Inspirational",
    },
    {
        "name":         "SACRIFICE — Attack on Titan",
        "mood":         "sacrifice",
        "anime":        "attack_on_titan",
        "style":        "dark_cinematic",
        "aspect_ratio": "9:16",
        "title":        "Erwin's Last Charge",
        "purpose":      "For those who gave everything for others",
        "narrative": [
            {"text": "He knew they would not survive.",         "duration": 4.5},
            {"text": "He led them anyway.",                     "duration": 5.0},
            {"text": "Not for glory. For those who could not.", "duration": 5.0},
            {"text": "GIVE YOUR HEARTS",                        "duration": 5.5},
            {"text": "Some heroes are remembered in silence.",  "duration": 5.0},
        ],
        "caption": "Give your hearts for the future we believe in\n#AttackOnTitan #AOT #ErwinSmith #AnimeEdit #DarkAnime #AnimeReels #Sacrifice #ShingekiNoKyojin #Heroism",
    },
    {
        "name":         "ROMANCE — Your Lie in April",
        "mood":         "romantic",
        "anime":        "your_lie_in_april",
        "style":        "romance",
        "aspect_ratio": "1:1",
        "title":        "Love Between Every Note",
        "purpose":      "For those who loved someone so deeply it changed them",
        "narrative": [
            {"text": "He never believed in love.",              "duration": 4.5},
            {"text": "Until she played her piano for him.",     "duration": 5.0},
            {"text": "She was fading away...",                  "duration": 5.0},
            {"text": "YOUR MELODY LIVES IN MY HEART",           "duration": 5.5},
            {"text": "Some love stories never truly end.",      "duration": 5.0},
        ],
        "caption": "Your melody lives in my heart\n#YourLieInApril #ShigatsuWaKimiNoUso #AnimeEdit #Romance #AnimeRomance #LoveAnime #EmotionalAnime #Piano",
    },
    {
        "name":         "DARK — FMA Brotherhood",
        "mood":         "dark_cinematic",
        "anime":        "fullmetal_alchemist",
        "style":        "dark_cinematic",
        "aspect_ratio": "9:16",
        "title":        "Equivalent Exchange",
        "purpose":      "Nothing in life is free. That is what makes it worth fighting for",
        "narrative": [
            {"text": "They broke the only rule that mattered.", "duration": 4.5},
            {"text": "And paid a price they did not expect.",   "duration": 5.0},
            {"text": "But they never stopped moving forward.",  "duration": 5.0},
            {"text": "TO OBTAIN - EQUAL MUST BE LOST",          "duration": 5.5},
            {"text": "That is the price of becoming great.",    "duration": 5.0},
        ],
        "caption": "To obtain, something of equal value must be lost\n#FMABrotherhood #FullmetalAlchemist #AnimeEdit #DarkAnime #EquivalentExchange #EdwardElric #AnimeReels #Legendary",
    },
]

# ─────────────────────────────────────────────────────────────────────────────

def print_inventory():
    t = Table(title="Available Local Clips", border_style="cyan")
    t.add_column("Plan", style="bold")
    t.add_column("Clips Found")
    t.add_column("Music Found")
    for plan in PLANS:
        clips = find_clips_for(plan["anime"], plan["style"])
        # broader search if none
        if not clips:
            clips = [f for f in CLIPS_DIR.glob("*.mp4") if plan["anime"] in f.name.lower()]
        music = find_music_for(plan["style"])
        t.add_row(
            plan["name"],
            f"YES ({len(clips)})" if clips else "NO",
            f"YES - {music.name[:30]}" if music else "NO",
        )
    console.print(t)


def generate_one(plan: dict) -> Path | None:
    from generator.reel_composer import ReelComposer

    anime = plan["anime"]
    style = plan["style"]
    mood  = plan["mood"]

    clips = find_clips_for(anime, style)
    if not clips:
        # broader: any file containing the anime name
        clips = [f for f in CLIPS_DIR.glob("*.mp4") if anime in f.name.lower()]

    if not clips:
        console.print(f"  [red]No local clip found for {anime}/{style}. Skipping.[/]")
        return None

    video_path = clips[0]
    console.print(f"  Clip    : {video_path.name}")

    music_path = find_music_for(style)
    if music_path:
        console.print(f"  Music   : {music_path.name}")
    else:
        console.print("  Music   : none (silent)")

    out_dir = ARCHIVE / mood
    out_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"{mood}_{anime}_{style}.mp4"

    reel_meta = {
        "style":        style,
        "anime":        anime,
        "mood":         mood,
        "title":        plan["title"],
        "caption":      plan["caption"],
        "aspect_ratio": plan["aspect_ratio"],
        "narrative":    plan["narrative"],
    }

    composer = ReelComposer()
    result = composer.compose_reel(video_path, music_path, reel_meta, output_name)

    if result and result.exists():
        size_mb = result.stat().st_size / 1_000_000
        console.print(f"  [bold green]SAVED: {result} ({size_mb:.1f} MB)[/]")
    else:
        console.print("  [red]Composition failed[/]")
        result = None

    return result


def main():
    parser = argparse.ArgumentParser(description="REEL GOD Quick Generate")
    parser.add_argument("--mood",    type=str, default=None)
    parser.add_argument("--all",     action="store_true")
    parser.add_argument("--list",    action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]REEL GOD - QUICK GENERATE[/]\n"
        "[dim]Using local clips + music - no internet needed[/]",
        border_style="cyan"
    ))

    if args.list:
        print_inventory()
        return

    if args.all:
        selected = PLANS
    elif args.mood:
        selected = [p for p in PLANS if p["mood"] == args.mood or p["style"] == args.mood]
        if not selected:
            console.print(f"[red]No plan for mood: {args.mood}[/]")
            return
    else:
        # Default: 3 reels
        selected = [p for p in PLANS if p["mood"] in ("epic_action", "emotional", "motivational")]

    print_inventory()
    console.print()

    if args.dry_run:
        console.print("[yellow]DRY RUN complete[/]")
        return

    results = []
    failed  = []

    for i, plan in enumerate(selected, 1):
        console.print(f"\n{'='*60}")
        console.print(Panel(
            f"[bold]{plan['name']}[/]\n[dim]{plan['purpose']}[/]",
            border_style="magenta"
        ))
        console.print(f"  Reel {i}/{len(selected)} | Mood: {plan['mood']} | Format: {plan['aspect_ratio']}")

        r = generate_one(plan)
        if r:
            results.append(r)
        else:
            failed.append(plan["name"])

    console.print(f"\n{'='*60}")
    lines = [f"[bold green]{len(results)} reel(s) generated[/]"]
    if failed:
        lines.append(f"[red]{len(failed)} failed: {', '.join(failed)}[/]")
    lines.append(f"\nOutput folder: {ARCHIVE}")
    for r in results:
        size_mb = r.stat().st_size / 1_000_000
        lines.append(f"  -> {r.name} ({size_mb:.1f} MB)")

    console.print(Panel("\n".join(lines), title="DONE", border_style="green"))


if __name__ == "__main__":
    main()
