"""
REEL GOD - Anime Clip Fetcher
Downloads real anime video clips from YouTube using yt-dlp.
Uses pre-merged single-stream format (no ffmpeg merge required).
Selects the best high-energy 15-30 second window automatically.
"""
import os, sys, re, random, math
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
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

console = Console()

# Style-specific search queries per anime — covers action, emotional, romantic, sad, motivational moods
ANIME_SEARCHES = {
    "demon_slayer": {
        "epic_action":    ["Demon Slayer Tanjiro Hinokami Kagura breathtaking fight", "Demon Slayer Zenitsu lightning fast attack", "Demon Slayer Rengoku flame pillars battle"],
        "emotional":      ["Demon Slayer Rengoku death emotional scene", "Demon Slayer Mugen Train Tanjiro crying", "Demon Slayer sad farewell scene"],
        "motivational":   ["Demon Slayer Tanjiro never give up scene", "Demon Slayer training motivation", "Demon Slayer determination scene"],
        "mystical":       ["Demon Slayer breathing technique mystical", "Demon Slayer Nezuko demon transformation", "Demon Slayer beautiful scenery"],
        "dark_cinematic": ["Demon Slayer dark night battle scene", "Demon Slayer Muzan scene cinematic"],
        "romance":        ["Demon Slayer Tanjiro Nezuko bond heartwarming", "Demon Slayer emotional sibling scene"],
    },
    "attack_on_titan": {
        "epic_action":    ["Attack on Titan Levi Ackerman fight compilation", "AOT Eren Founding Titan battle", "Attack on Titan Survey Corps charge scene"],
        "emotional":      ["Attack on Titan Eren and Armin childhood emotional", "AOT Erwin death scene heartbreaking", "Attack on Titan Levi crying"],
        "motivational":   ["Attack on Titan Erwin speech charge", "AOT Survey Corps sacrifice motivational", "Attack on Titan fight for freedom"],
        "dark_cinematic": ["Attack on Titan Rumbling cinematic", "AOT dark atmospheric scene night", "Attack on Titan titan horror scene"],
        "mystical":       ["Attack on Titan Wall Titans reveal", "AOT Paths dimension mystical"],
        "romance":        ["Attack on Titan Eren Historia heartfelt", "AOT Historia Ymir touching moment"],
    },
    "jujutsu_kaisen": {
        "epic_action":    ["Jujutsu Kaisen Gojo Satoru Domain Expansion", "JJK Yuji Itadori Black Flash", "Jujutsu Kaisen Sukuna cursed flame"],
        "emotional":      ["Jujutsu Kaisen Yuji death emotional scene", "JJK Nobara heartbreaking", "Jujutsu Kaisen sacrifice scene sad"],
        "motivational":   ["Jujutsu Kaisen Yuji never gives up", "JJK Nanami motivational speech"],
        "dark_cinematic": ["Jujutsu Kaisen dark cinematic night fight", "JJK Gojo blindfold reveal"],
        "mystical":       ["Jujutsu Kaisen Six Eyes mystical power", "JJK special grade cursed spirit"],
        "romance":        ["Jujutsu Kaisen Yuji Nobara friendship heartfelt"],
    },
    "your_lie_in_april": {
        "epic_action":    ["Your Lie in April Kousei piano performance intense"],
        "emotional":      ["Your Lie in April Kaori last performance crying", "Your Lie in April final letter heartbreaking", "Shigatsu wa Kimi no Uso saddest scenes"],
        "motivational":   ["Your Lie in April Kousei returns to piano motivational", "Your Lie in April overcoming fear"],
        "dark_cinematic": ["Your Lie in April dark moment isolation"],
        "mystical":       ["Your Lie in April beautiful music bloom"],
        "romance":        ["Your Lie in April Kaori Kousei romantic moment", "Shigatsu wa Kimi no Uso love scene beautiful", "Your Lie in April cherry blossom scene"],
    },
    "one_piece": {
        "epic_action":    ["One Piece Luffy Gear 5 Sun God awakening", "One Piece Zoro epic fight", "One Piece Luffy vs Kaido battle"],
        "emotional":      ["One Piece Robin I want to live scene", "One Piece Going Merry farewell emotional", "One Piece Ace death heartbreaking"],
        "motivational":   ["One Piece Luffy inspiring speech", "One Piece friendship nakama power", "One Piece never give up"],
        "dark_cinematic": ["One Piece dark sea cinematic", "One Piece Marineford war cinematic"],
        "mystical":       ["One Piece Devil Fruit powers mystical", "One Piece Sky Island beautiful"],
        "romance":        ["One Piece Luffy Nami heartfelt scene", "One Piece emotional farewell"],
    },
    "naruto": {
        "epic_action":    ["Naruto vs Pain fight Konoha battle", "Naruto Sage Mode Six Path fight", "Rock Lee removes weights Gaara"],
        "emotional":      ["Naruto Jiraiya death emotional scene", "Naruto Minato farewell son", "Naruto Kushina I love you scene"],
        "motivational":   ["Naruto ninja way speech motivational", "Naruto believe it never give up", "Rock Lee hard work motivational speech"],
        "dark_cinematic": ["Naruto Akatsuki dark cinematic night", "Naruto Pain destruction of Konoha"],
        "mystical":       ["Naruto Nine Tails chakra mystical power", "Naruto Sage Art beautiful"],
        "romance":        ["Naruto Hinata confesses love", "Naruto Hinata love scene", "Naruto and Hinata relationship"],
    },
    "violet_evergarden": {
        "epic_action":    ["Violet Evergarden fight scene auto memories doll"],
        "emotional":      ["Violet Evergarden crying scene heartbreaking", "Violet Evergarden mother letter scene", "Violet Evergarden most emotional moments"],
        "motivational":   ["Violet Evergarden learning love motivational", "Violet Evergarden I understand now"],
        "dark_cinematic": ["Violet Evergarden war memory dark"],
        "mystical":       ["Violet Evergarden beautiful scenery peaceful"],
        "romance":        ["Violet Evergarden Gilbert love scene", "Violet Evergarden I love you scene beautiful", "Violet Evergarden romantic moment"],
    },
    "sword_art_online": {
        "epic_action":    ["SAO Kirito Dual Wielding fight", "Sword Art Online boss fight epic"],
        "emotional":      ["SAO Kirito Asuna death scene emotional", "Sword Art Online heartbreaking moment"],
        "motivational":   ["SAO Kirito never give up fight"],
        "dark_cinematic": ["SAO dark dungeon boss cinematic"],
        "mystical":       ["SAO virtual world beautiful scenery"],
        "romance":        ["SAO Kirito Asuna romantic scene", "Sword Art Online Kirito Asuna love", "SAO couple scene beautiful"],
    },
    "re_zero": {
        "epic_action":    ["Re Zero Subaru fight scene", "Re Zero battle epic"],
        "emotional":      ["Re Zero Rem I love you confession", "Re Zero Subaru crying breakdown", "Re Zero heartbreaking death scene"],
        "motivational":   ["Re Zero Subaru never give up", "Re Zero starting over determination"],
        "dark_cinematic": ["Re Zero dark night scene tragic", "Re Zero despair dark"],
        "mystical":       ["Re Zero Emilia spirit sanctuary beautiful"],
        "romance":        ["Re Zero Rem confession love scene", "Re Zero Emilia Subaru romantic moment"],
    },
    "fullmetal_alchemist": {
        "epic_action":    ["FMA Brotherhood Edward Elric alchemy fight", "FMA Roy Mustang flame alchemy battle"],
        "emotional":      ["FMA Brotherhood Nina Tucker death scene", "FMA Edward Alphonse sacrifice emotional", "Fullmetal Alchemist heartbreaking moment"],
        "motivational":   ["FMA Edward Elric equivalent exchange speech", "FMA Brotherhood rise again"],
        "dark_cinematic": ["FMA Brotherhood Envy Father dark scene"],
        "mystical":       ["FMA Brotherhood Gate of Truth transmutation"],
        "romance":        ["FMA Brotherhood Ed Winry confession", "Fullmetal Alchemist Edward Winry romance"],
    },
}

