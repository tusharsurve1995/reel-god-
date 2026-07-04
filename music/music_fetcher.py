"""
REEL GOD - Music Fetcher
Downloads Bollywood, Hollywood, and Instrumental music from YouTube
using yt-dlp (audio-only). Matches music to anime mood/style.
"""
import os, sys, re, random
from pathlib import Path
from typing import Optional
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

# ══════════════════════════════════════════════════════════════════════════════
#  REEL GOD MUSIC LIBRARY
#  Every mood = Bollywood + Hollywood + Instrumental options
#  Tracks selected for maximum emotional impact and virality
# ══════════════════════════════════════════════════════════════════════════════

MUSIC_BY_MOOD = {

    # ── ROMANTIC ─────────────────────────────────────────────────────────────
    # Warm, tender, longing — for love stories and bittersweet moments
    "romantic_bollywood": [
        "Kesariya Brahmastra full song instrumental",
        "Tujhe Kitna Chahne Lage piano cover instrumental",
        "Raataan Lambiyan guitar instrumental cover",
        "Kal Ho Na Ho piano instrumental sad",
        "Ae Dil Hai Mushkil sad instrumental piano",
        "Hawayein Jab Harry Met Sejal instrumental",
        "Tere Bina Guru piano instrumental",
        "Pehla Nasha piano instrumental",
    ],
    "romantic_hollywood": [
        "City of Stars La La Land piano instrumental",
        "A Thousand Years Christina Perri piano",
        "Can't Help Falling In Love piano cover",
        "Perfect Ed Sheeran piano instrumental",
        "All of Me John Legend piano instrumental",
        "Thinking Out Loud Ed Sheeran piano",
        "Thousand Years piano violin cover",
    ],
    "romantic_instrumental": [
        "Beautiful romantic orchestral music no copyright",
        "Emotional love piano music no copyright",
        "Romantic violin piano music instrumental",
        "Soft romantic background music emotional",
        "Anime romantic piano ost compilation",
    ],

    # ── SACRIFICE / HEROIC ────────────────────────────────────────────────────
    # Noble, tragic, powerful — for characters who give everything
    "sacrifice_bollywood": [
        "Rang De Basanti main theme instrumental",
        "Lakshya theme music instrumental heroic",
        "Swades Yun Hi Chala Chal instrumental",
        "Border Sandese Aate Hain instrumental",
        "Uri The Surgical Strike theme instrumental",
        "Baby Ko Bass Pasand Hai Dhoom Bhaag",
    ],
    "sacrifice_hollywood": [
        "Hans Zimmer Now We Are Free Gladiator",
        "Interstellar Stay Hans Zimmer piano",
        "Transformers Arrival to Earth orchestral",
        "Pirates of Caribbean He's a Pirate epic",
        "Lord of the Rings May It Be Enya",
        "Hans Zimmer Cornfield Chase Interstellar",
        "Avengers Endgame Portals scene music",
    ],
    "sacrifice_instrumental": [
        "Epic heroic orchestral music no copyright sacrifice",
        "Emotional cinematic sacrifice theme orchestral",
        "Dramatic cinematic orchestra hero moment",
        "Anime sacrifice music emotional epic",
        "Noble sacrifice orchestral emotional music",
    ],

    # ── EMOTIONAL / SAD ───────────────────────────────────────────────────────
    # Tearful, poignant, heart-wrenching — for loss, goodbye, heartbreak
    "emotional_bollywood": [
        "Tum Hi Ho Aashiqui 2 piano instrumental",
        "Phir Le Aya Dil Barfi piano sad",
        "Channa Mereya piano sad instrumental",
        "Agar Tum Saath Ho Tamasha instrumental",
        "Kabira Yeh Jawaani Hai Deewani piano sad",
        "Jo Bhi Main Rockstar piano instrumental",
        "Safar Jab Harry Met Sejal piano",
        "Teri Mitti Kesari piano sad instrumental",
    ],
    "emotional_hollywood": [
        "My Heart Will Go On Titanic piano instrumental",
        "Interstellar Main Theme Hans Zimmer piano emotional",
        "Arrival Amy Adams theme piano emotional",
        "Forrest Gump Feather Theme piano",
        "Schindler's List Main Theme violin emotional",
        "Your Lie in April Otomodachi piano ost",
        "Violet Evergarden OST piano emotional",
        "Clannad Dango Daikazoku piano",
    ],
    "emotional_instrumental": [
        "Sad emotional anime piano music no copyright",
        "Heartbreaking piano music emotional cinematic",
        "Crying emotional piano music no copyright",
        "Sad violin music emotional cinematic no copyright",
        "Emotional piano music anime style beautiful",
    ],

    # ── MOTIVATIONAL / RISE ───────────────────────────────────────────────────
    # Uplifting, triumphant, building — for training, comeback, determination
    "motivational_bollywood": [
        "Kar Har Maidan Fateh instrumental Sanju",
        "Sultan AR Rahman instrumental theme",
        "Dangal OST Aamir Khan instrumental",
        "Bhaag Milkha Bhaag title instrumental",
        "Chak De India instrumental",
        "Mary Kom theme music instrumental",
    ],
    "motivational_hollywood": [
        "Eye of the Tiger Survivor instrumental",
        "Hall of Fame The Script piano",
        "Believer Imagine Dragons instrumental",
        "Warriors Imagine Dragons instrumental",
        "Lose Yourself Eminem instrumental",
        "Stronger Kanye West instrumental beat",
        "Till I Collapse Eminem instrumental",
    ],
    "motivational_instrumental": [
        "Epic motivational music no copyright rise",
        "Uplifting cinematic music no copyright training",
        "Inspirational orchestral music no copyright",
        "Rise up powerful orchestral music no copyright",
        "Anime motivational background music no copyright",
    ],

    # ── DARK CINEMATIC ────────────────────────────────────────────────────────
    # Brooding, tense, atmospheric — for tragedy, darkness, destiny
    "dark_cinematic_hollywood": [
        "Hans Zimmer Dark Knight Rises orchestral",
        "Inception BRAAAM Hans Zimmer",
        "Joker 2019 theme music dark",
        "Batman v Superman Is She with You",
        "Requiem for a Dream dark orchestral",
        "Hans Zimmer Man of Steel No Mercy",
    ],
    "dark_cinematic_instrumental": [
        "Dark cinematic orchestral music no copyright",
        "Epic dark dramatic music no copyright",
        "Anime dark atmospheric music no copyright",
        "Tension cinematic music dark no copyright",
        "AOT Attack on Titan OST dark theme",
    ],

    # ── EPIC ACTION ───────────────────────────────────────────────────────────
    # Explosive, hype, adrenaline — for battles and power moments
    "epic_action_bollywood": [
        "Pathaan title track instrumental",
        "War 2019 instrumental theme",
        "Bang Bang film instrumental theme",
        "Dhoom 3 instrumental theme",
        "Fighter film action theme instrumental",
    ],
    "epic_action_hollywood": [
        "Two Steps From Hell Heart of Courage",
        "Avengers theme full orchestra epic",
        "Batman Dark Knight orchestral",
        "Wonder Woman No Man's Land theme",
        "Thor Ragnarok Immigrant Song Led Zeppelin",
        "Superman theme John Williams epic",
    ],
    "epic_action_instrumental": [
        "Demon Slayer Gurenge instrumental epic",
        "Jujutsu Kaisen opening instrumental",
        "Naruto Shippuden opening instrumental",
        "Epic battle music no copyright anime style",
        "Action cinematic music no copyright intense",
    ],

    # ── MYSTICAL / ETHEREAL ───────────────────────────────────────────────────
    # Wonder, ancient, magical — for otherworldly and fantasy moments
    "mystical_hollywood": [
        "Lord of the Rings Shire theme piano",
        "Spirited Away Joe Hisaishi piano",
        "Princess Mononoke theme orchestra",
        "Howl's Moving Castle Merry Go Round",
        "Doctor Strange theme mystical",
        "Avatar main theme Pandora James Horner",
    ],
    "mystical_instrumental": [
        "Mystical fantasy music no copyright ethereal",
        "Ancient magical orchestral music no copyright",
        "Ethereal ambient music no copyright mystical",
        "Anime mystical piano music no copyright",
        "Frieren OST piano instrumental beautiful",
    ],
}

