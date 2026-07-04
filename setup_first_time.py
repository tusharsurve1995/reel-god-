"""
REEL GOD — First Time Setup
==============================
Run this ONCE before starting the agent.
Walks you through getting your Gemini API key and configuring everything.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

# ── Minimal rich import for nice output ──────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    console = Console()
    def panel(msg, title="", style="blue"):
        console.print(Panel(msg, title=title, border_style=style))
    def ask(prompt, default=""):
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]", default=default)
    def confirm(prompt):
        return Confirm.ask(f"[bold yellow]{prompt}[/bold yellow]")
    def info(msg):  console.print(f"[dim]{msg}[/dim]")
    def ok(msg):    console.print(f"[green]✅ {msg}[/green]")
    def warn(msg):  console.print(f"[yellow]⚠️  {msg}[/yellow]")
    def err(msg):   console.print(f"[red]❌ {msg}[/red]")
    def bold(msg):  console.print(f"[bold]{msg}[/bold]")
except ImportError:
    def panel(msg, title="", style=""):  print(f"\n{'='*50}\n{title}\n{msg}\n{'='*50}")
    def ask(prompt, default=""):         return input(f"{prompt}: ") or default
    def confirm(prompt):                 return input(f"{prompt} (y/n): ").lower() == "y"
    def info(msg):   print(f"  {msg}")
    def ok(msg):     print(f"✅ {msg}")
    def warn(msg):   print(f"⚠️  {msg}")
    def err(msg):    print(f"❌ {msg}")
    def bold(msg):   print(f"\n>>> {msg}")


ENV_FILE = Path(__file__).parent / ".env"


def write_env(key: str, value: str):
    """Write or update a key in the .env file."""
    env_lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            env_lines = f.readlines()

    updated = False
    new_lines = []
    for line in env_lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)


def step_gemini():
    """Guide user through getting a free Gemini API key."""
    panel(
        "REEL GOD's brain runs on [bold]Gemini 2.5 Flash[/bold] — Google's best free AI model.\n\n"
        "You need a FREE API key from Google AI Studio.\n"
        "It takes about [bold]2 minutes[/bold] and doesn't require a credit card.",
        title="🔑 Step 1: Gemini API Key",
        style="cyan"
    )

    bold("Here's how to get your key:")
    info("1. We'll open Google AI Studio in your browser")
    info("2. Sign in with your Google account")
    info("3. Click 'Get API Key' → 'Create API Key'")
    info("4. Copy the key and paste it here")
    info("")

    if confirm("Open Google AI Studio in your browser now?"):
        webbrowser.open("https://aistudio.google.com/apikey")
        info("Browser opened! Get your key, then come back here.")
        input("\n  Press ENTER when you have your key ready...")

    api_key = ask("Paste your Gemini API key here", "")
    
    if not api_key or len(api_key) < 20:
        err("That doesn't look like a valid key. Please try again.")
        return step_gemini()

    # Test the key
    info("Testing your API key...")
    try:
        from google import genai as gai
        client = gai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say exactly: REEL GOD ONLINE"
        )
        if response.text:
            ok(f"API key works! Response: {response.text.strip()}")
            write_env("GEMINI_API_KEY", api_key)
            return True
    except Exception as e:
        err(f"Key test failed: {e}")
        if confirm("Try entering the key again?"):
            return step_gemini()
        return False

    return True


def step_system_check():
    """Run system compatibility check."""
    panel(
        "Checking your system for required components...",
        title="🖥️  Step 2: System Check",
        style="blue"
    )
    
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.gpu_check import print_system_report
    report = print_system_report()

    # Python check
    if not report["python"]["ok"]:
        err(f"Python {report['python']['version']} is too old. Please install Python 3.10+")
        info("Download from: https://www.python.org/downloads/")
        return False

    # GPU info
    gpu = report["gpu"]
    if gpu["found"]:
        ok(f"GPU detected: {gpu['name']} with {gpu['vram_gb']} GB VRAM")
        ok(f"Recommended model: {gpu['recommended_model']}")
        # Update config with recommended model
        write_env("SD_MODEL", gpu["recommended_model"])
    else:
        warn("No NVIDIA GPU found — using CPU mode")
        warn("Image generation will be slower but everything still works!")

    # FFmpeg check
    if not report["ffmpeg"]:
        warn("FFmpeg not found. You'll need it for video assembly.")
        info("Install from: https://www.gyan.dev/ffmpeg/builds/ (get the 'full' build)")
        info("After installing, add FFmpeg to your system PATH")
        if not confirm("Continue setup without FFmpeg (you can install it later)?"):
            return False
    else:
        ok("FFmpeg is installed")

    return True


def step_instagram():
    """Guide through Instagram account setup."""
    panel(
        "Instagram posting requires a [bold]Business Account[/bold] and Meta API approval.\n\n"
        "Your current account is Personal — that's totally fine!\n"
        "REEL GOD will generate and prepare all content now.\n"
        "We'll set up Instagram posting when you're ready to switch accounts.",
        title="📱 Step 3: Instagram Setup",
        style="magenta"
    )

    info("For now, REEL GOD will:")
    info("• Generate content and save it to your computer")
    info("• Show you everything in the approval dashboard")
    info("• Be ready to post the moment your account is upgraded")
    info("")
    info("When you're ready to switch to a Business account:")
    info("→ Go to Instagram → Settings → Account → Switch to Professional Account → Business")
    info("→ Then come back here and run: python setup_first_time.py --instagram")

    ok("Instagram setup noted — skipping for now (can set up later)")
    return True


def step_instagram_account():
    """Set Instagram username for account identification."""
    panel(
        "What's your Instagram @username?",
        title="📱 Instagram Username",
        style="magenta"
    )
    username = ask("Instagram username (without @)")
    if username:
        username = username.lstrip("@")
        write_env("INSTAGRAM_USERNAME", username)
        ok(f"Instagram username saved: @{username}")
    return True


def step_run_mode():
    """Configure how REEL GOD runs."""
    panel(
        "You want REEL GOD to run [bold]24/7 in the background[/bold].\n\n"
        "We'll set it up as a Windows scheduled task that starts automatically.",
        title="⏰ Step 4: Run Mode",
        style="green"
    )

    write_env("RUN_MODE", "24/7")
    write_env("AUTO_START", "true")
    
    ok("24/7 mode configured")
    info("After setup, run: python main.py --install-service")
    info("This will register REEL GOD to start with Windows")
    return True


def step_final():
    """Install dependencies and finalize."""
    panel(
        "Almost done! Installing Python dependencies...",
        title="📦 Step 5: Install Dependencies",
        style="cyan"
    )
    
    req_file = Path(__file__).parent / "requirements.txt"
    if req_file.exists():
        info("Running: pip install -r requirements.txt")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                check=True
            )
            ok("All dependencies installed!")
        except subprocess.CalledProcessError as e:
            err(f"Dependency installation failed: {e}")
            warn("Try running manually: pip install -r requirements.txt")
            return False
    return True


def main():
    """Run the full first-time setup wizard."""
    panel(
        "[bold cyan]Welcome to REEL GOD Setup[/bold cyan]\n\n"
        "This wizard will configure your autonomous anime Instagram agent.\n"
        "Takes about 5 minutes. Follow each step carefully.",
        title="🤖 REEL GOD — First Time Setup",
        style="cyan"
    )

    steps = [
        ("Gemini API Key", step_gemini),
        ("System Check", step_system_check),
        ("Instagram Setup", step_instagram),
        ("Instagram Username", step_instagram_account),
        ("Run Mode", step_run_mode),
        ("Install Dependencies", step_final),
    ]

    for i, (name, step_fn) in enumerate(steps):
        print()
        try:
            success = step_fn()
            if not success:
                err(f"Setup stopped at step: {name}")
                info("Fix the issue and run setup_first_time.py again")
                return
        except KeyboardInterrupt:
            warn("Setup cancelled. Run setup_first_time.py again to continue.")
            return
        except Exception as e:
            err(f"Unexpected error in {name}: {e}")
            if not confirm("Continue anyway?"):
                return

    print()
    panel(
        "🎉 [bold green]REEL GOD is configured and ready![/bold green]\n\n"
        "Next steps:\n"
        "  [bold]python main.py[/bold]          → Start REEL GOD\n"
        "  [bold]python main.py --status[/bold]  → Check agent status\n"
        "  [bold]python main.py --ideas[/bold]   → Generate content ideas now\n\n"
        "Your command dashboard will be at: [cyan]http://localhost:5000[/cyan]",
        title="✅ Setup Complete",
        style="green"
    )


if __name__ == "__main__":
    main()
