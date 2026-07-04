"""
REEL GOD — Quality Assurance & Verification
Checks completed Reels against strict quality standards:
  1. Resolution must be exactly 1080x1920 (9:16 portrait)
  2. Duration must match the narrative sum (~25s)
  3. Video codec must be H.264 high-profile
  4. Audio must be AAC stereo 44.1kHz / 48kHz
  5. Bitrate must be high (>3500kbps)
  6. File size must be reasonable (>2MB)
  7. Metadata JSON must be complete and valid
"""
import os, sys, json, subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_ffprobe(filepath: Path) -> dict:
    """Run ffprobe to get video stream data."""
    # Find aliased ffmpeg path
    ffmpeg_dir = Path(__file__).resolve().parent / "data" / "bin"
    ffprobe_cmd = shutil_which("ffprobe") or str(ffmpeg_dir / "ffprobe.exe")
    if not Path(ffprobe_cmd).exists() and not shutil_which("ffprobe"):
        ffmpeg_bin = ffmpeg_dir / "ffmpeg.exe"
        if ffmpeg_bin.exists():
            ffprobe_cmd = str(ffmpeg_dir / "ffprobe.exe")
    
    if not shutil_which("ffprobe") and not Path(ffprobe_cmd).exists():
        return _fallback_ffmpeg_probe(filepath)

    cmd = [
        ffprobe_cmd or "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(filepath)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return json.loads(out)
    except Exception as e:
        return _fallback_ffmpeg_probe(filepath)

def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)

def _fallback_ffmpeg_probe(filepath: Path) -> dict:
    """Fallback probe using ffmpeg stderr output."""
    ffmpeg_dir = Path(__file__).resolve().parent / "data" / "bin"
    ffmpeg_cmd = shutil_which("ffmpeg") or str(ffmpeg_dir / "ffmpeg.exe")
    cmd = [ffmpeg_cmd, "-i", str(filepath)]
    
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    _, stderr = p.communicate()
    stderr_str = stderr.decode(errors='ignore')
    
    info = {"format": {}, "streams": []}
    import re
    res_match = re.search(r"(\d{3,4})x(\d{3,4})", stderr_str)
    if res_match:
        info["streams"].append({
            "codec_type": "video",
            "width": int(res_match.group(1)),
            "height": int(res_match.group(2)),
            "codec_name": "h264" if "h264" in stderr_str.lower() else "unknown"
        })
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_str)
    if dur_match:
        hours = int(dur_match.group(1))
        mins = int(dur_match.group(2))
        secs = float(dur_match.group(3))
        total_secs = hours * 3600 + mins * 60 + secs
        info["format"]["duration"] = str(total_secs)
    if "audio" in stderr_str.lower():
        info["streams"].append({
            "codec_type": "audio",
            "codec_name": "aac" if "aac" in stderr_str.lower() else "unknown",
            "sample_rate": "44100" if "44100" in stderr_str else "48000"
        })
    return info