# ── GENRE-FIRST QUERY POOLS ───────────────────────────────────────────────────
# Used when the Commander explicitly picks a music genre in the dashboard.
# {mood} is substituted with the reel's emotional register (e.g. "romantic", "epic").
MUSIC_BY_GENRE = {
    "bollywood": [
        "{mood} Bollywood song instrumental cover",
        "best {mood} Hindi film music instrumental",
        "trending Bollywood {mood} background music",
    ],
    "hollywood": [
        "{mood} Hollywood movie soundtrack orchestral",
        "epic {mood} film score cinematic",
        "{mood} Hans Zimmer style orchestral music",
    ],
    "pop": [
        "{mood} pop song instrumental no copyright",
        "trending pop {mood} background music no copyright",
        "upbeat {mood} pop instrumental viral",
    ],
    "instrumental": [
        "{mood} instrumental music no copyright",
        "{mood} piano instrumental emotional no copyright",
        "cinematic {mood} instrumental background no copyright",
    ],
    "action": [
        "{mood} epic action battle music no copyright",
        "intense {mood} trailer music cinematic",
        "hype {mood} action background music no copyright",
    ],
    "romantic": [
        "{mood} romantic love song instrumental",
        "soft {mood} romantic piano music",
        "beautiful {mood} romantic background music",
    ],
    "worldwide": [
        "{mood} world music no copyright global",
        "{mood} international cinematic music no copyright",
        "epic {mood} global soundtrack no copyright",
    ],
}

