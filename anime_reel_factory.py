"""
REEL GOD - Autonomous 30-Reel Anime Content Factory
====================================================
I (REEL GOD) decide everything:
  - Which anime to use
  - What style/mood
  - Which music (Bollywood / Hollywood / Instrumental)
  - What caption & hashtags
  - When to post (content calendar)

Run this once → it generates 30 reels autonomously.
"""
import os, sys, json, random
from pathlib import Path

# Fix Windows console encoding issue
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# ── Pillow 10+ compatibility monkeypatch for MoviePy 1.x ──
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from datetime import datetime, timedelta
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv()

# ── Auto-detect and register FFmpeg (from imageio-ffmpeg if system ffmpeg missing) ──
def _setup_ffmpeg():
    """Find ffmpeg binary and add to PATH / MoviePy config."""
    import shutil
    # Check system ffmpeg first
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    # Try imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and Path(ffmpeg_path).exists():
            # yt-dlp requires the binary to be named exactly 'ffmpeg.exe'
            local_bin_dir = ROOT / "data" / "bin"
            local_bin_dir.mkdir(parents=True, exist_ok=True)
            local_ffmpeg = local_bin_dir / "ffmpeg.exe"
            
            if not local_ffmpeg.exists():
                try:
                    shutil.copy2(ffmpeg_path, local_ffmpeg)
                except Exception as e:
                    print(f"[FFmpeg] Symlink/copy failed: {e}")
            
            if local_ffmpeg.exists():
                # Add its directory to PATH for yt-dlp and subprocesses
                ffmpeg_dir = str(local_bin_dir)
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
                # Set for MoviePy
                os.environ["FFMPEG_BINARY"] = str(local_ffmpeg)
                try:
                    import moviepy.config as mpy_cfg
                    mpy_cfg.FFMPEG_BINARY = str(local_ffmpeg)
                except Exception:
                    pass
                print(f"[FFmpeg] Aliased imageio-ffmpeg as: {local_ffmpeg}")
                return str(local_ffmpeg)
    except Exception as e:
        print(f"[FFmpeg] imageio-ffmpeg not available: {e}")
    print("[FFmpeg] WARNING: ffmpeg not found. Video encoding may fail.")
    return None

_FFMPEG_PATH = _setup_ffmpeg()

console = Console()


# ── My content calendar decision (30 reels × 10 days) ────────────────────────