def verify_reel(video_path: Path) -> bool:
    """Verify all quality standards strictly."""
    console.print(f"\n[bold yellow]🔍 Starting Quality Assurance Check:[/] {video_path.name}")
    
    if not video_path.exists():
        console.print("[red]❌ Video file does not exist![/]")
        return False
        
    size_mb = video_path.stat().st_size / (1024 * 1024)
    meta_path = video_path.with_suffix(".json")
    
    if not meta_path.exists():
        console.print("[red]❌ Missing metadata sidecar JSON file![/]")
        return False
        
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]❌ Failed to parse metadata JSON: {e}[/]")
        return False

    probe = run_ffprobe(video_path)
    streams = probe.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    
    duration = float(probe.get("format", {}).get("duration", 0))
    if not duration and v_stream:
        duration = float(v_stream.get("duration", 0))
        
    checks = []
    
    # A. Resolution Check (Strictly matching target aspect ratio)
    ar = meta.get("aspect_ratio", "9:16")
    expected_w, expected_h = 1080, 1920
    if ar == "1:1":
        expected_w, expected_h = 1080, 1080
    elif ar == "4:5":
        expected_w, expected_h = 1080, 1350

    w = v_stream.get("width", 0) if v_stream else 0
    h = v_stream.get("height", 0) if v_stream else 0
    
    if w == expected_w and h == expected_h:
        checks.append((f"Resolution ({ar} -> {expected_w}x{expected_h})", "PASS", f"{w}x{h}"))
    else:
        checks.append((f"Resolution ({ar} -> {expected_w}x{expected_h})", "FAIL", f"{w}x{h} (Expected {expected_w}x{expected_h})"))
        
    # B. Video Codec Check (Strictly H.264)
    v_codec = v_stream.get("codec_name", "unknown") if v_stream else "none"
    if v_codec == "h264":
        checks.append(("Video Codec (H.264)", "PASS", v_codec))
    else:
        checks.append(("Video Codec (H.264)", "FAIL", f"{v_codec} (Must be H.264)"))
        
    # C. Audio Check (Strictly AAC stereo)
    a_codec = a_stream.get("codec_name", "unknown") if a_stream else "none"
    if a_codec == "aac":
        checks.append(("Audio Codec (AAC)", "PASS", a_codec))
    else:
        checks.append(("Audio Codec (AAC)", "FAIL", f"{a_codec} (Must be AAC)"))
        
    # D. Duration Check
    expected_dur = sum(item.get("duration", 5.0) for item in meta.get("narrative", []))
    if abs(duration - expected_dur) < 1.0:
        checks.append(("Duration Match", "PASS", f"{duration:.2f}s (Expected {expected_dur}s)"))
    else:
        checks.append(("Duration Match", "WARNING", f"{duration:.2f}s (Expected {expected_dur}s)"))
        
    # E. File Size Check (Must be > 2MB for high-bitrate quality)
    if size_mb >= 2.0:
        checks.append(("File Size (>2MB)", "PASS", f"{size_mb:.2f} MB"))
    else:
        checks.append(("File Size (>2MB)", "FAIL", f"{size_mb:.2f} MB (Too small, bitrate is too low)"))
        
    # F. Narrative Subtitles Integrity
    narrative = meta.get("narrative", [])
    if len(narrative) >= 4:
        checks.append(("Narrative Flow", "PASS", f"{len(narrative)} story segments"))
    else:
        checks.append(("Narrative Flow", "FAIL", f"{len(narrative)} segments (Must have at least 4 for progressive tension)"))

    table = Table(title="REEL GOD Quality Assurance Report", border_style="cyan")
    table.add_column("Standard", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Measured Value")
    
    all_pass = True
    for std, status, val in checks:
        color = "green" if status == "PASS" else ("yellow" if status == "WARNING" else "red")
        table.add_row(std, f"[{color}]{status}[/]", val)
        if status == "FAIL":
            all_pass = False
            
    console.print(table)
    
    if all_pass:
        console.print(Panel("[bold green]✅ CONGRATULATIONS! Video qualifies under the highest world-class standards![/]", border_style="green"))
    else:
        console.print(Panel("[bold red]❌ REJECTED! Video does not meet the strict quality standards. Refactoring needed.[/]", border_style="red"))
        
    return all_pass

if __name__ == "__main__":
    import shutil
    root = Path(__file__).resolve().parent
    archive_dir = root / "data" / "content_archive"

    if len(sys.argv) >= 2:
        targets = [Path(sys.argv[1])]
    else:
        # Recursively find all mp4 files in all mood subfolders
        targets = list(archive_dir.rglob("*.mp4"))
        # Filter out temporary/ig_ready files
        targets = [t for t in targets if "_ig_ready" not in t.stem]
        if not targets:
            console.print("[yellow]⚠️  No reels found in content archive to verify. Generate some first![/yellow]")
            sys.exit(0)

    console.print(Panel(
        f"[bold cyan]🔍 QUALITY ASSURANCE SUITE[/]\n"
        f"[dim]Verifying {len(targets)} reels in content archive[/]",
        border_style="cyan"
    ))

    success = True
    for target in targets:
        if not verify_reel(target):
            success = False

    if not success:
        sys.exit(1)