# Map reel styles → a natural-language mood word used to flavour genre queries
STYLE_TO_MOOD_WORD = {
    "epic_action":    "epic",
    "emotional":      "emotional sad",
    "romance":        "romantic",
    "dark_cinematic": "dark cinematic",
    "motivational":   "motivational uplifting",
    "mystical":       "mystical ethereal",
    "sacrifice":      "heroic emotional",
    "happy":          "happy upbeat",
}

# ── ANIME × STYLE → MUSIC MOOD PRIORITY LIST ──────────────────────────────────
# Carefully matched: specific Bollywood/Hollywood tracks per anime theme
ANIME_MUSIC_MAP = {
    # Action styles → heroic Hollywood + action Bollywood
    "epic_action":    [
        "epic_action_hollywood", "epic_action_bollywood", "epic_action_instrumental",
        "sacrifice_hollywood", "motivational_bollywood",
    ],
    # Sacrifice/tragic → noble Hollywood + Bollywood patriotic
    "sacrifice":      [
        "sacrifice_hollywood", "sacrifice_bollywood", "sacrifice_instrumental",
        "emotional_hollywood", "dark_cinematic_hollywood",
    ],
    # Emotional/sad → heart-wrenching Bollywood + Hollywood piano
    "emotional":      [
        "emotional_bollywood", "emotional_hollywood", "emotional_instrumental",
        "romantic_bollywood", "sacrifice_instrumental",
    ],
    # Romance → warm Bollywood love + Hollywood tender
    "romance":        [
        "romantic_bollywood", "romantic_hollywood", "romantic_instrumental",
        "emotional_bollywood", "emotional_hollywood",
    ],
    # Motivational/rise → upbeat Bollywood + power Hollywood
    "motivational":   [
        "motivational_bollywood", "motivational_hollywood", "motivational_instrumental",
        "epic_action_bollywood", "sacrifice_hollywood",
    ],
    # Dark cinematic → tense Hollywood + atmospheric
    "dark_cinematic": [
        "dark_cinematic_hollywood", "dark_cinematic_instrumental",
        "sacrifice_hollywood", "emotional_hollywood",
    ],
    # Mystical/wonder → fantasy Hollywood + ethereal
    "mystical":       [
        "mystical_hollywood", "mystical_instrumental",
        "emotional_hollywood", "romantic_instrumental",
    ],
    # Happy → upbeat motivational
    "happy":          [
        "motivational_bollywood", "motivational_instrumental",
        "epic_action_bollywood", "romantic_bollywood",
    ],
}