THIRTY_REEL_PLAN = [
    # Day 1
    {"day":1, "slot":"morning", "anime":"demon_slayer",        "style":"epic_action",    "music":"hollywood", "title":"The Flame Never Dies",        "quote":"Set your heart ablaze 🔥", "aspect_ratio": "9:16"},
    {"day":1, "slot":"evening", "anime":"your_lie_in_april",   "style":"emotional",      "music":"bollywood", "title":"Love Between Every Note",      "quote":"Your melody lives in my heart 🎵", "aspect_ratio": "1:1"},
    {"day":1, "slot":"night",   "anime":"attack_on_titan",     "style":"dark_cinematic", "music":"hollywood", "title":"Beyond the Walls",             "quote":"We fight so others can live 🗡️", "aspect_ratio": "9:16"},
    # Day 2
    {"day":2, "slot":"morning", "anime":"naruto",              "style":"motivational",   "music":"bollywood", "title":"Believe It",                   "quote":"I never give up. That's my ninja way 🌀"},
    {"day":2, "slot":"evening", "anime":"violet_evergarden",   "style":"romance",        "music":"bollywood", "title":"Words From the Heart",         "quote":"I love you. Do you understand that? 💌"},
    {"day":2, "slot":"night",   "anime":"jujutsu_kaisen",      "style":"dark_cinematic", "music":"instrumental","title":"Cursed and Beautiful",       "quote":"The strong devour the weak 👁️"},
    # Day 3
    {"day":3, "slot":"morning", "anime":"one_piece",           "style":"motivational",   "music":"bollywood", "title":"King of the Pirates",          "quote":"I'm going to be King of the Pirates! 🏴‍☠️"},
    {"day":3, "slot":"evening", "anime":"re_zero",             "style":"emotional",      "music":"bollywood", "title":"Starting Life Over Again",     "quote":"Even reset, my love never fades 💙"},
    {"day":3, "slot":"night",   "anime":"demon_slayer",        "style":"mystical",       "music":"instrumental","title":"Breathing Forms",            "quote":"Turn your sorrow into strength ⚡"},
    # Day 4
    {"day":4, "slot":"morning", "anime":"fullmetal_alchemist", "style":"epic_action",    "music":"hollywood", "title":"Equivalent Exchange",         "quote":"To obtain, something of equal value must be lost ⚖️"},
    {"day":4, "slot":"evening", "anime":"sword_art_online",    "style":"romance",        "music":"bollywood", "title":"Together in Any World",        "quote":"I'll always find you 💫"},
    {"day":4, "slot":"night",   "anime":"attack_on_titan",     "style":"dark_cinematic", "music":"hollywood", "title":"Rumbling",                     "quote":"The world is cruel and beautiful 🌍"},
    # Day 5
    {"day":5, "slot":"morning", "anime":"jujutsu_kaisen",      "style":"epic_action",    "music":"hollywood", "title":"Domain Expansion",             "quote":"Malleable Reality 🌀"},
    {"day":5, "slot":"evening", "anime":"your_lie_in_april",   "style":"emotional",      "music":"bollywood", "title":"Lie We Tell Ourselves",        "quote":"You are my spring 🌸"},
    {"day":5, "slot":"night",   "anime":"re_zero",             "style":"dark_cinematic", "music":"instrumental","title":"Return by Death",            "quote":"Even in despair, I stand 💀"},
    # Day 6
    {"day":6, "slot":"morning", "anime":"naruto",              "style":"motivational",   "music":"bollywood", "title":"Pain's Path",                  "quote":"If you don't share pain, you can't understand others 🔥"},
    {"day":6, "slot":"evening", "anime":"violet_evergarden",   "style":"romance",        "music":"bollywood", "title":"A Letter Never Sent",          "quote":"I have finally understood what 'I love you' means 💜"},
    {"day":6, "slot":"night",   "anime":"demon_slayer",        "style":"epic_action",    "music":"hollywood", "title":"Thunder Breathing",            "quote":"Rumble and Flash ⚡"},
    # Day 7
    {"day":7, "slot":"morning", "anime":"one_piece",           "style":"epic_action",    "music":"hollywood", "title":"Gear Fifth",                   "quote":"Awakening of a Warrior God 🥁"},
    {"day":7, "slot":"evening", "anime":"fullmetal_alchemist", "style":"emotional",      "music":"bollywood", "title":"Promise Brothers",             "quote":"Brother, I'll bring you back 🤝"},
    {"day":7, "slot":"night",   "anime":"attack_on_titan",     "style":"dark_cinematic", "music":"instrumental","title":"Last of the Survey Corps",   "quote":"If you win, you live 🗡️"},
    # Day 8
    {"day":8, "slot":"morning", "anime":"jujutsu_kaisen",      "style":"mystical",       "music":"instrumental","title":"Six Eyes Open",              "quote":"Throughout Heaven and Earth, I alone am the honored one ∞"},
    {"day":8, "slot":"evening", "anime":"your_lie_in_april",   "style":"romance",        "music":"bollywood", "title":"April Love Song",              "quote":"You were my color in a grey world 🎶"},
    {"day":8, "slot":"night",   "anime":"naruto",              "style":"dark_cinematic", "music":"hollywood", "title":"Akatsuki Rising",              "quote":"Even if I must take the world's hate 🌑"},
    # Day 9
    {"day":9, "slot":"morning", "anime":"demon_slayer",        "style":"epic_action",    "music":"bollywood", "title":"Water Breathing First Form",   "quote":"Surface Slash 💧"},
    {"day":9, "slot":"evening", "anime":"re_zero",             "style":"emotional",      "music":"bollywood", "title":"Rem's Confession",             "quote":"I love you, Subaru 💙"},
    {"day":9, "slot":"night",   "anime":"attack_on_titan",     "style":"mystical",       "music":"instrumental","title":"Colossal Titan Falls",       "quote":"The battle for freedom begins 🌊"},
    # Day 10
    {"day":10,"slot":"morning", "anime":"fullmetal_alchemist", "style":"motivational",   "music":"hollywood", "title":"Beyond the Gate",             "quote":"Stand up and walk. Keep moving forward ⚔️"},
    {"day":10,"slot":"evening", "anime":"violet_evergarden",   "style":"emotional",      "music":"bollywood", "title":"The Last Letter",             "quote":"Thank you for giving me life to love 💛"},
    {"day":10,"slot":"night",   "anime":"one_piece",           "style":"dark_cinematic", "music":"hollywood", "title":"The Final War",               "quote":"The age of pirates will never end 🌊"},
]

