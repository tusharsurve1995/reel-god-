"""
REEL GOD — GPU & System Checker
=================================
Detects hardware capabilities and recommends the best settings.
"""

import subprocess
import platform
import sys
from pathlib import Path


def check_nvidia_gpu() -> dict:
    """
    Detect NVIDIA GPU and return its details.
    Returns dict with found, name, vram_gb, driver_version.
    """
    result = {
        "found": False,
        "name": None,
        "vram_gb": 0,
        "driver_version": None,
        "cuda_available": False,
        "recommended_model": None,
        "recommended_mode": "cpu"
    }

    try:
        # Run nvidia-smi to get GPU info
        output = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            timeout=5
        ).decode("utf-8").strip()

        if output:
            lines = output.split("\n")
            gpu_info = lines[0].split(", ")
            
            if len(gpu_info) >= 2:
                result["found"] = True
                result["name"] = gpu_info[0].strip()
                vram_mb = float(gpu_info[1].strip())
                result["vram_gb"] = round(vram_mb / 1024, 1)
                if len(gpu_info) >= 3:
                    result["driver_version"] = gpu_info[2].strip()
                result["recommended_mode"] = "gpu"

                # Recommend SD model based on VRAM
                vram = result["vram_gb"]
                if vram >= 8:
                    result["recommended_model"] = "animagine-xl-4.0"
                    result["model_note"] = "Excellent! Can run SDXL models for top anime quality."
                elif vram >= 6:
                    result["recommended_model"] = "animagine-xl-4.0"
                    result["model_note"] = "Good! Can run SDXL with optimized settings."
                elif vram >= 4:
                    result["recommended_model"] = "anything-v5"
                    result["model_note"] = "SD 1.5 models recommended (Anything V5, MeinaMix)."
                else:
                    result["recommended_model"] = "anything-v5"
                    result["model_note"] = "Low VRAM. Using lightweight SD 1.5 models."

    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        pass

    # Check CUDA via Python if GPU found
    if result["found"]:
        try:
            import torch
            result["cuda_available"] = torch.cuda.is_available()
        except ImportError:
            result["cuda_available"] = None  # torch not installed yet

    # CPU fallback
    if not result["found"]:
        result["recommended_model"] = "anything-v5"
        result["model_note"] = (
            "No NVIDIA GPU detected. Will use CPU mode for image generation. "
            "This is slower but fully functional."
        )
        result["recommended_mode"] = "cpu"

    return result


def check_python_version() -> dict:
    """Check Python version requirements."""
    version = sys.version_info
    required = (3, 10)
    return {
        "version": f"{version.major}.{version.minor}.{version.micro}",
        "ok": version >= required,
        "required": f"{required[0]}.{required[1]}+"
    }


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.check_output(
            ["ffmpeg", "-version"],
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_comfyui() -> dict:
    """Check if ComfyUI server is running."""
    try:
        import requests
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {
                "running": True,
                "vram_total": data.get("system", {}).get("vram_total", 0),
                "vram_free": data.get("system", {}).get("vram_free", 0)
            }
    except Exception:
        pass
    return {"running": False}


def full_system_check() -> dict:
    """Run all system checks and return a complete status report."""
    report = {
        "python": check_python_version(),
        "gpu": check_nvidia_gpu(),
        "ffmpeg": check_ffmpeg(),
        "comfyui": check_comfyui(),
        "platform": platform.system(),
        "machine": platform.machine()
    }
    return report


def print_system_report():
    """Print a human-readable system check report."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False

    report = full_system_check()

    if use_rich:
        table = Table(title="🖥️  System Check", show_header=True)
        table.add_column("Component", style="bold")
        table.add_column("Status")
        table.add_column("Details")

        # Python
        py = report["python"]
        py_status = "✅ OK" if py["ok"] else "❌ Too old"
        table.add_row("Python", py_status, f"v{py['version']} (need {py['required']})")

        # GPU
        gpu = report["gpu"]
        if gpu["found"]:
            table.add_row(
                "GPU",
                "✅ Found",
                f"{gpu['name']} · {gpu['vram_gb']} GB VRAM"
            )
            table.add_row(
                "SD Model",
                "📌 Recommended",
                f"{gpu['recommended_model']} — {gpu.get('model_note', '')}"
            )
        else:
            table.add_row("GPU", "⚠️  CPU mode", gpu.get("model_note", "No GPU found"))

        # FFmpeg
        table.add_row(
            "FFmpeg",
            "✅ Installed" if report["ffmpeg"] else "❌ Not found",
            "Required for video assembly" if not report["ffmpeg"] else "Ready"
        )

        # ComfyUI
        comfy = report["comfyui"]
        if comfy["running"]:
            table.add_row("ComfyUI", "✅ Running", "Server at localhost:8188")
        else:
            table.add_row("ComfyUI", "⚠️  Offline", "Start ComfyUI before generating images")

        console.print(table)

        # Recommendations
        notes = []
        if not py["ok"]:
            notes.append("[red]• Upgrade Python to 3.10 or newer[/red]")
        if not report["ffmpeg"]:
            notes.append("[yellow]• Install FFmpeg: https://ffmpeg.org/download.html[/yellow]")
        if not comfy["running"]:
            notes.append("[yellow]• Start ComfyUI: python main.py --disable-auto-launch[/yellow]")
        if gpu["recommended_mode"] == "cpu":
            notes.append("[dim]• Image generation will be slower without a GPU (still works)[/dim]")

        if notes:
            console.print(Panel("\n".join(notes), title="📋 Notes", border_style="yellow"))
    else:
        print("\n=== System Check ===")
        py = report["python"]
        print(f"Python: {py['version']} ({'OK' if py['ok'] else 'UPGRADE NEEDED'})")
        gpu = report["gpu"]
        print(f"GPU: {gpu['name'] if gpu['found'] else 'Not found'}")
        print(f"FFmpeg: {'Found' if report['ffmpeg'] else 'Not found'}")
        print(f"ComfyUI: {'Running' if report['comfyui']['running'] else 'Offline'}")

    return report


if __name__ == "__main__":
    print_system_report()