# ── ANIME-SPECIFIC MUSIC OVERRIDES ────────────────────────────────────────────
# Best-matched tracks for specific anime × style combos
ANIME_SPECIFIC_MUSIC = {
    # Your Lie in April is ALL about piano and music — use piano tracks
    ("your_lie_in_april", "romance"):        ["Your Lie in April OST piano shigatsu", "Tujhe Kitna Chahne Lage piano cover"],
    ("your_lie_in_april", "emotional"):      ["Shigatsu wa Kimi no Uso sad piano OST", "Tum Hi Ho piano sad instrumental"],
    # Violet Evergarden — lush orchestral and emotional piano
    ("violet_evergarden", "romance"):        ["Violet Evergarden OST piano beautiful", "Kal Ho Na Ho instrumental sad"],
    ("violet_evergarden", "emotional"):      ["Violet Evergarden Letter OST piano", "Clannad Dango Daikazoku piano emotional"],
    # Attack on Titan — powerful, cinematic, epic
    ("attack_on_titan", "sacrifice"):        ["Attack on Titan Vogel im Kafig orchestral", "Interstellar Stay Hans Zimmer"],
    ("attack_on_titan", "dark_cinematic"):   ["AOT Levi Theme piano dark", "Hans Zimmer Dark Knight orchestral"],
    # Naruto — emotional breakdown scenes need sad Bollywood + rise scenes need hype
    ("naruto", "emotional"):                 ["Naruto Sadness and Sorrow piano", "Tum Hi Ho Aashiqui 2 piano instrumental"],
    ("naruto", "motivational"):              ["Naruto Shippuden opening piano", "Kar Har Maidan Fateh instrumental"],
    # Demon Slayer — intense fire-breathing music
    ("demon_slayer", "epic_action"):         ["Demon Slayer Gurenge instrumental", "Two Steps From Hell Heart of Courage"],
    ("demon_slayer", "emotional"):           ["Demon Slayer Mugen Train theme piano", "Phir Le Aya Dil Barfi piano"],
    # Fullmetal Alchemist — equivalent exchange = sacrifice and hope
    ("fullmetal_alchemist", "sacrifice"):    ["FMA Brotherhood OST emotional piano", "Rang De Basanti main theme instrumental"],
    ("fullmetal_alchemist", "emotional"):    ["FMA Brotherhood Lullaby instrumental", "Channa Mereya piano sad"],
    # Re:Zero — dark tragedy with romantic hope
    ("re_zero", "emotional"):               ["Re Zero OST piano sad", "Safar Jab Harry Met Sejal piano"],
    ("re_zero", "romance"):                 ["Re Zero Rem theme piano", "Raataan Lambiyan guitar instrumental"],
}


