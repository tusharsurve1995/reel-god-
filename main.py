"""
REEL GOD — Main Entry Point
=============================
The command center. Start here.

Usage:
  python main.py                  → Start the agent (full 24/7 mode)
  python main.py --status         → Check agent status
  python main.py --ideas          → Generate content ideas now
  python main.py --briefing       → Run morning briefing
  python main.py --plan           → Generate weekly content calendar
  python main.py --chat           → Chat with REEL GOD directly
  python main.py --system-check   → Check system requirements
  python main.py --install-service → Register as Windows startup service
"""

import sys
import time
import argparse
import schedule
import threading
from datetime import datetime
from pathlib import Path
import config

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs): print(*args)
    console = Console()
    class Panel:
        def __init__(self, *a, **kw): pass


def print_banner():
    banner = """
[bold cyan]
██████╗ ███████╗███████╗██╗      ██████╗  ██████╗ ██████╗
██╔══██╗██╔════╝██╔════╝██║     ██╔════╝ ██╔═══██╗██╔══██╗
██████╔╝█████╗  █████╗  ██║     ██║  ███╗██║   ██║██║  ██║
██╔══██╗██╔══╝  ██╔══╝  ██║     ██║   ██║██║   ██║██║  ██║
██║  ██║███████╗███████╗███████╗╚██████╔╝╚██████╔╝██████╔╝
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝
[/bold cyan]
[dim]  Autonomous Anime Instagram Agent · Beast Level · Loyal to the Commander[/dim]
"""
    console.print(banner)


