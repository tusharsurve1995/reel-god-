"""
REEL GOD - Royalty-Free Stock Fetcher
=====================================
Pulls HD b-roll VIDEO and PHOTOS from free, legally-reusable sources so REEL GOD
can build a Reel/Post/Story from "the whole internet" without any copyright risk:

  - Pexels   (https://www.pexels.com/api/)   — video + photos, free API key
  - Pixabay  (https://pixabay.com/api/docs/)  — video + photos, free API key

Everything is licensed for reuse (Pexels License / Pixabay Content License), so
the output is safe to post to Instagram. Unlike scraping copyrighted anime from
YouTube, this never gets bot-blocked on a server and never triggers takedowns.

Design goals mirror the existing AnimeFetcher / MusicFetcher:
  - Cache downloads under data/stock_clips/ and reuse them.
  - Degrade gracefully: no API key or a failed request → return None so the
    caller can fall back (e.g. to a cached clip or the upload path).
"""
import re
import random
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from rich.console import Console

import config

console = Console()

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"
PIXABAY_PHOTO_URL = "https://pixabay.com/api/"

# Map REEL GOD moods/styles → good stock search terms. Anime footage isn't on
# stock sites, so we translate the emotional register into cinematic b-roll that
# fits the same vibe.
STYLE_TO_STOCK_QUERY = {
    "epic_action":    ["dramatic storm clouds", "fast city lights motion", "powerful ocean waves", "lightning night sky"],
    "emotional":      ["rain on window", "lonely person silhouette sunset", "slow candle flame", "misty mountain morning"],
    "romance":        ["golden hour couple", "cherry blossom petals falling", "soft bokeh lights", "sunset over sea"],
    "dark_cinematic": ["dark moody forest fog", "neon city night rain", "abstract dark smoke", "storm at night"],
    "motivational":   ["sunrise mountain summit", "runner training", "city skyline timelapse", "waves crashing rocks"],
    "mystical":       ["milky way galaxy stars", "northern lights aurora", "glowing forest fireflies", "ethereal clouds"],
    "sacrifice":      ["dramatic sky sunset", "flag waving slow motion", "candle memorial", "waves stormy sea"],
    "happy":          ["colorful confetti", "sunny beach summer", "smiling city crowd", "bright flowers field"],
}