class MusicFetcher:
    """Downloads mood-matched music from YouTube as MP3 audio."""

    def __init__(self):
        self.music_dir = config.MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)

    def fetch_for_style(self, style: str, anime: str = None) -> Optional[Path]:
        """Get music matching anime style + optionally a specific anime. Checks cache first."""
        # Build cache tag: prefer anime-specific cache
        cache_tag = f"{anime}_{style}" if anime else style
        safe_cache = re.sub(r"[^a-z0-9_]", "", cache_tag.lower())[:30]
        cached = list(self.music_dir.glob(f"{safe_cache}_*.mp3"))
        if not cached:
            # Also check generic style cache as fallback
            cached = list(self.music_dir.glob(f"{style}_*.mp3"))
        if cached:
            track = random.choice(cached)
            console.print(f"[green]Music cached:[/] {track.name}")
            return track

        # Check anime-specific override first
        if anime:
            override_key = (anime, style)
            if override_key in ANIME_SPECIFIC_MUSIC:
                queries = ANIME_SPECIFIC_MUSIC[override_key]
                query = random.choice(queries)
                console.print(f"[bold magenta]Music override [{anime}+{style}]:[/] {query}")
                result = self._download_audio(query, safe_cache)
                if result:
                    return result

        # Use mood priority list
        mood_options = ANIME_MUSIC_MAP.get(style, ["epic_action_hollywood"])
        for mood in mood_options:
            queries = MUSIC_BY_MOOD.get(mood, [])
            if not queries:
                continue
            query = random.choice(queries)
            console.print(f"[bold cyan]Music [{mood}]:[/] {query}")
            result = self._download_audio(query, safe_cache)
            if result:
                return result

        # Fallback to SoundHelix
        return self._soundhelix_fallback(style)

    def fetch_for_anime_and_style(self, anime: str, style: str) -> Optional[Path]:
        """Fetch music perfectly matched to a specific anime + style combination."""
        return self.fetch_for_style(style=style, anime=anime)

    def fetch_by_genre(self, genre: str, style: str = "epic_action", anime: str = None) -> Optional[Path]:
        """Fetch music for an explicitly chosen genre matched to the reel's mood.

        genre ∈ {auto, bollywood, hollywood, pop, instrumental, action, romantic, worldwide}.
        'auto' (or unknown) falls back to the smart anime/style matcher.
        """
        genre = (genre or "auto").strip().lower()
        if genre in ("", "auto", "any", "smart"):
            return self.fetch_for_style(style, anime=anime)

        pool = MUSIC_BY_GENRE.get(genre)
        if not pool:
            console.print(f"[yellow]Unknown genre '{genre}', using smart match[/]")
            return self.fetch_for_style(style, anime=anime)

        mood_word = STYLE_TO_MOOD_WORD.get(style, style.replace("_", " "))
        template = random.choice(pool)
        query = template.format(mood=mood_word)
        console.print(f"[bold cyan]Music [{genre} · {style}]:[/] {query}")

        safe_cache = re.sub(r"[^a-z0-9_]", "", f"{genre}_{style}".lower())[:30]
        result = self._download_audio(query, safe_cache)
        if result:
            return result
        # Fall back to the smart matcher, then SoundHelix
        return self.fetch_for_style(style, anime=anime)

    def fetch_by_mood(self, mood: str, style: str = "epic_action") -> Optional[Path]:
        """Download music by explicit mood name."""
        queries = MUSIC_BY_MOOD.get(mood, list(MUSIC_BY_MOOD.get("emotional_bollywood", [])))
        if not queries:
            queries = ["cinematic instrumental no copyright"]
        query = random.choice(queries)
        console.print(f"[bold cyan]Music ({mood}):[/] {query}")
        return self._download_audio(query, f"{style}_{mood}")


    def _download_audio(self, query: str, tag: str) -> Optional[Path]:
        """Download audio-only track from YouTube with comprehensive fallbacks."""
        try:
            import yt_dlp
        except ImportError:
            console.print("[red]yt-dlp not installed[/]")
            return self._use_any_cached_music()

        safe_tag = re.sub(r"[^a-z0-9_]", "", tag.lower())[:30]
        out_tmpl = str(self.music_dir / f"{safe_tag}_%(id)s.%(ext)s")

        # Detect ffmpeg location for postprocessor
        ffmpeg_loc = None
        try:
            import imageio_ffmpeg
            ffmpeg_loc = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            import shutil
            ffmpeg_loc = shutil.which("ffmpeg")

        # Progressive format fallback
        formats = [
            "bestaudio[ext=m4a]/bestaudio/best",
            "bestaudio",
            "worst"
        ]

        for fmt in formats:
            ydl_opts = {
                "format": fmt,
                "outtmpl": out_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "socket_timeout": 30,
                "concurrent_fragment_download": True,
                "buffersize": 1024 * 16,
            }
            
            if ffmpeg_loc:
                ffmpeg_path_obj = Path(ffmpeg_loc)
                if ffmpeg_path_obj.name.lower() not in ["ffmpeg.exe", "ffmpeg"]:
                    local_ffmpeg = config.DATA_DIR / "bin" / "ffmpeg.exe"
                    if local_ffmpeg.exists():
                        ffmpeg_path_obj = local_ffmpeg
                ydl_opts["ffmpeg_location"] = str(ffmpeg_path_obj.parent)

            config.apply_ytdlp_auth(ydl_opts)

            try:
                console.print(f"[yellow]Attempting music download with format: {fmt[:30]}...[/]")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                    if info and "entries" in info and info["entries"]:
                        entry = info["entries"][0]
                        vid_id = entry.get("id", "")
                        for f in self.music_dir.glob(f"{safe_tag}_{vid_id}*.mp3"):
                            if f.stat().st_size > 100_000:
                                console.print(f"[green]✓ Downloaded:[/] {f.name}")
                                return f

            except Exception as e:
                console.print(f"[yellow]Music format {fmt[:30]} failed: {str(e)[:50]}...[/]")
                continue

        # All formats failed, try cached fallback
        console.print("[red]All music download attempts failed, trying cached fallback...[/]")
        return self._use_any_cached_music()

    def _use_any_cached_music(self) -> Optional[Path]:
        """Fallback: use any available cached music."""
        # Try any music file
        any_music = list(self.music_dir.glob("*.mp3"))
        if any_music:
            c = random.choice(any_music)
            if c.stat().st_size > 100_000:
                console.print(f"[yellow]Music fallback: using {c.name}[/]")
                return c
        
        console.print("[red]No cached music available[/]")
        return None

    def _soundhelix_fallback(self, style: str) -> Optional[Path]:
        """Download fallback music from SoundHelix."""
        import requests
        FALLBACKS = {
            "epic_action":    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
            "emotional":      "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            "dark_cinematic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "mystical":       "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
            "motivational":   "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
            "romance":        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        }
        url = FALLBACKS.get(style, FALLBACKS["epic_action"])
        save = self.music_dir / f"fallback_{style}.mp3"
        if save.exists() and save.stat().st_size > 50_000:
            return save
        try:
            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(save, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            console.print(f"[green]Fallback music:[/] {save.name}")
            return save
        except Exception as e:
            console.print(f"[red]Fallback music failed: {e}[/]")
            return None
