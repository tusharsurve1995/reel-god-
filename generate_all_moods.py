"""
REEL GOD — Generate All Moods
==============================
Master script that generates 6 emotional reels (one per mood category),
each saved to its proper mood folder with full metadata, thumbnail, and caption.

Moods covered:
  1. romantic      → Your Lie in April  × Bollywood/Hollywood piano love
  2. emotional     → Violet Evergarden  × orchestral tearjerker
  3. motivational  → Naruto             × Bollywood rise anthem
  4. sacrifice     → Attack on Titan    × heroic Hollywood orchestra
  5. dark_cinematic→ FMA Brotherhood    × Gladiator/Rang De Basanti
  6. epic_action   → Demon Slayer       × Two Steps From Hell / Gurenge

Run:
  py generate_all_moods.py            # Generate all 6 moods
  py generate_all_moods.py --mood romantic   # Only one mood
  py generate_all_moods.py --dry-run  # Show plan without generating
"""

import os, sys, json, copy, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Pillow compat ─────────────────────────────────────────────────────────────
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from dotenv import load_dotenv
load_dotenv()


def _setup_ffmpeg():
    import shutil as sh
    if sh.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and Path(ffmpeg_path).exists():
            local_bin = ROOT / "data" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)
            local_ff = local_bin / "ffmpeg.exe"
            if not local_ff.exists():
                shutil.copy2(ffmpeg_path, local_ff)
            os.environ["PATH"] = str(local_bin) + os.pathsep + os.environ.get("PATH", "")
            os.environ["FFMPEG_BINARY"] = str(local_ff)
            try:
                import moviepy.config as mpy_cfg
                mpy_cfg.FFMPEG_BINARY = str(local_ff)
            except Exception:
                pass
    except Exception:
        pass


_setup_ffmpeg()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
#  CONTENT PLANS — 6 moods, each with a unique purpose and emotional arc
# ─────────────────────────────────────────────────────────────────────────────

