"""
REEL GOD — Audio Mixer
======================
Combines background music with generated video clips.
Trims/loops the audio to match the video duration, applies fade effects,
and exports the final high-definition MP4 with AAC audio encoding.
"""

import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.fx.all import audio_fadein, audio_fadeout, audio_loop

import config

console = Console()


class AudioMixer:
    """
    Mixes audio tracks with compiled video clips.
    
    Responsibilities:
    - Overlay audio track on top of video clip
    - Loop audio if it is shorter than video duration
    - Trim audio if it is longer than video duration
    - Apply fade-in (1.5s) and fade-out (2.0s) to audio
    - Save and export the final Reel to data/content_archive
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.CONTENT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        console.print("[dim]Audio Mixer initialized[/dim]")
        
    def mix_audio(self, video_path: Path, audio_path: Path, output_filename: str) -> Path:
        """
        Merge audio and video files. Trim or loop audio as needed.
        
        Args:
            video_path: Path to the compiled silent MP4 video file
            audio_path: Path to the MP3 audio file
            output_filename: Output filename (e.g. final_reel_01.mp4)
            
        Returns:
            Path to the final audio-mixed MP4 file.
        """
        output_path = self.output_dir / output_filename
        console.print(f"[cyan]Mixing audio {audio_path.name} with video {video_path.name}...[/cyan]")
        
        video_clip = None
        audio_clip = None
        final_video = None
        
        try:
            # 1. Load clips
            video_clip = VideoFileClip(str(video_path))
            audio_clip = AudioFileClip(str(audio_path))
            
            video_duration = video_clip.duration
            audio_duration = audio_clip.duration
            
            # 2. Match durations (trim or loop)
            if audio_duration < video_duration:
                console.print(f"[dim]  Audio ({audio_duration:.1f}s) is shorter than video ({video_duration:.1f}s) → looping[/dim]")
                mixed_audio = audio_clip.fx(audio_loop, duration=video_duration)
            else:
                console.print(f"[dim]  Audio ({audio_duration:.1f}s) is longer than video ({video_duration:.1f}s) → trimming[/dim]")
                mixed_audio = audio_clip.subclip(0, video_duration)
                
            # 3. Apply fade in/out effects
            mixed_audio = mixed_audio.fx(audio_fadein, 1.5).fx(audio_fadeout, 2.0)
            
            # 4. Set audio of the video clip
            final_video = video_clip.set_audio(mixed_audio)
            
            # 5. Write final output file
            console.print(f"[yellow]Rendering final video with audio → {output_path}[/yellow]")
            final_video.write_videofile(
                str(output_path),
                fps=config.VIDEO_FPS,
                codec=config.VIDEO_CODEC,
                bitrate=config.VIDEO_BITRATE,
                audio_codec="aac",
                logger="bar"
            )
            
            console.log(f"[bold green]✔ Final Reel compiled successfully:[/] {output_path}")
            return output_path
            
        except Exception as e:
            console.print(f"[red]Error during audio mixing: {e}[/red]")
            raise
            
        finally:
            # Explicitly close all clips to release file locks on Windows
            if final_video:
                final_video.close()
            if video_clip:
                video_clip.close()
            if audio_clip:
                audio_clip.close()