def check_setup() -> bool:
    """Verify that first-time setup has been completed."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        console.print(
            "\n[bold red]⚠️  First-time setup not complete![/bold red]\n"
            "[yellow]Run:[/yellow] [bold]python setup_first_time.py[/bold]\n"
        )
        return False
    
    # Check for Gemini key in .env
    with open(env_file) as f:
        content = f.read()
    
    if "GEMINI_API_KEY" not in content or "PASTE_YOUR_KEY_HERE" in content:
        console.print(
            "\n[bold red]⚠️  Gemini API Key not configured![/bold red]\n"
            "[yellow]Run:[/yellow] [bold]python setup_first_time.py[/bold]\n"
        )
        return False
    
    return True


def check_scheduled_posts(brain):
    """
    Check the content_schedule table for any slots due for posting.
    If due, compile and upload the matching Reel.
    """
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    
    console.print(f"\n[cyan]🔍 Checking content schedule for {today_str} {time_str}...[/cyan]")
    slots = brain.memory.get_pending_scheduled_slots(today_str, time_str)
    
    if not slots:
        console.print("[dim]No pending scheduled slots due at this time.[/dim]")
        return
        
    for slot in slots:
        slot_id = slot["id"]
        style = slot["style"]
        theme = slot["theme"]
        console.print(f"[bold cyan]🚀 Scheduled posting slot triggered! Style: {style} | Theme: {theme}[/bold cyan]")
        
        # 1. Locate approved idea for this style
        idea = None
        with brain.memory._connect() as conn:
            row = conn.execute(
                "SELECT * FROM content_ideas WHERE status = 'approved' AND style = ? ORDER BY approved_at ASC LIMIT 1",
                (style,)
            ).fetchone()
            if row:
                idea = dict(row)
            else:
                # Fallback to any approved idea
                row = conn.execute(
                    "SELECT * FROM content_ideas WHERE status = 'approved' ORDER BY approved_at ASC LIMIT 1"
                ).fetchone()
                if row:
                    idea = dict(row)
                    
        # 2. Autonomous fallback: generate and auto-approve a matching idea
        if not idea:
            console.print("[yellow]⚠️ No approved ideas found in database. Auto-generating fresh content idea...[/yellow]")
            ideas = brain.generate_content_ideas(count=1, style=style)
            if ideas:
                idea = ideas[0]
                brain.memory.approve_idea(idea["id"])
                console.print(f"[green]✓ Auto-generated and approved Idea #{idea['id']}: '{idea['title']}'[/green]")
            else:
                console.print("[red]❌ Failed to auto-generate idea. Skipping slot.[/red]")
                continue

        # 3. Compile the Reel video
        try:
            video_path_str = brain.generate_video_content(idea["id"])
            video_path = Path(video_path_str)
            
            # Find the created post record
            post = None
            with brain.memory._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM posts WHERE idea_id = ? ORDER BY id DESC LIMIT 1",
                    (idea["id"],)
                ).fetchone()
                if row:
                    post = dict(row)
                    
            if not post:
                raise RuntimeError(f"Post record not found in database for Idea #{idea['id']}.")
                
            post_id = post["id"]
            
            # 4. Check Instagram Connection
            import os
            ig_user = os.environ.get("INSTAGRAM_USERNAME") or getattr(config, "INSTAGRAM_USERNAME", None)
            ig_pass = os.environ.get("INSTAGRAM_PASSWORD") or getattr(config, "INSTAGRAM_PASSWORD", None)
            
            if ig_user and ig_pass:
                console.print(f"[cyan]Uploading Reel #{post_id} to Instagram account @{ig_user}...[/cyan]")
                from instagram.publisher import InstagramPublisher
                publisher = InstagramPublisher()
                media_id = publisher.publish_reel(video_path, post["caption"])
                
                if media_id:
                    with brain.memory._connect() as conn:
                        conn.execute(
                            "UPDATE posts SET instagram_id = ?, posted_at = datetime('now') WHERE id = ?",
                            (media_id, post_id)
                        )
                    brain.memory.mark_slot_published(slot_id, post_id)
                    console.print(f"[bold green]✓ Reel #{post_id} successfully posted to Instagram! Media ID: {media_id}[/bold green]")
                else:
                    raise RuntimeError("Reel upload returned empty media ID.")
            else:
                # Fallback: Mark slot published in dry-run mode
                brain.memory.mark_slot_published(slot_id, post_id)
                console.print("[yellow]⚠️ Instagram credentials not connected. Dry-run mode completed: compiled reel saved.[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed scheduled posting loop: {e}[/bold red]")
            with brain.memory._connect() as conn:
                conn.execute("UPDATE content_schedule SET status = 'failed' WHERE id = ?", (slot_id,))


def harvest_instagram_analytics(brain):
    """
    Query Instagram private API to update views, likes, and comments for published reels.
    """
    console.print("\n[cyan]📊 Running daily Instagram performance harvesting...[/cyan]")
    posts = brain.memory.get_all_published_posts_with_ig_ids()
    
    if not posts:
        console.print("[dim]No published posts found to harvest metrics for.[/dim]")
        return
        
    import os
    ig_user = os.environ.get("INSTAGRAM_USERNAME") or getattr(config, "INSTAGRAM_USERNAME", None)
    ig_pass = os.environ.get("INSTAGRAM_PASSWORD") or getattr(config, "INSTAGRAM_PASSWORD", None)
    
    if not ig_user or not ig_pass:
        console.print("[yellow]⚠️ Instagram credentials not linked. Skipping metrics harvest.[/yellow]")
        return
        
    try:
        from instagram.publisher import InstagramPublisher
        publisher = InstagramPublisher()
        if not publisher.login():
            console.print("[red]❌ Failed to authenticate with Instagram during metrics harvest.[/red]")
            return
            
        updated_count = 0
        for post in posts:
            media_id = post["instagram_id"]
            post_id = post["id"]
            
            console.print(f"[dim]Retrieving analytics for media ID #{media_id}...[/dim]")
            metrics = publisher.get_reel_analytics(media_id)
            if metrics:
                brain.memory.update_post_analytics(post_id, metrics)
                updated_count += 1
                
        console.print(f"[bold green]✓ Performance harvest completed. Updated {updated_count} post records in database.[/bold green]")
        
        # Log self-analysis thought
        analysis = brain.self_analyze()
        brain.memory.save_thought(
            f"Daily Performance Analysis complete: {analysis[:150]}...",
            "self_analysis"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Analytics harvest failed: {e}[/bold red]")


def start_agent():
    """Start REEL GOD in full 24/7 autonomous mode."""
    from brain.core import ReelGodBrain
    import config

    brain = ReelGodBrain()
    
    console.print("\n[bold green]🚀 REEL GOD is now running in 24/7 mode[/bold green]")
    console.print("[dim]Press Ctrl+C to stop | Dashboard: http://localhost:5000[/dim]\n")

    # ── Schedule daily tasks ──────────────────────────────────────────────

    def run_morning_briefing():
        console.print(f"\n[yellow]⏰ Scheduled morning briefing at {datetime.now().strftime('%H:%M')}[/yellow]")
        brain.morning_briefing()

    def run_idea_generation():
        console.print(f"\n[magenta]💡 Scheduled idea generation at {datetime.now().strftime('%H:%M')}[/magenta]")
        ideas = brain.generate_content_ideas(count=3)
        if ideas:
            console.print(
                f"[green]Generated {len(ideas)} ideas. "
                f"Check dashboard for approval: http://localhost:5000[/green]"
            )

    def run_self_analysis():
        console.print(f"\n[blue]🔍 Weekly self-analysis...[/blue]")
        analysis = brain.self_analyze()
        console.print(f"[dim]{analysis[:200]}...[/dim]")

    # Schedule using config times
    schedule.every().day.at(
        f"{config.DAILY_PLANNING_HOUR:02d}:00"
    ).do(run_morning_briefing)

    # Generate ideas 3x per day
    schedule.every().day.at("09:30").do(run_idea_generation)
    schedule.every().day.at("14:00").do(run_idea_generation)
    schedule.every().day.at("20:00").do(run_idea_generation)

    # Weekly self-analysis every Sunday
    schedule.every().sunday.at("23:00").do(run_self_analysis)

    # ── Autonomous Loop Schedules ─────────────────────────────────────────
    schedule.every(5).minutes.do(check_scheduled_posts, brain)
    schedule.every().day.at("02:00").do(harvest_instagram_analytics, brain)

    # ── Start dashboard in background ────────────────────────────────────
    try:
        from dashboard.app import start_dashboard
        dashboard_thread = threading.Thread(
            target=start_dashboard,
            daemon=True
        )
        dashboard_thread.start()
        console.print("[dim]Dashboard started at http://localhost:5000[/dim]")
    except ImportError:
        console.print("[dim]Dashboard not yet built (Phase 6 — coming soon)[/dim]")

    # ── Run immediately on first start ───────────────────────────────────
    brain.morning_briefing()
    brain.generate_content_ideas(count=3)
    check_scheduled_posts(brain)

    # ── Main loop ─────────────────────────────────────────────────────────
    console.print("\n[dim]Agent is running. Scheduled tasks active.[/dim]")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        console.print("\n\n[yellow]REEL GOD shutting down gracefully...[/yellow]")
        brain.memory.save_thought("Agent shutdown by commander.", "system")


def cmd_status():
    """Show current agent status."""
    from brain.core import ReelGodBrain
    brain = ReelGodBrain()
    brain.print_status()


def cmd_ideas(style: str = None, count: int = 3):
    """Generate content ideas immediately."""
    from brain.core import ReelGodBrain
    brain = ReelGodBrain()
    ideas = brain.generate_content_ideas(count=count, style=style)
    
    if not ideas:
        console.print("[red]No ideas generated. Check Gemini API key.[/red]")
        return

    console.print(f"\n[bold green]Generated {len(ideas)} ideas:[/bold green]\n")
    for i, idea in enumerate(ideas, 1):
        score = idea.get("quality_score", 7)
        color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
        console.print(
            f"  [bold]{i}. {idea.get('title', 'Untitled')}[/bold]\n"
            f"     Style: {idea.get('style', 'N/A')} · Mood: {idea.get('mood', 'N/A')}\n"
            f"     Quality: [{color}]{score}/10[/{color}]\n"
            f"     [dim]{idea.get('hook', '')[:100]}[/dim]\n"
            f"     ID #{idea.get('id')} — approve at http://localhost:5000/approve/{idea.get('id')}\n"
        )


def cmd_briefing():
    """Run the morning briefing now."""
    from brain.core import ReelGodBrain
    brain = ReelGodBrain()
    brain.morning_briefing()


def cmd_plan():
    """Generate weekly content calendar."""
    from brain.core import ReelGodBrain
    import json
    brain = ReelGodBrain()
    console.print("\n[bold]📅 Generating weekly content calendar...[/bold]")
    calendar = brain.planner.generate_weekly_calendar()
    
    if "error" in calendar:
        console.print(f"[red]Error: {calendar['error']}[/red]")
        return
    
    console.print(f"\n[bold cyan]Week Strategy:[/bold cyan] {calendar.get('week_strategy', '')}\n")
    for day in calendar.get("days", []):
        console.print(
            f"  [bold]{day.get('day')}[/bold] — {day.get('style')} — {day.get('theme')}\n"
            f"  Post time: {day.get('post_time')} | {day.get('reasoning', '')[:80]}\n"
        )


def cmd_chat():
    """Start an interactive chat session with REEL GOD."""
    from brain.core import ReelGodBrain
    brain = ReelGodBrain()
    
    console.print(
        "\n[bold cyan]💬 REEL GOD Chat Mode[/bold cyan]\n"
        "[dim]Type your message and press Enter. Type 'exit' to quit.[/dim]\n"
    )

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                console.print("[cyan]REEL GOD: Signing off. Stay legendary. 🔥[/cyan]")
                break

            response = brain.respond_to_commander(user_input)
            console.print(f"\n[bold cyan]REEL GOD:[/bold cyan] {response}\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Chat ended.[/yellow]")
            break


def cmd_system_check():
    """Run system compatibility check."""
    from utils.gpu_check import print_system_report
    print_system_report()


def cmd_generate(idea_id: int):
    """Compile video content for a specific idea ID."""
    from brain.core import ReelGodBrain
    brain = ReelGodBrain()
    try:
        final_path = brain.generate_video_content(idea_id)
        console.print(f"[bold green]✓ Compilation completed successfully! Video saved at: {final_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Compilation failed: {e}[/bold red]")


def install_windows_service():
    """Register REEL GOD as a Windows startup task."""
    import subprocess
    
    script_path = Path(__file__).resolve()
    python_path = sys.executable
    task_name = "ReelGodAgent"
    
    cmd = [
        "schtasks", "/create", "/tn", task_name,
        "/tr", f'"{python_path}" "{script_path}"',
        "/sc", "ONLOGON",
        "/ru", "SYSTEM",
        "/f"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        console.print(f"[green]✅ Windows service registered as '{task_name}'[/green]")
        console.print("[dim]REEL GOD will start automatically when Windows boots[/dim]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to register service: {e}[/red]")
        console.print("[yellow]Try running this script as Administrator[/yellow]")


# ─────────────────────────────────────────────────────────────────────────────
#  ARGUMENT PARSER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="REEL GOD — Autonomous Anime Instagram Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--status", action="store_true", help="Show agent status")
    parser.add_argument("--ideas", action="store_true", help="Generate content ideas now")
    parser.add_argument("--style", type=str, help="Content style for --ideas")
    parser.add_argument("--count", type=int, default=3, help="Number of ideas to generate")
    parser.add_argument("--briefing", action="store_true", help="Run morning briefing")
    parser.add_argument("--plan", action="store_true", help="Generate weekly calendar")
    parser.add_argument("--chat", action="store_true", help="Chat with REEL GOD")
    parser.add_argument("--system-check", action="store_true", help="Check system requirements")
    parser.add_argument("--install-service", action="store_true", help="Register as Windows service")
    parser.add_argument("--generate", type=int, help="Compile video content for approved idea ID")

    args = parser.parse_args()

    print_banner()

    # System check doesn't need API key
    if args.system_check:
        cmd_system_check()
        return

    # Install service
    if args.install_service:
        install_windows_service()
        return

    # All other commands require setup
    if not check_setup():
        return

    if args.status:
        cmd_status()
    elif args.ideas:
        cmd_ideas(style=args.style, count=args.count)
    elif args.briefing:
        cmd_briefing()
    elif args.plan:
        cmd_plan()
    elif args.chat:
        cmd_chat()
    elif args.generate:
        cmd_generate(args.generate)
    else:
        # Default: full 24/7 mode
        start_agent()


if __name__ == "__main__":
    main()