# Hashtag packs
HASHTAGS = {
    "demon_slayer":        "#demonslayer #鬼滅の刃 #tanjiro #nezuko #kimetsonoyaiba #animeedit #animetiktok",
    "attack_on_titan":     "#attackontitan #aot #shingekinokyojin #eren #levi #animeedit #anime2024",
    "jujutsu_kaisen":      "#jujutsukaisen #jjk #gojo #yuji #sukuna #animeedit #anime",
    "your_lie_in_april":   "#yourlieinapril #shigatsu #kaori #kousei #animeedit #animelove #sadanime",
    "one_piece":           "#onepiece #luffy #gear5 #zoro #nakama #animeedit #shounen",
    "naruto":              "#naruto #narutoshippuden #boruto #uzumaki #animeedit #anime #ninja",
    "violet_evergarden":   "#violetevergarden #violet #auto_memory_doll #animeedit #animecry #kyoani",
    "sword_art_online":    "#sao #swordartonline #kirito #asuna #animeedit #animeromance",
    "re_zero":             "#rezero #subaru #rem #emilia #animeedit #animedark #isekai",
    "fullmetal_alchemist": "#fmab #fullmetalalchemist #edward #alphonse #equivalent #animeedit",
}

COMMON_TAGS = "#anime #animereels #animemoments #animelovers #animefan #reelsgod #otaku"

POSTING_TIMES = {
    "morning": "09:00",
    "evening": "18:00",
    "night":   "21:00",
}

# Rich narrative fallbacks organized by style — full emotional range
NARRATIVE_TEMPLATES = {
    "epic_action": [
        {"text": "They told him to kneel...",                    "duration": 4.5},
        {"text": "He rose from the ashes, unstoppable.",          "duration": 5.0},
        {"text": "Every blow made him stronger.",                 "duration": 5.0},
        {"text": "THIS IS WHERE LEGENDS ARE BORN.",               "duration": 5.5},
        {"text": "The battle is just beginning.",                 "duration": 5.0},
    ],
    "emotional": [
        {"text": "She was always smiling.",                       "duration": 4.5},
        {"text": "But no one knew the pain she carried.",         "duration": 5.0},
        {"text": "Until the day she couldn't hide it anymore.",   "duration": 5.0},
        {"text": "Some goodbyes are never spoken.",               "duration": 5.5},
        {"text": "But they echo forever in the heart. 💙",        "duration": 5.0},
    ],
    "romance": [
        {"text": "He never believed in love.",                    "duration": 4.5},
        {"text": "Until she walked into his world.",              "duration": 5.0},
        {"text": "She saw the broken pieces of him...",           "duration": 5.0},
        {"text": "AND LOVED EVERY SINGLE ONE. 💕",               "duration": 5.5},
        {"text": "Some love stories last beyond forever.",        "duration": 5.0},
    ],
    "motivational": [
        {"text": "Everyone said he'd fail.",                      "duration": 4.5},
        {"text": "He trained while they slept.",                  "duration": 5.0},
        {"text": "He bled while they laughed.",                   "duration": 5.0},
        {"text": "NOW WATCH HIM RISE. 🔥",                        "duration": 5.5},
        {"text": "Hard work always beats talent in the end.",    "duration": 5.0},
    ],
    "dark_cinematic": [
        {"text": "The world carries no mercy.",                   "duration": 4.5},
        {"text": "And yet, he stood at the edge of the abyss.",  "duration": 5.0},
        {"text": "To protect the ones he lost.",                  "duration": 5.0},
        {"text": "EVEN IF IT MEANS BECOMING THE MONSTER.",       "duration": 5.5},
        {"text": "Some sacrifices are never forgotten. 🗡️",      "duration": 5.0},
    ],
    "mystical": [
        {"text": "Beyond the world you know...",                  "duration": 4.5},
        {"text": "Lies a power older than time itself.",          "duration": 5.0},
        {"text": "She carried it alone, in silence.",             "duration": 5.0},
        {"text": "UNTIL THE ANCIENT FLAME IGNITED. ✨",           "duration": 5.5},
        {"text": "Some destinies are written in starlight.",      "duration": 5.0},
    ],
    "sacrifice": [
        {"text": "He gave everything for his friends.",           "duration": 4.5},
        {"text": "Even when his body could no longer fight.",     "duration": 5.0},
        {"text": "He smiled through the pain.",                   "duration": 5.0},
        {"text": "BECAUSE THEIR SURVIVAL WAS WORTH IT ALL.",     "duration": 5.5},
        {"text": "A hero dies, but the legend lives forever. 💛", "duration": 5.0},
    ],
    "happy": [
        {"text": "Life isn't always serious.",                    "duration": 4.5},
        {"text": "Sometimes joy is the greatest rebellion.",      "duration": 5.0},
        {"text": "Laughing together, they forgot the world.",     "duration": 5.0},
        {"text": "HAPPINESS IS A SUPERPOWER. 🌟",                 "duration": 5.5},
        {"text": "Choose joy. Always. 🌸",                        "duration": 5.0},
    ],
}