MOOD_PLANS = [
    # ── 1. ROMANTIC ──────────────────────────────────────────────────────────
    {
        "mood":          "romantic",
        "anime":         "your_lie_in_april",
        "style":         "romance",
        "music":         "bollywood",
        "aspect_ratio":  "1:1",
        "title":         "Love Between Every Note",
        "quote":         "Your melody lives in my heart 🎵",
        "purpose":       "For people who loved someone so deeply it changed who they are",
        "music_name":    "Tujhe Kitna Chahne Lage — Piano Cover",
        "narrative": [
            {"text": "He never believed in love.",              "duration": 4.5},
            {"text": "Until she played her piano for him.",     "duration": 5.0},
            {"text": "She was fading away...",                  "duration": 5.0},
            {"text": "YOUR MELODY LIVES IN MY HEART 🎵",        "duration": 5.5},
            {"text": "Some love stories never truly end. 💕",   "duration": 5.0},
        ],
    },

    # ── 2. EMOTIONAL ─────────────────────────────────────────────────────────
    {
        "mood":          "emotional",
        "anime":         "violet_evergarden",
        "style":         "emotional",
        "music":         "hollywood",
        "aspect_ratio":  "9:16",
        "title":         "The Last Letter",
        "quote":         "Thank you for giving me a life to love 💛",
        "purpose":       "For people who never got to say goodbye to someone they loved",
        "music_name":    "Violet Evergarden OST — Piano",
        "narrative": [
            {"text": "She was a weapon. Taught only to fight.", "duration": 4.5},
            {"text": "Then she learned what words truly are.",   "duration": 5.0},
            {"text": "Each letter she wrote... held a soul.",    "duration": 5.0},
            {"text": "THANK YOU FOR GIVING ME A LIFE TO LOVE 💛","duration": 5.5},
            {"text": "Some goodbyes take a lifetime to write. 💙","duration": 5.0},
        ],
    },

    # ── 3. MOTIVATIONAL ──────────────────────────────────────────────────────
    {
        "mood":          "motivational",
        "anime":         "naruto",
        "style":         "motivational",
        "music":         "bollywood",
        "aspect_ratio":  "9:16",
        "title":         "Believe It",
        "quote":         "I never give up. That's my ninja way 🌀",
        "purpose":       "For everyone who feels like giving up today — this is for you",
        "music_name":    "Kar Har Maidan Fateh — Instrumental",
        "narrative": [
            {"text": "Every village laughed at him.",            "duration": 4.5},
            {"text": "He trained while others slept.",           "duration": 5.0},
            {"text": "He cried alone. He rose alone.",           "duration": 5.0},
            {"text": "I NEVER GIVE UP. THAT'S MY NINJA WAY 🌀",  "duration": 5.5},
            {"text": "Your story isn't over. Keep going. 🔥",    "duration": 5.0},
        ],
    },

    # ── 4. SACRIFICE ─────────────────────────────────────────────────────────
    {
        "mood":          "sacrifice",
        "anime":         "attack_on_titan",
        "style":         "sacrifice",
        "music":         "hollywood",
        "aspect_ratio":  "9:16",
        "title":         "Erwin's Last Charge",
        "quote":         "Give your hearts — for the future we believe in 🗡️",
        "purpose":       "For everyone who gave everything for people they loved",
        "music_name":    "Avengers Endgame — Portals (Hans Zimmer Style)",
        "narrative": [
            {"text": "He knew they wouldn't survive.",           "duration": 4.5},
            {"text": "He led them anyway.",                       "duration": 5.0},
            {"text": "Not for glory. For the ones who couldn't.", "duration": 5.0},
            {"text": "GIVE YOUR HEARTS — FOR THE FUTURE 🗡️",    "duration": 5.5},
            {"text": "Some heroes are remembered in silence. 👑","duration": 5.0},
        ],
    },

    # ── 5. DARK CINEMATIC ────────────────────────────────────────────────────
    {
        "mood":          "dark_cinematic",
        "anime":         "fullmetal_alchemist",
        "style":         "dark_cinematic",
        "music":         "bollywood",
        "aspect_ratio":  "9:16",
        "title":         "Equivalent Exchange",
        "quote":         "To obtain, something of equal value must be lost ⚖️",
        "purpose":       "Nothing in life is free — and that's what makes it worth fighting for",
        "music_name":    "Rang De Basanti — Main Theme",
        "narrative": [
            {"text": "They broke the only rule that mattered.",  "duration": 4.5},
            {"text": "And paid a price they didn't expect.",      "duration": 5.0},
            {"text": "But they never stopped moving forward.",    "duration": 5.0},
            {"text": "TO OBTAIN — SOMETHING EQUAL MUST BE LOST ⚖️","duration": 5.5},
            {"text": "That is the price of becoming great. 🌑",  "duration": 5.0},
        ],
    },

    # ── 6. EPIC ACTION ───────────────────────────────────────────────────────
    {
        "mood":          "epic_action",
        "anime":         "demon_slayer",
        "style":         "epic_action",
        "music":         "hollywood",
        "aspect_ratio":  "9:16",
        "title":         "Set Your Heart Ablaze",
        "quote":         "Set your heart ablaze — and burn brighter than the sun 🔥",
        "purpose":       "When you need to feel unstoppable — this is your battle cry",
        "music_name":    "Two Steps From Hell — Heart of Courage",
        "narrative": [
            {"text": "They called him weak.",                     "duration": 4.5},
            {"text": "He came back with Total Concentration.",    "duration": 5.0},
            {"text": "Every breath. Every strike. Pure fire.",    "duration": 5.0},
            {"text": "SET YOUR HEART ABLAZE 🔥",                  "duration": 5.5},
            {"text": "This is where legends are born. ⚔️",       "duration": 5.0},
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────

def print_plan():
    """Print a summary table of the content plan."""
    t = Table(title="🎬 REEL GOD — Content Plan (All 6 Moods)", border_style="cyan")
    t.add_column("#", style="dim")
    t.add_column("Mood", style="bold")
    t.add_column("Anime")
    t.add_column("Title")
    t.add_column("Music")
    t.add_column("Purpose")

    for i, plan in enumerate(MOOD_PLANS, 1):
        t.add_row(
            str(i),
            plan["mood"].upper(),
            plan["anime"].replace("_", " ").title(),
            plan["title"],
            plan["music_name"][:30],
            plan["purpose"][:45] + "..." if len(plan["purpose"]) > 45 else plan["purpose"],
        )
    console.print(t)


def generate_reel(plan: dict, input_clip_override: str = None) -> Path | None:
    """Generate a single reel from a plan dict."""
    from generator.anime_fetcher import AnimeFetcher
    from generator.reel_composer import ReelComposer
    from music.music_fetcher import MusicFetcher
    from instagram.caption_builder import build_caption

    fetcher  = AnimeFetcher()
    composer = ReelComposer()
    music_fx = MusicFetcher()

    anime = plan["anime"]
    style = plan["style"]
    mood  = plan["mood"]
    title = plan["title"]

    console.print(Panel(
        f"[bold magenta]🎬 {title.upper()}[/]\n"
        f"[dim]Mood: {mood} | Anime: {anime}[/]\n"
        f"[cyan italic]{plan['purpose']}[/]",
        border_style="cyan"
    ))

    # 1. Fetch anime clip
    if input_clip_override:
        console.print(f"[bold green]  ✓ Using local input clip override:[/] {input_clip_override}")
        video_path = Path(input_clip_override)
        if not video_path.exists():
            console.print(f"[red]  ✗ Override video file not found: {input_clip_override}[/]")
            return None
    else:
        console.print(f"[yellow]  Fetching {anime} [{style}] clip...[/]")
        video_path = fetcher.fetch_for_anime_and_style(anime, style)
        if not video_path:
            console.print(f"[red]  ✗ Video fetch failed[/]")
            return None


    # 2. Best segment
    start_t, end_t = fetcher.get_best_segment(video_path, target_dur=25.0)

    # 3. Music — anime-specific
    console.print(f"[yellow]  Fetching music: {plan['music_name']}...[/]")
    music_path = music_fx.fetch_for_anime_and_style(anime, style)
    if not music_path:
        music_path = music_fx.fetch_for_style(style)

    # 4. Build caption via caption_builder
    reel_meta_for_caption = {
        **plan,
        "music_name": plan["music_name"],
    }
    caption = build_caption(reel_meta_for_caption, mood=mood, hook_index=0)

    # 5. Build full reel_meta for composer
    reel_meta = {
        **plan,
        "start":    start_t,
        "end":      end_t,
        "caption":  caption,
        "music_name": plan["music_name"],
    }

    # 6. Output filename includes mood folder context
    output_name = f"{mood}_{anime}_{style}.mp4"

    # 7. Compose
    result = composer.compose_reel(video_path, music_path, reel_meta, output_name)

    if result:
        console.print(f"[bold green]  ✓ [{mood.upper()}] reel ready:[/] {result.parent.name}/{result.name}")
    else:
        console.print(f"[red]  ✗ Composition failed[/]")

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="REEL GOD — Generate All Moods")
    parser.add_argument("--mood",    type=str, default=None, help="Generate only this mood (e.g. romantic)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    parser.add_argument("--input-clip", type=str, default=None, help="Path to a specific local raw clip to edit and compile")
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]REEL GOD — MOOD CONTENT GENERATOR[/]\n"
        "[dim]Generating world-class anime reels organized by emotional mood[/]",
        border_style="cyan"
    ))

    # Handle local clip processing override
    if args.input_clip:
        clip_path = Path(args.input_clip)
        if not clip_path.exists():
            console.print(f"[bold red]✗ Input clip file not found:[/] {args.input_clip}")
            return
            
        filename = clip_path.name.lower()
        
        # 1. Detect anime name
        detected_anime = "unknown"
        for a in ["your_lie_in_april", "demon_slayer", "attack_on_titan", "naruto", "violet_evergarden", "re_zero", "jujutsu_kaisen", "fullmetal_alchemist"]:
            if a in filename:
                detected_anime = a
                break
                
        # 2. Detect style and mood
        detected_mood = "happy"
        detected_style = "happy"
        mood_mappings = {
            "romantic": ("romantic", "romance"),
            "romance": ("romantic", "romance"),
            "emotional": ("emotional", "emotional"),
            "sad": ("emotional", "emotional"),
            "motivational": ("motivational", "motivational"),
            "sacrifice": ("sacrifice", "heroic"),
            "heroic": ("sacrifice", "heroic"),
            "epic_action": ("epic_action", "action"),
            "action": ("epic_action", "action"),
            "dark_cinematic": ("dark_cinematic", "cinematic"),
            "cinematic": ("dark_cinematic", "cinematic"),
            "mystical": ("mystical", "mystical"),
            "happy": ("happy", "happy"),
        }
        for key, (m, s) in mood_mappings.items():
            if key in filename:
                detected_mood = m
                detected_style = s
                break
                
        console.print(f"[bold green]✓ Auto-Detected metadata from filename:[/] Anime: [bold]{detected_anime}[/], Mood: [bold]{detected_mood}[/]")
        
        # Find matching plan
        target_plan = None
        for plan in MOOD_PLANS:
            if plan["anime"] == detected_anime and plan["mood"] == detected_mood:
                target_plan = plan
                break
                
        if not target_plan:
            console.print("[yellow]  No pre-configured plan found in MOOD_PLANS. Creating a dynamic cinematic plan...[/]")
            target_plan = {
                "mood": detected_mood,
                "style": detected_style,
                "anime": detected_anime,
                "aspect_ratio": "9:16" if detected_mood != "romantic" else "1:1",
                "title": f"{detected_anime.replace('_', ' ').title()} Climax",
                "quote": f"A testament to determination and destiny ✨",
                "purpose": f"Epic cinematic edit of {detected_anime.replace('_', ' ').title()}",
                "music_name": f"{detected_anime.replace('_', ' ').title()} Instrumental OST",
                "narrative": [
                    {"text": "In a world of light and shadow...", "duration": 4.5},
                    {"text": "They had to fight for what they loved.", "duration": 5.0},
                    {"text": "No matter the cost.", "duration": 5.0},
                    {"text": "UNLEASH THE POWER 🔥", "duration": 5.5},
                    {"text": "Where legends begin and end. ⚔️", "duration": 5.0}
                ]
            }
            
        if args.dry_run:
            console.print("[yellow]DRY RUN — plan created for custom clip processing:[/]")
            console.print(target_plan)
            return
            
        # Ensure mood folders exist
        from generator.mood_organizer import MoodOrganizer
        organizer = MoodOrganizer()
        
        # Generate the reel
        generate_reel(target_plan, input_clip_override=str(clip_path))
        organizer.print_archive_summary()
        return

    # Show plan
    print_plan()

    if args.dry_run:
        console.print("[yellow]DRY RUN — no reels generated[/]")
        return

    # Filter by mood if requested
    plans = MOOD_PLANS
    if args.mood:
        plans = [p for p in MOOD_PLANS if p["mood"] == args.mood or p["style"] == args.mood]
        if not plans:
            console.print(f"[red]No plan found for mood: {args.mood}[/]")
            console.print(f"[dim]Available moods: {', '.join(p['mood'] for p in MOOD_PLANS)}[/]")
            return

    # Ensure mood folders exist
    from generator.mood_organizer import MoodOrganizer
    organizer = MoodOrganizer()

    # Generate each reel sequentially
    results = []
    failed = []

    for i, plan in enumerate(plans, 1):
        console.print(f"\n{'─'*70}")
        console.print(f"[bold]Reel {i}/{len(plans)}:[/] [{plan['mood'].upper()}] {plan['title']}")
        result = generate_reel(plan)
        if result:
            results.append(result)
        else:
            failed.append(plan["title"])

    # Final summary
    console.print(f"\n{'═'*70}")
    console.print(Panel(
        f"[bold green]✓ {len(results)} reels generated successfully[/]\n"
        + (f"[red]✗ {len(failed)} failed: {', '.join(failed)}[/]" if failed else "")
        + f"\n\n[cyan]Content organized by mood in:[/]\n"
        + f"[dim]{organizer.archive_root}[/]",
        title="GENERATION COMPLETE",
        border_style="green"
    ))

    # Print archive summary
    organizer.print_archive_summary()

    # Print upload command
    console.print("\n[bold]To upload to Instagram:[/]")
    console.print("[dim]  py upload_to_instagram.py --mood romantic[/]")
    console.print("[dim]  py upload_to_instagram.py --all[/]")


if __name__ == "__main__":
    main()

