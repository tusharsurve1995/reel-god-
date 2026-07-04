"""
REEL GOD — Core Brain
======================
The central reasoning engine. This is REEL GOD's mind.
Powered by Gemini 2.5 Flash with persistent memory and planning capabilities.
"""

import json
from google import genai as gai
from google.genai import types as genai_types
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import config
from brain.memory import AgentMemory
from brain.personality import REEL_GOD_PERSONALITY
from brain.planner import ContentPlanner

console = Console()


class ReelGodBrain:
    """
    The central mind of REEL GOD.
    
    Responsibilities:
    - Reasoning and decision-making via Gemini 2.5 Flash
    - Persistent memory via SQLite
    - Content planning and strategy
    - Morning briefings and daily tasks
    - Commander communication
    """

    def __init__(self):
        self._validate_config()
        
        # Initialize core systems
        self.memory = AgentMemory(config.DB_PATH)
        self.planner = ContentPlanner(self)

        # Initialize Gemini client
        self._genai_client = gai.Client(api_key=config.GEMINI_API_KEY)
        self._booted_at = datetime.now()
        self.log_callback = None

        console.print(Panel(
            f"[bold cyan]{config.AGENT_NAME}[/bold cyan] v{config.AGENT_VERSION}\n"
            f"[dim]Brain initialized · Memory loaded · Gemini connected[/dim]\n"
            f"[dim]Model: {config.GEMINI_MODEL} · Started: {self._booted_at.strftime('%H:%M:%S')}[/dim]",
            title="🤖 REEL GOD ONLINE",
            border_style="cyan"
        ))

    def log(self, message: str, style: str = None):
        """Log a message to console and execute callback if registered."""
        formatted = f"[{style}]{message}[/{style}]" if style else message
        console.print(formatted)
        if self.log_callback:
            try:
                self.log_callback(formatted)
            except Exception:
                pass


    def _get_personality_with_rules(self) -> str:
        try:
            rules = self.memory.get_active_rules()
        except Exception:
            rules = []
            
        rules_text = ""
        if rules:
            rules_text = "\n\nCOMMANDER'S CUSTOM PREFERENCES & MEMORY RULES (YOU MUST STRICTLY ADHERE TO THESE):\n"
            for r in rules:
                rules_text += f"- {r['rule']}\n"
        return REEL_GOD_PERSONALITY + rules_text

    # ──────────────────────────────────────────────────────────────────────
    #  CORE THINKING
    # ──────────────────────────────────────────────────────────────────────

    def think(self, prompt: str, save_thought: bool = False) -> str:
        """
        Send a thought to the brain and get a response.
        This is the primary way all modules interact with Gemini.
        """
        try:
            response = self._genai_client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=self._get_personality_with_rules() + "\n\n" + prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.85,
                    top_p=0.95,
                    max_output_tokens=8192,
                )
            )
            result = response.text
            if save_thought:
                self.memory.save_thought(result, "general")
            return result
        except Exception as e:
            error_msg = f"Brain error: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            self.memory.save_thought(error_msg, "error")
            raise

    def think_fresh(self, prompt: str, system_override: str = None) -> str:
        """
        Think without conversation history — for isolated analysis tasks.
        """
        try:
            system = system_override or self._get_personality_with_rules()
            response = self._genai_client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=system + "\n\n" + prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            return f"[Error in fresh think: {e}]"

    # ──────────────────────────────────────────────────────────────────────
    #  DAILY ROUTINES
    # ──────────────────────────────────────────────────────────────────────

    def morning_briefing(self) -> dict:
        """
        The agent's daily morning session.
        Reviews performance, reads trends, plans the day.
        """
        console.print("\n[bold yellow]🌅 Morning Briefing Starting...[/bold yellow]")
        
        memory_snapshot = self.memory.get_full_memory_snapshot()
        
        prompt = f"""
Good morning. It's {datetime.now().strftime('%A, %B %d, %Y at %H:%M')}.
Time for your daily briefing as REEL GOD.

━━━ PERFORMANCE OVERVIEW ━━━
{json.dumps(memory_snapshot.get('performance', {}), indent=2)}

━━━ CONTENT STYLE BREAKDOWN ━━━
{json.dumps(memory_snapshot.get('style_stats', []), indent=2)}

━━━ ACTIVE TRENDS ━━━
{json.dumps([t.get('topic') for t in memory_snapshot.get('active_trends', [])[:10]], indent=2)}

━━━ RECENT COMMANDER FEEDBACK ━━━
{json.dumps([f.get('feedback') for f in memory_snapshot.get('commander_feedback', [])[-3:]], indent=2)}

Analyze this data and provide:
1. KEY INSIGHT: The most important thing you've learned from recent performance
2. TODAY'S FOCUS: What style/theme should today's content be, and why?
3. OPPORTUNITY: One trend or angle you could capitalize on right now
4. CONCERN: Anything the commander should know about the account's trajectory
5. TODAY'S PLAN: 2-3 content ideas you'll generate today

Be direct and specific. This is your daily report to your commander.
"""
        analysis = self.think(prompt)
        self.memory.save_thought(analysis, "morning_briefing")
        
        console.print(Panel(
            analysis,
            title="🌅 Morning Briefing",
            border_style="yellow"
        ))
        
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "snapshot": memory_snapshot
        }

    def generate_content_ideas(self, count: int = 3, style: str = None) -> list:
        """Generate a batch of content ideas. Returns list of idea dicts."""
        console.print(f"\n[bold magenta]💡 Generating {count} content ideas...[/bold magenta]")
        ideas = self.planner.generate_ideas(count=count, style=style)
        
        for idea in ideas:
            # Self-critique each idea
            critique = self.planner.self_critique_idea(idea)
            idea["quality_score"] = critique.get("overall_score", 7)
            idea["critique"] = critique
            
            score = idea["quality_score"]
            color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
            console.print(
                f"  [{color}]✓[/{color}] '{idea.get('title', 'Untitled')}' "
                f"[dim]Quality: {score}/10[/dim]"
            )
        
        return ideas

    def self_analyze(self) -> str:
        """
        Deep self-analysis: the agent evaluates its own performance
        and suggests how to improve.
        """
        snapshot = self.memory.get_full_memory_snapshot()
        
        prompt = f"""
Perform a deep self-analysis. You are REEL GOD evaluating your own performance.

Full memory snapshot:
{json.dumps(snapshot, indent=2)}

Answer honestly:
1. What's working well in your content strategy?
2. What's not working, and why?
3. What content gaps exist that you haven't explored?
4. What would you do differently starting today?
5. Rate your current performance 1-10 and justify it.
6. What is the single highest-impact change you could make?

This is for your eyes only — be brutally honest.
"""
        analysis = self.think_fresh(prompt)
        self.memory.save_thought(analysis, "self_analysis")
        return analysis

    def respond_to_commander(self, message: str) -> str:
        """
        Process a direct message from the commander and respond.
        The agent can receive commands, feedback, or questions.
        """
        # Inject context so the agent can respond intelligently
        context = f"""
The commander just said: "{message}"

Current time: {datetime.now().strftime('%A, %B %d at %H:%M')}

Your response should:
- Directly address what was asked/said
- If it's feedback, acknowledge it, store it mentally, and confirm what you'll do differently
- If it's a command, confirm you understand and what action you'll take
- If it's a question, answer it clearly and specifically
- Always stay in character as REEL GOD
"""
        response = self.think(context)
        
        # Store the interaction
        self.memory.save_feedback(
            feedback=message,
            sentiment="neutral"
        )
        self.memory.save_thought(
            f"Commander said: {message}\nMy response: {response[:200]}",
            "commander_interaction"
        )
        
        return response

    def explain_decision(self, decision_type: str, context: dict = None) -> str:
        """
        Ask the agent to explain a specific decision it made.
        """
        prompt = f"""
Explain your decision-making process for: {decision_type}

Context: {json.dumps(context or {}, indent=2)}

Explain in plain English:
1. WHY you made this choice
2. WHAT data or reasoning led you here
3. WHAT alternatives you considered
4. HOW you'll know if this was the right call
"""
        return self.think(prompt)

    # ──────────────────────────────────────────────────────────────────────
    #  STATUS
    # ──────────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return current agent status and key metrics."""
        performance = self.memory.get_performance_summary()
        pending = self.memory.get_pending_ideas()
        
        return {
            "agent": config.AGENT_NAME,
            "version": config.AGENT_VERSION,
            "model": config.GEMINI_MODEL,
            "uptime": str(datetime.now() - self._booted_at),
            "total_posts": performance.get("total_posts", 0),
            "avg_engagement": round(performance.get("avg_engagement", 0) or 0, 2),
            "best_style": performance.get("best_style", {}).get("style", "N/A"),
            "pending_approvals": len(pending),
            "timestamp": datetime.now().isoformat()
        }

    def print_status(self):
        """Print a formatted status report to the console."""
        status = self.get_status()
        
        status_text = Text()
        status_text.append(f"Agent: ", style="dim")
        status_text.append(f"{status['agent']} v{status['version']}\n", style="bold cyan")
        status_text.append(f"Model: ", style="dim")
        status_text.append(f"{status['model']}\n", style="green")
        status_text.append(f"Uptime: ", style="dim")
        status_text.append(f"{status['uptime']}\n")
        status_text.append(f"Total Posts: ", style="dim")
        status_text.append(f"{status['total_posts']}\n")
        status_text.append(f"Avg Engagement: ", style="dim")
        status_text.append(f"{status['avg_engagement']}%\n")
        status_text.append(f"Best Style: ", style="dim")
        status_text.append(f"{status['best_style']}\n")
        status_text.append(f"Pending Approvals: ", style="dim")
        status_text.append(f"{status['pending_approvals']}", style="yellow bold")

        console.print(Panel(status_text, title="📊 Agent Status", border_style="blue"))

    # ──────────────────────────────────────────────────────────────────────
    #  CONFIG VALIDATION
    # ──────────────────────────────────────────────────────────────────────

    def _validate_config(self):
        """Check config before starting. Raise if critical things are missing."""
        issues = config.validate()
        if issues:
            console.print("\n[bold red]⚠️  Configuration Issues:[/bold red]")
            for issue in issues:
                console.print(f"  {issue}")
            console.print(
                "\n[yellow]Run [bold]python setup_first_time.py[/bold] to complete setup.[/yellow]\n"
            )
            raise RuntimeError("Configuration incomplete. See above for details.")

    def generate_video_content(self, idea_id: int) -> str:
        """
        The complete generation loop for an approved idea:
        1. Retrieve idea from memory
        2. Prompt engineering: convert story scenes to SD prompts
        3. Image generation: use ComfyUI client (or fall back if offline)
        4. Video assembly: compile images into a silent slideshow video
        5. Visual effects: apply style-specific cinematic effects and transitions
        6. Music intelligence: discover, download and mix matching background music
        7. Save the final video path to the posts table
        
        Returns the path to the final mixed video file.
        """
        import os
        from pathlib import Path
        from generator.comfyui_client import ComfyUIClient
        from generator.prompt_engineer import PromptEngineer
        from generator.style_manager import StyleManager
        from generator.video_assembler import VideoAssembler
        from generator.effects import CinematicEffects
        from music.jamendo_client import JamendoClient
        from music.audio_mixer import AudioMixer

        console.print(f"\n[bold green]🎬 Compiling Video Assets for Idea ID #{idea_id}...[/bold green]")
        
        # 1. Retrieve idea
        idea = self.memory.get_idea(idea_id)
        if not idea:
            raise ValueError(f"Idea ID #{idea_id} not found in database.")
            
        title = idea.get("title", "Untitled")
        style = idea.get("style", "dark_cinematic")
        story = idea.get("story", "")
        script = idea.get("script", "") or story
        
        console.print(f"[dim]Title: {title} | Style: {style}[/dim]")

        # 2. Prompt engineering
        engineer = PromptEngineer(brain=self)
        # We need config.IMAGES_PER_VIDEO scenes for images per video
        scene_prompts = engineer.craft_scene_prompts(script, style=style, scene_count=config.IMAGES_PER_VIDEO)
        
        # 3. Image generation
        client = ComfyUIClient()
        style_mgr = StyleManager()
        
        image_paths = []
        workflow = style_mgr.get_workflow_template(style)
        
        # Check if ComfyUI is online. If not, generate colored fallback placeholders.
        comfy_online = client.check_connection()
        
        for i, scene in enumerate(scene_prompts, 1):
            pos_prompt = scene["positive"]
            neg_prompt = scene["negative"]
            seed = -1
            
            console.print(f"[cyan]Generating scene {i}/{config.IMAGES_PER_VIDEO}...[/cyan]")
            
            if comfy_online:
                # Modify workflow and generate via ComfyUI
                img_path = client.generate_image(
                    workflow=workflow,
                    prompt_text=pos_prompt,
                    negative_prompt=neg_prompt,
                    seed=seed,
                    output_dir=config.COMFYUI_OUTPUT_DIR
                )
                if img_path:
                    image_paths.append(str(img_path))
                    continue
                else:
                    console.print("[yellow]ComfyUI generation failed. Falling back to placeholder image.[/yellow]")
            
            # Placeholder generation fallback (if comfy offline or failed)
            from PIL import Image, ImageDraw
            # Generate a solid color background based on style
            color_map = {
                "dark_cinematic": (20, 20, 30),
                "emotional": (50, 40, 40),
                "epic_action": (60, 20, 20),
                "mystical": (30, 20, 50),
                "motivational": (50, 50, 20)
            }
            bg_color = color_map.get(style, (10, 10, 10))
            img = Image.new("RGB", (config.IMAGE_WIDTH, config.IMAGE_HEIGHT), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Simple grid lines or design to make it look like a placeholder
            draw.rectangle([50, 50, config.IMAGE_WIDTH - 50, config.IMAGE_HEIGHT - 50], outline=(100, 100, 100), width=3)
            
            # Draw text
            font = None
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
            except Exception:
                pass
                
            draw.text((100, config.IMAGE_HEIGHT // 2), f"Scene {i}\n{pos_prompt[:40]}...", fill=(255, 255, 255), font=font)
            
            filename = f"placeholder_{style}_{idea_id}_{i}.png"
            img_path = config.COMFYUI_OUTPUT_DIR / filename
            img.save(img_path)
            image_paths.append(str(img_path))

        # 4. Video assembly
        assembler = VideoAssembler()
        silent_video_filename = f"silent_reel_{idea_id}.mp4"
        
        # Assemble silent slideshow
        silent_video_path_str = assembler.assemble_reel(
            image_paths=image_paths,
            output_filename=silent_video_filename,
            story_text=title,
            intro_title=title,
            intro_subtitle=f"A {style.replace('_', ' ').title()} Story",
            outro_text="Follow for more 🔥"
        )
        silent_video_path = Path(silent_video_path_str)

        # 5. Visual effects (apply style-specific effects)
        effects = CinematicEffects()
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(str(silent_video_path))
        styled_clip = effects.apply_style_effects(clip, style)
        
        styled_video_filename = f"styled_reel_{idea_id}.mp4"
        styled_video_path = config.CONTENT_DIR / styled_video_filename
        
        console.print(f"[yellow]Applying visual effects and saving → {styled_video_path}[/yellow]")
        styled_clip.write_videofile(
            str(styled_video_path),
            fps=config.VIDEO_FPS,
            codec=config.VIDEO_CODEC,
            bitrate=config.VIDEO_BITRATE,
            audio=False
        )
        clip.close()
        styled_clip.close()
        
        # Delete intermediate silent video
        if silent_video_path.exists():
            os.remove(silent_video_path)

        # 6. Music intelligence
        jamendo = JamendoClient()
        try:
            music_path = jamendo.get_track_for_style(style, self.memory)
        except Exception as e:
            console.print(f"[red]Failed to get track for style: {e}[/red]")
            music_path = None
            
        final_video_filename = f"final_reel_{idea_id}_{style}.mp4"
        final_video_path = config.CONTENT_DIR / final_video_filename
        
        if music_path:
            mixer = AudioMixer()
            final_video_path = mixer.mix_audio(styled_video_path, music_path, final_video_filename)
            # Delete intermediate styled video
            if styled_video_path.exists():
                os.remove(styled_video_path)
        else:
            # If no music could be mixed, just rename the styled video to final
            os.rename(styled_video_path, final_video_path)
            console.print(f"[yellow]⚠️  Proceeded without music mixing. Saved to {final_video_path}[/yellow]")

        # 7. Record post in database
        caption_prompt = f"Write an engaging Instagram caption for an anime Reel titled '{title}' with a '{style}' style. Keep it short, include emojis, and suggest relevant hashtags. Return only the caption and hashtags."
        caption = self.think_fresh(caption_prompt)
        
        # Save post record
        post_id = self.memory.save_post(
            idea_id=idea_id,
            video_path=str(final_video_path),
            caption=caption,
            hashtags=",".join(config.BASE_HASHTAGS),
            music_track=music_path.name if music_path else "None",
            title=title,
            style=style
        )
        
        # Mark idea as published
        with self.memory._connect() as conn:
            conn.execute("UPDATE content_ideas SET status='published' WHERE id=?", (idea_id,))
            
        console.print(Panel(
            f"[bold green]✓ REEL COMPILED AND READY![/bold green]\n\n"
            f"Final File: [cyan]{final_video_path.name}[/cyan]\n"
            f"Post ID: {post_id} | Style: {style}\n"
            f"Caption: {caption[:120]}...",
            title="🎬 Compilation Successful",
            border_style="green"
        ))
        
        return str(final_video_path)