def get_gemini_captions(plan_item: dict) -> dict:
    """Use Gemini to generate a rich caption and timed narrative subtitles."""
    try:
        from google import genai as gai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return {}
        client = gai.Client(api_key=api_key)
        prompt = f"""You are REEL GOD, the world's best anime Instagram editor.

Generate structured content for a viral anime Instagram Reel:
- Anime: {plan_item['anime'].replace('_',' ').title()}
- Style: {plan_item['style']}
- Title: {plan_item['title']}
- Base Quote: {plan_item['quote']}

Create a 5-step narrative subtitle script that builds deep tension and delivers a high-impact climax.
The total duration of all 5 steps combined MUST be exactly 25.0 seconds. Keep each subtitle short (max 7 words).

Return ONLY valid JSON:
{{
  "caption": "Viral Instagram caption with emojis and hashtags",
  "story_text": "Story text hook",
  "narrative": [
    {{"text": "Short emotional hook...", "duration": 4.5}},
    {{"text": "Rising tension line...", "duration": 5.0}},
    {{"text": "The turning point...", "duration": 5.0}},
    {{"text": "CLIMAX LINE IN ALL CAPS...", "duration": 5.5}},
    {{"text": "Final resolution punchline...", "duration": 5.0}}
  ]
}}"""
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        import json, re
        txt = re.sub(r'^```[a-z]*\n?', '', resp.text.strip())
        txt = re.sub(r'```$', '', txt).strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        console.print(f"[dim]Caption gen fallback: {e}[/]")
    return {}


