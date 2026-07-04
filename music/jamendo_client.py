"""
REEL GOD — Jamendo Music Client
===============================
Fetches CC-licensed instrumental background music matching content styles.
Integrates with SQLite memory to cache tracks and handle offline fallbacks.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any
from rich.console import Console

import config

console = Console()


class JamendoClient:
    """
    Client for the Jamendo API v3.0 to search and download royalty-free music.
    
    Responsibilities:
    - Search for tracks based on mood and style mapping
    - Handle downloads and save to data/music_library
    - Manage offline fallback tracks
    """
    
    # Static fallbacks (SoundHelix testing tracks - robust, publicly available instrumentals)
    FALLBACK_TRACKS = {
        "dark_cinematic": {
            "title": "Helix Cinematic Dark",
            "artist": "Helix Tech",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        },
        "emotional": {
            "title": "Helix Emotional Acoustic",
            "artist": "Helix Tech",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
        },
        "epic_action": {
            "title": "Helix Epic Action",
            "artist": "Helix Tech",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
        },
        "mystical": {
            "title": "Helix Mystical Ethereal",
            "artist": "Helix Tech",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
        },
        "motivational": {
            "title": "Helix Motivational Rock",
            "artist": "Helix Tech",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"
        }
    }
    
    # Map styles to Jamendo search tags
    STYLE_TAG_MAP = {
        "dark_cinematic": ["dark", "ambient", "cinematic", "sad"],
        "emotional": ["emotional", "piano", "acoustic", "sad", "dramatic"],
        "epic_action": ["epic", "orchestral", "electronic", "battle", "action"],
        "mystical": ["fantasy", "mystical", "ethereal", "ambient", "magic"],
        "motivational": ["motivational", "energetic", "inspiring", "rock", "uplifting"]
    }
    
    def __init__(self):
        self.client_id = config.JAMENDO_CLIENT_ID
        self.base_url = "https://api.jamendo.com/v3.0"
        self.music_dir = config.MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)
        console.print("[dim]Jamendo Music Client initialized[/dim]")
        
    def get_track_for_style(self, style: str, memory) -> Path:
        """
        Get a track matching the style. Checks local SQLite library first.
        If empty, fetches from Jamendo API. Falls back to static URLs if offline/no key.
        
        Args:
            style: The content style (dark_cinematic, emotional, etc.)
            memory: AgentMemory instance to check/save tracks
            
        Returns:
            Path to the downloaded track file.
        """
        # 1. Check local cache in database
        cached_tracks = memory.get_music_by_mood(style, limit=5)
        for track in cached_tracks:
            file_path = Path(track["file_path"])
            if file_path.exists():
                console.print(f"[green]✓ Reusing cached track:[/] {track['title']} ({file_path.name})")
                memory.mark_music_used(track["id"])
                return file_path
                
        # 2. Try to fetch from Jamendo API
        if self.client_id and self.client_id != "PASTE_YOUR_KEY_HERE":
            try:
                tags = self.STYLE_TAG_MAP.get(style, ["cinematic"])
                track_data = self._search_jamendo(tags)
                if track_data:
                    downloaded_path = self._download_track(track_data, style, memory)
                    if downloaded_path:
                        return downloaded_path
            except Exception as e:
                console.print(f"[yellow]Jamendo API search failed: {e}. Falling back to default track.[/yellow]")
        else:
            console.print("[yellow]Jamendo API Client ID not configured. Using default fallback track.[/yellow]")
            
        # 3. Fallback: Download from SoundHelix static URL
        return self._get_fallback_track(style, memory)
        
    def _search_jamendo(self, tags: List[str]) -> Optional[Dict[str, Any]]:
        """Query Jamendo API for instrumental tracks matching tags."""
        url = f"{self.base_url}/tracks/"
        # Join tags with a plus sign for Jamendo search
        tag_str = "+".join(tags)
        params = {
            "client_id": self.client_id,
            "format": "json",
            "limit": 10,
            "order": "popularity_total",
            "tags": tag_str,
            "vocalinstrumental": "instrumental",
            "audioformat": "mp32"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                # Return the best match that has download url
                for track in results:
                    if track.get("audio") and track.get("audiodownload_allowed", True):
                        return track
        return None
        
    def _download_track(self, track_data: Dict[str, Any], style: str, memory) -> Optional[Path]:
        """Download track from URL and register in the database."""
        track_url = track_data.get("audio")
        title = track_data.get("name", "Unknown Title")
        artist = track_data.get("artist_name", "Unknown Artist")
        jamendo_id = track_data.get("id")
        duration = float(track_data.get("duration", 0))
        
        # Clean title for filename safety
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
        filename = f"jamendo_{style}_{jamendo_id}_{safe_title.replace(' ', '_')}.mp3"
        save_path = self.music_dir / filename
        
        console.print(f"[cyan]Downloading Jamendo track: {title} by {artist}...[/cyan]")
        try:
            response = requests.get(track_url, timeout=30)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                # Save to database
                memory.save_music(
                    title=title,
                    artist=artist,
                    mood=style,
                    genre="instrumental",
                    file_path=str(save_path),
                    jamendo_id=str(jamendo_id),
                    source_url=track_url,
                    duration=duration
                )
                console.print(f"[green]✓ Saved track to library:[/] {save_path.name}")
                return save_path
        except Exception as e:
            console.print(f"[red]Failed to download track '{title}': {e}[/red]")
        return None

    def _get_fallback_track(self, style: str, memory) -> Path:
        """Download static SoundHelix track as a fallback."""
        track_info = self.FALLBACK_TRACKS.get(style, self.FALLBACK_TRACKS["dark_cinematic"])
        url = track_info["url"]
        title = track_info["title"]
        artist = track_info["artist"]
        
        filename = f"fallback_{style}_{Path(url).name}"
        save_path = self.music_dir / filename
        
        # Check if already downloaded
        if save_path.exists():
            # Ensure it is registered in db
            tracks = memory.get_music_by_mood(style, limit=10)
            already_registered = any(t["file_path"] == str(save_path) for t in tracks)
            if not already_registered:
                memory.save_music(
                    title=title,
                    artist=artist,
                    mood=style,
                    genre="instrumental",
                    file_path=str(save_path),
                    source_url=url,
                    duration=300.0  # SoundHelix tracks are typically around 5 mins
                )
            return save_path
            
        console.print(f"[cyan]Downloading fallback track: {title}...[/cyan]")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                memory.save_music(
                    title=title,
                    artist=artist,
                    mood=style,
                    genre="instrumental",
                    file_path=str(save_path),
                    source_url=url,
                    duration=300.0
                )
                console.print(f"[green]✓ Fallback track saved:[/] {save_path.name}")
                return save_path
        except Exception as e:
            console.print(f"[red]Failed to download fallback track '{title}': {e}[/red]")
            # Return any existing mp3 file as absolute worst case fallback
            existing_mp3s = list(self.music_dir.glob("*.mp3"))
            if existing_mp3s:
                console.print(f"[yellow]Using existing mp3 from library: {existing_mp3s[0].name}[/yellow]")
                return existing_mp3s[0]
            raise RuntimeError(f"Could not download fallback track or find local tracks. Details: {e}")
