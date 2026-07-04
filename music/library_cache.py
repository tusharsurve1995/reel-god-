"""
REEL GOD — Music Library Cache
==============================
Manages the local music library with additional utilities beyond SQLite memory.
Provides library statistics, cleanup, and organization functions.
"""

from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
import shutil

import config

console = Console()


class MusicLibraryCache:
    """
    Manages the local music library with additional utilities.
    
    Responsibilities:
    - Provide library statistics (size, track count, mood distribution)
    - Clean up orphaned files (files not in database)
    - Organize library by mood/style
    - Validate library integrity
    """
    
    def __init__(self):
        """Initialize the library cache manager."""
        self.music_dir = config.MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)
        console.print("[dim]Music Library Cache initialized[/dim]")
    
    def get_library_stats(self, memory) -> Dict[str, any]:
        """
        Get statistics about the music library.
        
        Args:
            memory: AgentMemory instance to query database.
            
        Returns:
            Dictionary with library statistics.
        """
        # Count tracks by mood
        mood_counts = {}
        for mood in ["dark_cinematic", "emotional", "epic_action", "mystical", "motivational"]:
            tracks = memory.get_music_by_mood(mood, limit=1000)
            mood_counts[mood] = len(tracks)
        
        # Count total files
        mp3_files = list(self.music_dir.glob("*.mp3"))
        total_files = len(mp3_files)
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in mp3_files)
        total_size_mb = total_size / (1024 * 1024)
        
        stats = {
            "total_tracks": sum(mood_counts.values()),
            "total_files": total_files,
            "total_size_mb": round(total_size_mb, 2),
            "mood_distribution": mood_counts
        }
        
        return stats
    
    def print_library_stats(self, memory):
        """Print library statistics to console."""
        stats = self.get_library_stats(memory)
        
        console.print("\n[bold cyan]📊 Music Library Statistics[/bold cyan]")
        console.print(f"  Total Tracks: {stats['total_tracks']}")
        console.print(f"  Total Files: {stats['total_files']}")
        console.print(f"  Total Size: {stats['total_size_mb']} MB")
        console.print("\n[bold]Mood Distribution:[/bold]")
        
        for mood, count in stats["mood_distribution"].items():
            emoji = {"dark_cinematic": "🌑", "emotional": "💙", "epic_action": "⚔️", 
                    "mystical": "✨", "motivational": "🔥"}.get(mood, "🎵")
            console.print(f"  {emoji} {mood}: {count} tracks")
    
    def cleanup_orphaned_files(self, memory) -> int:
        """
        Remove MP3 files that are not in the database.
        
        Args:
            memory: AgentMemory instance to query database.
            
        Returns:
            Number of files removed.
        """
        mp3_files = list(self.music_dir.glob("*.mp3"))
        removed_count = 0
        
        # Get all file paths from database
        all_tracks = memory.get_all_music(limit=10000)
        db_paths = {track["file_path"] for track in all_tracks}
        
        for mp3_file in mp3_files:
            if str(mp3_file) not in db_paths:
                console.print(f"[yellow]Removing orphaned file:[/] {mp3_file.name}")
                mp3_file.unlink()
                removed_count += 1
        
        if removed_count > 0:
            console.print(f"[green]✓ Cleaned up {removed_count} orphaned file(s)[/green]")
        else:
            console.print("[dim]No orphaned files found[/dim]")
        
        return removed_count
    
    def organize_by_mood(self, memory):
        """
        Organize library into mood subdirectories.
        
        Args:
            memory: AgentMemory instance to query database.
        """
        console.print("[cyan]Organizing library by mood...[/cyan]")
        
        # Create mood subdirectories
        mood_dirs = {}
        for mood in ["dark_cinematic", "emotional", "epic_action", "mystical", "motivational"]:
            mood_dir = self.music_dir / mood
            mood_dir.mkdir(exist_ok=True)
            mood_dirs[mood] = mood_dir
        
        # Move files to appropriate directories
        all_tracks = memory.get_all_music(limit=10000)
        moved_count = 0
        
        for track in all_tracks:
            file_path = Path(track["file_path"])
            mood = track["mood"]
            
            if file_path.exists() and mood in mood_dirs:
                target_dir = mood_dirs[mood]
                target_path = target_dir / file_path.name
                
                # Move if not already in correct directory
                if file_path.parent != target_dir:
                    shutil.move(str(file_path), str(target_path))
                    
                    # Update database with new path
                    memory.update_music_path(track["id"], str(target_path))
                    moved_count += 1
                    console.print(f"[dim]  Moved:[/] {file_path.name} → {mood}/")
        
        console.print(f"[green]✓ Organized {moved_count} track(s)[/green]")
    
    def validate_library(self, memory) -> bool:
        """
        Validate library integrity.
        
        Args:
            memory: AgentMemory instance to query database.
            
        Returns:
            True if library is valid, False otherwise.
        """
        console.print("[cyan]Validating library integrity...[/cyan]")
        
        # Check for tracks in database with missing files
        all_tracks = memory.get_all_music(limit=10000)
        missing_files = []
        
        for track in all_tracks:
            file_path = Path(track["file_path"])
            if not file_path.exists():
                missing_files.append(track["title"])
        
        if missing_files:
            console.print(f"[red]✗ Found {len(missing_files)} tracks with missing files:[/red]")
            for title in missing_files[:5]:  # Show first 5
                console.print(f"  - {title}")
            if len(missing_files) > 5:
                console.print(f"  ... and {len(missing_files) - 5} more")
            return False
        else:
            console.print("[green]✓ All tracks have valid files[/green]")
            return True