def run_anime_reel_factory(
    max_reels: int = 30,
    start_day: int = 1,
    test_mode: bool = False,
):
    """
    Main entry point. Generates up to max_reels anime reels autonomously.
    Set test_mode=True to do a dry-run without downloading.
    """
    from generator.anime_fetcher import AnimeFetcher
    from generator.reel_composer import ReelComposer
    from music.music_fetcher import MusicFetcher

    fetcher  = AnimeFetcher()
    composer = ReelComposer()
    music_fx = MusicFetcher()

    plan = [p for p in THIRTY_REEL_PLAN if p["day"] >= start_day][:max_reels]

    console.print(Panel(
        f"[bold magenta]REEL GOD ANIME FACTORY[/]\n"
        f"[dim]Generating {len(plan)} reels | {plan[0]['day']} to Day {plan[-1]['day']}[/]",
        border_style="magenta"
    ))

    # Print the plan
    t = Table(title="Content Calendar", border_style="cyan")
    t.add_column("#", style="dim")
    t.add_column("Day/Slot")
    t.add_column("Anime")
    t.add_column("Style")
    t.add_column("Music")
    t.add_column("Title")
    for i, p in enumerate(plan, 1):
        t.add_row(str(i), f"D{p['day']} {p['slot']}", p["anime"].replace("_"," "),
                  p["style"], p["music"], p["title"])
    console.print(t)

    if test_mode:
        console.print("[yellow]TEST MODE: Calendar shown above. No downloads.[/]")
        return []

    results = []
    failed  = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(), console=console
    ) as progress:
        task = progress.add_task("Generating reels...", total=len(plan))

        for i, reel in enumerate(plan, 1):
            progress.update(task, description=f"[{i}/{len(plan)}] {reel['anime']} {reel['style']}")
            console.print(f"\n{'-'*60}")
            console.print(f"[bold]Reel {i}/{len(plan)}:[/] Day {reel['day']} {reel['slot']} — [cyan]{reel['title']}[/]")

            # 1. Fetch anime clip using the SPECIFIC anime from the plan
            try:
                anime_key = reel.get("anime", "")
                if anime_key:
                    video_path = fetcher.fetch_for_anime_and_style(anime_key, reel["style"])
                else:
                    video_path = fetcher.fetch_clip_for_style(reel["style"])
                if not video_path:
                    console.print(f"[red]✗ Video fetch failed, skipping[/]")
                    failed.append(reel)
                    progress.advance(task)
                    continue
            except Exception as e:
                console.print(f"[red]✗ Video fetch error: {e}, skipping[/]")
                failed.append(reel)
                progress.advance(task)
                continue

            # 2. Find best segment
            try:
                start_t, end_t = fetcher.get_best_segment(video_path, target_dur=25.0)
            except Exception as e:
                console.print(f"[yellow]Segment detection failed, using default: {e}[/]")
                start_t, end_t = 0.0, 25.0

            # 3. Fetch music matched to BOTH style AND specific anime
            try:
                music_path = music_fx.fetch_for_style(reel["style"], anime=reel.get("anime"))
                if not music_path:
                    console.print("[yellow]Music fetch failed, continuing without music[/]")
                    music_path = None
            except Exception as e:
                console.print(f"[yellow]Music fetch error: {e}, continuing without music[/]")
                music_path = None

            # 4. Gemini caption
            try:
                extras = get_gemini_captions(reel)
                caption = extras.get("caption") or (
                    f"{reel['quote']} | {reel['title']}\n\n"
                    + HASHTAGS.get(reel["anime"], "") + " " + COMMON_TAGS
                )
            except Exception as e:
                console.print(f"[yellow]Caption generation failed, using fallback: {e}[/]")
                caption = f"{reel['quote']} | {reel['title']}\n\n" + COMMON_TAGS
                extras = {}

            # 5. Compose reel — use style-specific narrative fallback if Gemini didn't give us one
            try:
                if extras.get("narrative"):
                    narrative = extras["narrative"]
                else:
                    # Rich style-specific narrative templates — no more generic action text
                    base_template = NARRATIVE_TEMPLATES.get(reel["style"], NARRATIVE_TEMPLATES["epic_action"])
                    import copy
                    narrative = copy.deepcopy(base_template)
                    # Inject the reel's quote into the climax line (index 3)
                    if reel.get("quote"):
                        climax_text = reel["quote"].upper() if not reel["quote"].isupper() else reel["quote"]
                        narrative[3]["text"] = climax_text
                
                reel_meta = {
                    **reel,
                    "start": start_t,
                    "end":   end_t,
                    "caption": caption,
                    "narrative": narrative,
                }
                output_name = f"D{reel['day']}_{reel['slot']}_{reel['anime']}_{reel['style']}.mp4"
                result_path = composer.compose_reel(video_path, music_path, reel_meta, output_name)

                if result_path:
                    # Save metadata sidecar JSON
                    meta_path = result_path.with_suffix(".json")
                    meta_path.write_text(json.dumps({
                        **reel,
                        "caption": caption,
                        "post_time": POSTING_TIMES[reel["slot"]],
                        "file": str(result_path),
                        "narrative": narrative,
                        "generated_at": datetime.now().isoformat(),
                    }, indent=2, ensure_ascii=False))
                    results.append(result_path)
                    console.print(f"[bold green]✓ Saved:[/] {result_path.name}")
                else:
                    failed.append(reel)
                    console.print(f"[red]✗ Compose failed[/]")
            except Exception as e:
                console.print(f"[red]✗ Composition error: {e}[/]")
                failed.append(reel)

            progress.advance(task)

    # Final summary
    console.print(Panel(
        f"[bold green]FACTORY COMPLETE![/]\n\n"
        f"✅ Generated: {len(results)} reels\n"
        f"❌ Failed:    {len(failed)} reels\n\n"
        f"📁 Output: {composer.output_dir}\n\n"
        + "\n".join(f"  • {r.name}" for r in results[:10])
        + (f"\n  ... and {len(results)-10} more" if len(results) > 10 else ""),
        title="30-Reel Factory Results",
        border_style="green"
    ))

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="REEL GOD Anime Factory")
    parser.add_argument("--count", type=int, default=30, help="Number of reels to generate")
    parser.add_argument("--start-day", type=int, default=1, help="Start from day N")
    parser.add_argument("--test", action="store_true", help="Dry run - show plan only")
    parser.add_argument("--single", type=int, default=None, help="Generate only reel #N")
    args = parser.parse_args()

    if args.single is not None:
        run_anime_reel_factory(max_reels=1, start_day=args.single, test_mode=False)
    else:
        run_anime_reel_factory(max_reels=args.count, start_day=args.start_day, test_mode=args.test)