STYLE_TO_ANIME = {
    "epic_action":    ["demon_slayer", "jujutsu_kaisen", "attack_on_titan", "naruto", "fullmetal_alchemist"],
    "emotional":      ["your_lie_in_april", "violet_evergarden", "re_zero", "naruto", "attack_on_titan"],
    "dark_cinematic": ["attack_on_titan", "re_zero", "demon_slayer", "fullmetal_alchemist"],
    "mystical":       ["demon_slayer", "jujutsu_kaisen", "re_zero", "naruto"],
    "motivational":   ["naruto", "one_piece", "demon_slayer", "fullmetal_alchemist"],
    "romance":        ["your_lie_in_april", "violet_evergarden", "sword_art_online", "re_zero"],
    "sacrifice":      ["attack_on_titan", "naruto", "fullmetal_alchemist", "re_zero"],
    "happy":          ["one_piece", "naruto", "demon_slayer", "sword_art_online"],
}


class AnimeFetcher:
    """Downloads anime clips from YouTube via yt-dlp."""

    def __init__(self):
        self.clip_dir = config.DATA_DIR / "anime_clips"
        self.clip_dir.mkdir(parents=True, exist_ok=True)

    def fetch_clip_for_style(self, style: str, max_duration: int = 180) -> Optional[Path]:
        """Fetch anime clip matching the given style/mood. Picks randomly from pool."""
        anime_options = STYLE_TO_ANIME.get(style, ["demon_slayer"])
        anime_key = random.choice(anime_options)
        return self.fetch_for_anime_and_style(anime_key, style, max_duration)

    def fetch_for_anime_and_style(self, anime_key: str, style: str, max_duration: int = 180) -> Optional[Path]:
        """Fetch a clip for a SPECIFIC anime + style combination (e.g. your_lie_in_april + romance)."""
        # Resolve unknown anime to closest match
        if anime_key not in ANIME_SEARCHES:
            fallback_pool = STYLE_TO_ANIME.get(style, ["demon_slayer"])
            anime_key = random.choice(fallback_pool)
            console.print(f"[yellow]Unknown anime key, falling back to {anime_key}[/]")

        style_queries = ANIME_SEARCHES[anime_key]
        # If style-specific queries exist (new dict format), use them; otherwise use all
        if isinstance(style_queries, dict):
            # Try exact style, then fallbacks in order of emotional similarity
            STYLE_FALLBACK_ORDER = {
                "epic_action":    ["epic_action", "motivational", "dark_cinematic"],
                "emotional":      ["emotional", "romance", "motivational"],
                "romance":        ["romance", "emotional", "motivational"],
                "dark_cinematic": ["dark_cinematic", "emotional", "epic_action"],
                "motivational":   ["motivational", "epic_action", "emotional"],
                "mystical":       ["mystical", "dark_cinematic", "emotional"],
                "sacrifice":      ["emotional", "dark_cinematic", "motivational"],
                "happy":          ["motivational", "romance", "emotional"],
            }
            order = STYLE_FALLBACK_ORDER.get(style, [style, "emotional", "epic_action"])
            queries = []
            for s in order:
                if s in style_queries:
                    queries = style_queries[s]
                    break
            if not queries:
                queries = next(iter(style_queries.values()))
        else:
            queries = style_queries

        query = random.choice(queries)
        console.print(f"[bold cyan]Anime fetch:[/] [{anime_key}] style={style} → {query}")
        return self._download_best_clip(query, anime_key, style, max_duration)

    def fetch_specific(self, anime_key: str, style: str = "epic_action") -> Optional[Path]:
        """Fetch from a specific anime."""
        queries = ANIME_SEARCHES.get(anime_key, ANIME_SEARCHES["demon_slayer"])
        query = random.choice(queries)
        console.print(f"[bold cyan]Fetching {anime_key}:[/] {query}")
        return self._download_best_clip(query, anime_key, style, 180)

    def _download_best_clip(self, query: str, anime_key: str, style: str, max_dur: int) -> Optional[Path]:
        """Download best quality clip from YouTube using yt-dlp with comprehensive fallbacks."""
        try:
            import yt_dlp
        except ImportError:
            console.print("[red]yt-dlp not installed![/]")
            return self._use_any_cached_clip(anime_key, style)

        # Check cache first
        cached = list(self.clip_dir.glob(f"{anime_key}_{style}_*.mp4"))
        if cached:
            c = random.choice(cached)
            if c.stat().st_size > 500_000:
                console.print(f"[green]Using cached clip:[/] {c.name}")
                return c

        # Fallback: use any cached clip for this anime
        any_cached = list(self.clip_dir.glob(f"{anime_key}_*.mp4"))
        if any_cached:
            c = random.choice(any_cached)
            if c.stat().st_size > 500_000:
                console.print(f"[yellow]Using fallback cached clip:[/] {c.name}")
                return c

        out_tmpl = str(self.clip_dir / f"{anime_key}_{style}_%(id)s.%(ext)s")

        # Detect ffmpeg for high-quality merging
        import shutil
        ffmpeg_loc = shutil.which("ffmpeg")
        
        if not ffmpeg_loc:
            try:
                import imageio_ffmpeg
                ffmpeg_loc = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass

        # Progressive format fallback
        formats = [
            "best[ext=mp4][height<=1080]/best[height<=720]/worst[ext=mp4]",
            "best[ext=mp4]/best",
            "worst"
        ]

        for fmt in formats:
            ydl_opts = {
                "format": fmt,
                "outtmpl": out_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "socket_timeout": 30,
                "nocheckcertificate": True,
                "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {max_dur}"),
                "concurrent_fragment_download": True,
                "buffersize": 1024 * 16,
            }
            
            # Remove download_ranges for fallback formats (may not be supported)
            if "worst" not in fmt:
                ydl_opts["download_ranges"] = lambda info, ydl: [{'start_time': 0, 'end_time': 90}]
                ydl_opts["force_keyframes_at_cuts"] = True
            
            if ffmpeg_loc:
                ffmpeg_path_obj = Path(ffmpeg_loc)
                if ffmpeg_path_obj.name.lower() not in ["ffmpeg.exe", "ffmpeg"]:
                    local_ffmpeg = config.DATA_DIR / "bin" / "ffmpeg.exe"
                    if local_ffmpeg.exists():
                        ffmpeg_path_obj = local_ffmpeg
                ydl_opts["ffmpeg_location"] = str(ffmpeg_path_obj.parent)

            try:
                console.print(f"[yellow]Attempting download with format: {fmt[:30]}...[/]")
                is_url = query.startswith("http://") or query.startswith("https://")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    dl_target = query if is_url else f"ytsearch5:{query}"
                    info = ydl.extract_info(dl_target, download=True)

                    entries = []
                    if info and "entries" in info:
                        entries = [e for e in (info["entries"] or []) if e]
                    elif info:
                        entries = [info]

                    for entry in entries:
                        vid_id = entry.get("id", "direct_url")
                        duration = entry.get("duration", 999)
                        if duration > max_dur and not is_url:
                            console.print(f"[dim]Skip {vid_id} (too long: {duration}s)[/]")
                            continue
                        # Find the downloaded file
                        for ext in ["mp4", "webm", "mkv"]:
                            f = self.clip_dir / f"{anime_key}_{style}_{vid_id}.{ext}"
                            if f.exists() and f.stat().st_size > 500_000:
                                console.print(f"[green]✓ Downloaded:[/] {f.name} ({f.stat().st_size//1024}KB)")
                                return f
                        for f in self.clip_dir.glob(f"{anime_key}_{style}_{vid_id}*"):
                            if f.stat().st_size > 500_000:
                                console.print(f"[green]✓ Found:[/] {f.name}")
                                return f

            except Exception as e:
                console.print(f"[yellow]Format {fmt[:30]} failed: {str(e)[:50]}...[/]")
                continue

        # All formats failed, try using any cached clip
        console.print("[red]All download attempts failed, trying cached fallback...[/]")
        return self._use_any_cached_clip(anime_key, style)

    def _use_any_cached_clip(self, anime_key: str, style: str) -> Optional[Path]:
        """Fallback: use any available cached clip."""
        # Try same anime, any style
        any_anime = list(self.clip_dir.glob(f"{anime_key}_*.mp4"))
        if any_anime:
            c = random.choice(any_anime)
            if c.stat().st_size > 500_000:
                console.print(f"[yellow]Fallback: using {c.name}[/]")
                return c
        
        # Try any clip at all
        any_clip = list(self.clip_dir.glob("*.mp4"))
        if any_clip:
            c = random.choice(any_clip)
            if c.stat().st_size > 500_000:
                console.print(f"[yellow]Emergency fallback: using {c.name}[/]")
                return c
        
        console.print("[red]No cached clips available[/]")
        return None


    def get_best_segment(self, video_path: Path, target_dur: float = 25.0) -> Tuple[float, float]:
        """Find the highest-energy segment using frame difference analysis."""
        try:
            from moviepy.editor import VideoFileClip
            import numpy as np

            clip = VideoFileClip(str(video_path))
            total = clip.duration

            if total <= target_dur + 5:
                clip.close()
                return (0.0, min(target_dur, total))

            step = 3.0
            best_score = -1.0
            best_start = total * 0.2

            search_start = total * 0.15
            search_end = max(search_start + 1, total * 0.82 - target_dur)

            scores = {}
            prev_frame = None
            t = search_start
            while t < search_end:
                try:
                    frame = clip.get_frame(t)
                    if prev_frame is not None:
                        diff = float(np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))))
                        scores[t] = diff
                    prev_frame = frame
                except Exception:
                    pass
                t += step

            clip.close()

            if scores:
                best_t = max(scores, key=scores.get)
                best_start = max(0, best_t - target_dur / 2)
                console.print(f"[dim]Best segment: {best_start:.1f}s -> {best_start+target_dur:.1f}s[/]")

            return (best_start, min(best_start + target_dur, total))

        except Exception as e:
            console.print(f"[yellow]Segment pick failed ({e}), using 0[/]")
            return (0.0, target_dur)