class StockFetcher:
    """Downloads royalty-free HD video/photos from Pexels and Pixabay."""

    def __init__(self):
        self.clip_dir = config.DATA_DIR / "stock_clips"
        self.clip_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────
    def available(self) -> bool:
        return bool(config.stock_sources_available())

    def query_for_style(self, style: str, instruction: str = "") -> str:
        """Pick a stock search phrase. A commander directive always wins."""
        directive = (instruction or "").strip()
        if directive:
            return directive
        pool = STYLE_TO_STOCK_QUERY.get(style, STYLE_TO_STOCK_QUERY["motivational"])
        return random.choice(pool)

    def fetch_video(self, query: str, *, want_vertical: bool = True) -> Optional[Path]:
        """Return a path to an HD stock video matching `query`, or None.

        Tries every configured provider in random order, then falls back to a
        previously cached stock clip.
        """
        query = (query or "").strip() or "cinematic background"
        cached = self._cached_clip(query)
        if cached:
            console.print(f"[green]Using cached stock clip:[/] {cached.name}")
            return cached

        providers = config.stock_sources_available()
        random.shuffle(providers)
        for provider in providers:
            try:
                if provider == "pexels":
                    path = self._pexels_video(query, want_vertical)
                else:
                    path = self._pixabay_video(query, want_vertical)
                if path:
                    return path
            except Exception as e:  # network / quota / shape errors → next provider
                console.print(f"[yellow]{provider} video fetch failed: {str(e)[:60]}[/]")

        # No key or all providers failed → reuse any cached stock clip.
        return self._any_cached_clip()

    def fetch_photo(self, query: str) -> Optional[Path]:
        """Return a path to a royalty-free HD photo matching `query`, or None."""
        query = (query or "").strip() or "cinematic background"
        providers = config.stock_sources_available()
        random.shuffle(providers)
        for provider in providers:
            try:
                if provider == "pexels":
                    path = self._pexels_photo(query)
                else:
                    path = self._pixabay_photo(query)
                if path:
                    return path
            except Exception as e:
                console.print(f"[yellow]{provider} photo fetch failed: {str(e)[:60]}[/]")
        return None

    # ── Pexels ────────────────────────────────────────────────────────────────
    def _pexels_video(self, query: str, want_vertical: bool) -> Optional[Path]:
        headers = {"Authorization": config.PEXELS_API_KEY}
        params = {
            "query": query,
            "per_page": 15,
            "orientation": "portrait" if want_vertical else "landscape",
            "size": "large",
        }
        r = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None
        video = random.choice(videos)
        file_url = self._best_pexels_file(video.get("video_files", []), want_vertical)
        if not file_url:
            return None
        return self._download(file_url, f"pexels_{video.get('id', 'x')}", query, ".mp4")

    @staticmethod
    def _best_pexels_file(files: List[Dict[str, Any]], want_vertical: bool) -> Optional[str]:
        """Choose the highest-res <=1080p HD .mp4 file link."""
        candidates = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
        if not candidates:
            return None

        def score(f: Dict[str, Any]) -> tuple:
            h = f.get("height") or 0
            w = f.get("width") or 0
            vertical_ok = 1 if (h >= w) == want_vertical else 0
            cap = 1 if h <= 1200 else 0  # prefer <=1080p so downloads stay quick
            return (vertical_ok, cap, h)

        return max(candidates, key=score)["link"]

    def _pexels_photo(self, query: str) -> Optional[Path]:
        headers = {"Authorization": config.PEXELS_API_KEY}
        params = {"query": query, "per_page": 15, "orientation": "portrait", "size": "large"}
        r = requests.get(PEXELS_PHOTO_URL, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos)
        src = (photo.get("src") or {})
        url = src.get("large2x") or src.get("large") or src.get("original")
        if not url:
            return None
        return self._download(url, f"pexels_photo_{photo.get('id', 'x')}", query, ".jpg")

    # ── Pixabay ───────────────────────────────────────────────────────────────
    def _pixabay_video(self, query: str, want_vertical: bool) -> Optional[Path]:
        params = {"key": config.PIXABAY_API_KEY, "q": query, "per_page": 20, "safesearch": "true"}
        r = requests.get(PIXABAY_VIDEO_URL, params=params, timeout=20)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits)
        streams = hit.get("videos", {})
        stream = streams.get("large") or streams.get("medium") or streams.get("small")
        if not stream or not stream.get("url"):
            return None
        return self._download(stream["url"], f"pixabay_{hit.get('id', 'x')}", query, ".mp4")

    def _pixabay_photo(self, query: str) -> Optional[Path]:
        params = {
            "key": config.PIXABAY_API_KEY, "q": query, "per_page": 20,
            "image_type": "photo", "safesearch": "true", "min_height": 1080,
        }
        r = requests.get(PIXABAY_PHOTO_URL, params=params, timeout=20)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits)
        url = hit.get("largeImageURL") or hit.get("webformatURL")
        if not url:
            return None
        return self._download(url, f"pixabay_photo_{hit.get('id', 'x')}", query, ".jpg")

    # ── Shared helpers ────────────────────────────────────────────────────────
    def _download(self, url: str, ident: str, query: str, ext: str) -> Optional[Path]:
        tag = re.sub(r"[^a-z0-9_]", "", query.lower().replace(" ", "_"))[:30]
        dest = self.clip_dir / f"{tag}_{ident}{ext}"
        if dest.exists() and dest.stat().st_size > 100_000:
            return dest
        console.print(f"[cyan]Downloading stock media:[/] {ident} for '{query}'")
        with requests.get(url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    fh.write(chunk)
        if dest.stat().st_size < 50_000:
            dest.unlink(missing_ok=True)
            return None
        console.print(f"[green]✓ Stock media ready:[/] {dest.name} ({dest.stat().st_size // 1024}KB)")
        return dest

    def _cached_clip(self, query: str) -> Optional[Path]:
        tag = re.sub(r"[^a-z0-9_]", "", query.lower().replace(" ", "_"))[:30]
        matches = [p for p in self.clip_dir.glob(f"{tag}_*.mp4") if p.stat().st_size > 100_000]
        return random.choice(matches) if matches else None

    def _any_cached_clip(self) -> Optional[Path]:
        matches = [p for p in self.clip_dir.glob("*.mp4") if p.stat().st_size > 100_000]
        if matches:
            c = random.choice(matches)
            console.print(f"[yellow]Stock fallback: using cached {c.name}[/]")
            return c
        return None
