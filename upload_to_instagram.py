"""
REEL GOD — Instagram Upload CLI
================================
CLI tool to upload compiled anime reels to Instagram.
Uses the pre-upload pipeline (format check, cover thumbnail, caption building, Reel + Story).

Usage:
  py upload_to_instagram.py --mood romantic
  py upload_to_instagram.py --all
  py upload_to_instagram.py --file data/content_archive/romantic/your_lie_in_april_romance.mp4
  py upload_to_instagram.py --dry-run --all
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from instagram.publisher import InstagramPublisher
from generator.mood_organizer import MoodOrganizer

console = Console()

def main():
    parser = argparse.ArgumentParser(description="REEL GOD — Instagram Upload CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mood", type=str, help="Upload all reels in this mood folder")
    group.add_argument("--all", action="store_true", help="Upload all unposted reels in all mood folders")
    group.add_argument("--file", type=str, help="Upload a specific video file")
    
    parser.add_argument("--story", action="store_true", default=True, help="Also post cover thumbnail to Story")
    parser.add_argument("--no-story", dest="story", action="store_false", help="Do not post to Story")
    parser.add_argument("--dry-run", action="store_true", help="Dry run — simulate upload without calling Instagram API")
    
    args = parser.parse_args()
    
    console.print(Panel(
        "[bold cyan]REEL GOD — INSTAGRAM UPLOADER[/]\n"
        "[dim]Pre-upload format checks, thumbnail covers, and caption construction[/]",
        border_style="cyan"
    ))
    
    organizer = MoodOrganizer()
    publisher = InstagramPublisher()
    
    if args.dry_run:
        console.print("[bold yellow]⚠️  DRY RUN MODE ENABLED. No API calls will be made.[/bold yellow]\n")
        # Monkey patch cl to avoid loading real Client or calling it
        class MockClient:
            def clip_upload(self, path, caption, thumbnail):
                console.print(f"[bold yellow][MOCK CLIENT] Uploading Reel:[/] {Path(path).name}")
                console.print(f"[bold yellow][MOCK CLIENT] Caption length:[/] {len(caption)} chars")
                console.print(f"[bold yellow][MOCK CLIENT] Thumbnail:[/] {Path(thumbnail).name if thumbnail else 'None'}")
                class MockMedia:
                    id = "MOCK_MEDIA_12345"
                return MockMedia()
            
            def photo_upload_to_story(self, path, caption):
                console.print(f"[bold yellow][MOCK CLIENT] Uploading Story:[/] {Path(path).name}")
                console.print(f"[bold yellow][MOCK CLIENT] Story Caption:[/] {caption}")
                return True
        publisher._cl = MockClient()
        publisher.is_logged_in = True
        
    # Gather target files
    targets = []
    
    if args.file:
        video_path = Path(args.file).resolve()
        if not video_path.exists():
            console.print(f"[red]❌ File not found:[/] {video_path}")
            sys.exit(1)
        targets.append(video_path)
        
    elif args.mood:
        folder = organizer.get_mood_folder(args.mood)
        targets = list(folder.glob("*.mp4"))
        # Filter out temporary files and fixed version uploads
        targets = [t for t in targets if "_ig_ready" not in t.stem]
        if not targets:
            console.print(f"[yellow]No reels found in mood folder:[/] {folder.name}")
            sys.exit(0)
            
    elif args.all:
        for folder_name in set(organizer.list_reels_by_mood().keys()):
            folder = organizer.get_mood_folder(folder_name)
            folder_reels = list(folder.glob("*.mp4"))
            folder_reels = [t for t in folder_reels if "_ig_ready" not in t.stem]
            targets.extend(folder_reels)
        if not targets:
            console.print("[yellow]No reels found in any mood folder.[/yellow]")
            sys.exit(0)

    console.print(f"[bold]Found {len(targets)} reels to process.[/bold]\n")
    
    success_count = 0
    for idx, video_path in enumerate(targets, 1):
        console.print(f"[bold cyan]({idx}/{len(targets)}) Processing:[/] {video_path.parent.name}/{video_path.name}")
        
        # Check if already uploaded
        meta_path = video_path.with_suffix(".json")
        if meta_path.exists() and not args.dry_run:
            try:
                import json
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("instagram_media_id"):
                    console.print(f"  [yellow]Reel already posted with ID: {meta['instagram_media_id']}. Skipping.[/yellow]")
                    continue
            except Exception as e:
                console.print(f"  [dim]Could not check if posted: {e}[/dim]")
        
        try:
            media_id = publisher.publish_from_folder(video_path, post_story=args.story)
            if media_id:
                success_count += 1
            else:
                console.print("[red]❌ Upload failed.[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error during upload: {e}[/red]")
            
    console.print(f"\n[bold green]Finished![/] Successfully processed/uploaded {success_count} of {len(targets)} reels.")

if __name__ == "__main__":
    main()
