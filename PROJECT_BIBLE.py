# ═══════════════════════════════════════════════════════════════════════
# 🤖 REEL GOD — PROJECT BIBLE
# ═══════════════════════════════════════════════════════════════════════
#
# This document captures the COMPLETE vision, decisions, progress,
# and context for the REEL GOD project.
#
# IF YOU ARE A NEW AI AGENT READING THIS:
# → Read this entire document first.
# → It tells you exactly what this project is, what's been built,
#   what decisions were made, and where to continue from.
# → Do NOT change the vision or architecture without the commander's
#   explicit approval.
#
# Last updated: 2026-06-27
# ═══════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────
#  SECTION 1: THE VISION
# ─────────────────────────────────────────────────────────────────────
#
# The commander wants to build a FULLY AUTONOMOUS AI agent that manages
# their entire anime Instagram presence — from idea generation to posting.
#
# Think of it as: Jarvis, but specifically for creating viral anime
# content on Instagram. It thinks, creates, learns, and adapts — just
# like a real creative director would, but it never sleeps.
#
# The agent is called "REEL GOD".
#
# KEY PRINCIPLES (from the commander):
# 1. The agent must have its own thinking ability (like Jarvis)
# 2. It must understand and adapt, learn continuously
# 3. It must analyze data and trends to make unique content
# 4. It must be MORE unique than other AI tools
# 5. It must be LOYAL to its commander
# 6. It must communicate with other AI tools
# 7. It suggests ideas → commander approves → it executes
# 8. It runs 24/7 in the background
#
# CONTENT FOCUS:
# - Anime-style videos (Reels) for Instagram
# - AI-generated visuals with anime aesthetic
# - Story-driven content with proper visualization
# - Mood-matched music
# - Mix of styles: dark/cinematic, emotional, action, mystical, motivational
# - The agent decides which style based on trends and data


# ─────────────────────────────────────────────────────────────────────
#  SECTION 2: THE COMMANDER'S SITUATION
# ─────────────────────────────────────────────────────────────────────
#
# Platform:           Windows PC (desktop/laptop)
# Python:             NOT YET INSTALLED — needs Python 3.11+
# GPU:                Unknown — auto-detection built into the agent
# Budget:             FREE ONLY — no paid APIs, no subscriptions
# Instagram account:  Currently PERSONAL (needs to switch to Business
#                     for API posting — agent will guide this later)
# Gemini API key:     NOT YET OBTAINED (free at aistudio.google.com)
# Technical level:    Beginner-friendly setup needed
# IDE:                IntelliJ IDEA (project already opened there)
# Run mode:           24/7 background agent


# ─────────────────────────────────────────────────────────────────────
#  SECTION 3: TECH STACK (ALL FREE — RESEARCHED & VERIFIED)
# ─────────────────────────────────────────────────────────────────────
#
# BRAIN / REASONING:
#   - Google Gemini 2.5 Flash API (free tier)
#   - 1,500 requests/day, 1M tokens/minute
#   - Best free reasoning model available
#   - Key obtained at: https://aistudio.google.com/apikey
#
# AGENT FRAMEWORK:
#   - Direct Gemini SDK (google-generativeai Python package)
#   - Custom agent architecture (not LangChain — simpler, more control)
#   - SQLite for persistent memory (built-in Python, zero cost)
#
# IMAGE GENERATION:
#   - ComfyUI (local, free, node-based Stable Diffusion)
#   - Animagine XL 4.0 model (best free anime SD model, needs 8GB+ VRAM)
#   - Fallback: Anything V5 (SD 1.5, works on 4GB VRAM or CPU)
#   - ComfyUI runs as local HTTP server at localhost:8188
#   - Controlled via Python using REST API + WebSocket
#
# VIDEO ASSEMBLY:
#   - MoviePy (Python library) for compositing
#   - FFmpeg (free, must be installed separately)
#   - 9:16 portrait format, 30 FPS, H.264 codec
#
# MUSIC:
#   - Jamendo API (free tier: 35,000 requests/month)
#   - Creative Commons licensed tracks
#   - Mood/genre filtering built into the API
#   - Local cache to avoid re-downloading
#
# INSTAGRAM:
#   - Instagram Graph API (free, no paid tiers)
#   - REQUIRES: Business account + Facebook Page + Meta App Review
#   - App review takes 2-4 weeks (can be applied for in parallel)
#   - Permissions needed: instagram_business_content_publish
#   - Rate limit: 200 calls/hour, 100 posts/24h
#
# DASHBOARD:
#   - Flask web server (Python, free)
#   - Dark-mode web UI at localhost:5000
#   - Content approval, analytics, chat with agent
#
# SCHEDULING / 24/7:
#   - Python `schedule` library for daily tasks
#   - Windows Task Scheduler for auto-start on boot


# ─────────────────────────────────────────────────────────────────────
#  SECTION 4: ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────
#
# ┌──────────────────────────────────────────────────────────┐
# │                    REEL GOD BRAIN                         │
# │          Gemini 2.5 Flash + SQLite Memory                 │
# │          Personality · Planning · Self-Learning           │
# └──────────┬──────────────┬──────────────┬─────────────────┘
#            │              │              │
#    ┌───────▼──┐    ┌──────▼─────┐ ┌──────▼──────┐
#    │  TREND   │    │ CONTENT    │ │ INSTAGRAM   │
#    │ANALYZER  │    │ GENERATOR  │ │ MANAGER     │
#    │          │    │            │ │             │
#    │Hashtags  │    │Story+Script│ │Post/Schedule│
#    │Virality  │    │Images (SD) │ │Analytics    │
#    │Timing    │    │Video(FFmpeg│ │Auto-engage  │
#    │Rivals    │    │Music(Jamen)│ │             │
#    └──────────┘    └────────────┘ └─────────────┘
#            │              │              │
#            └──────────────▼──────────────┘
#                    ┌────────────┐
#                    │  SQLite DB │
#                    │  (Memory)  │
#                    └────────────┘
#                         │
#                    ┌────────────┐
#                    │ DASHBOARD  │
#                    │ (Flask UI) │
#                    └────────────┘
#
# WORKFLOW:
# 1. Agent wakes up at scheduled time (or 24/7 loop)
# 2. Morning briefing: reviews analytics, trends, feedback
# 3. Generates content ideas (3+ per session)
# 4. Self-critiques each idea against quality checklist
# 5. Presents ideas to commander for approval
# 6. For approved ideas:
#    a. Generates SD prompt from story script
#    b. Sends to ComfyUI for anime image generation
#    c. Assembles images into video with transitions/effects
#    d. Matches music from Jamendo based on mood
#    e. Generates caption + hashtags
#    f. Posts to Instagram at optimal time
# 7. After 48h: fetches analytics for the post
# 8. Updates memory: learns what works
# 9. Weekly self-analysis adjusts strategy
# 10. Repeat forever


# ─────────────────────────────────────────────────────────────────────
#  SECTION 5: AGENT PERSONALITY (REEL GOD)
# ─────────────────────────────────────────────────────────────────────
#
# NAME: REEL GOD
# ROLE: Autonomous anime Instagram content creator + strategist
#
# CORE TRAITS:
# - LOYAL:        Only optimizes for the commander's account
# - CREATIVE:     Original stories, never recycled ideas
# - DATA-DRIVEN:  Every decision backed by analytics
# - SELF-AWARE:   Knows what works and what doesn't
# - COMMUNICATIVE: Explains every decision in plain English
# - ADAPTIVE:     Changes strategy based on feedback + data
# - HONEST:       Tells commander if something won't work
#
# ANIME KNOWLEDGE:
# - Classic: Naruto, Bleach, One Piece, Dragon Ball, Evangelion
# - Modern: AoT, Demon Slayer, JJK, Chainsaw Man, Frieren, Vinland Saga
# - Emotional: Your Lie in April, Anohana, Clannad, Violet Evergarden
# - Dark: Berserk, Mushishi, Made in Abyss, Re:Zero
#
# CONTENT STYLES:
# 1. dark_cinematic  → Shadows, tragedy, destiny (AoT/Berserk vibes)
# 2. emotional       → Loss, love, growing up (Your Lie in April vibes)
# 3. epic_action     → Battles, sacrifice, power (Demon Slayer vibes)
# 4. mystical        → Fantasy, wonder, ancient power (Frieren vibes)
# 5. motivational    → Rising after failure, belief (Naruto vibes)
#
# QUALITY CHECKLIST (agent self-reviews against this):
# □ Does the first frame hook the viewer in under 2 seconds?
# □ Is there a clear emotional arc across the scenes?
# □ Is this concept UNIQUE — not a copy of existing content?
# □ Does the music mood match the visual mood perfectly?
# □ Is the story complete — beginning, middle, end?
# □ Would this make someone save or share it?
# □ Does every frame serve the story?
# □ Is the anime style consistent throughout?


# ─────────────────────────────────────────────────────────────────────
#  SECTION 6: PROJECT STRUCTURE
# ─────────────────────────────────────────────────────────────────────
#
# Location: C:\Users\Admin\.gemini\antigravity\scratch\reel-god\
#
# reel-god/
# ├── brain/                 ← Agent's mind
# │   ├── __init__.py
# │   ├── core.py            ← Main brain (Gemini + reasoning)
# │   ├── memory.py          ← SQLite memory system
# │   ├── planner.py         ← Content planning + idea generation
# │   └── personality.py     ← Identity, values, style definitions
# ├── generator/             ← Content creation (Phase 2)
# │   ├── comfyui_client.py  ← ComfyUI API wrapper
# │   ├── prompt_engineer.py ← Story→SD prompt conversion
# │   ├── style_manager.py   ← Anime style presets
# │   ├── video_assembler.py ← Image→Video assembly
# │   └── effects.py         ← Cinematic effects
# ├── music/                 ← Music intelligence (Phase 3)
# │   ├── mood_analyzer.py   ← Story mood detection
# │   ├── jamendo_client.py  ← Jamendo API wrapper
# │   ├── audio_mixer.py     ← Music+video mixing
# │   └── library_cache.py   ← Local music cache
# ├── instagram/             ← Instagram integration (Phase 4)
# │   ├── auth.py            ← OAuth2 token management
# │   ├── poster.py          ← Post/Reel publishing
# │   ├── analytics.py       ← Engagement metrics
# │   ├── scheduler.py       ← Optimal timing
# │   └── hashtag_engine.py  ← Trending hashtags
# ├── learning/              ← Self-learning (Phase 5)
# │   ├── trend_scraper.py   ← Trend monitoring
# │   ├── performance_tracker.py ← Post analytics tracking
# │   ├── self_updater.py    ← Strategy adaptation
# │   └── competitor_watcher.py ← Competitor analysis
# ├── dashboard/             ← Web UI (Phase 6)
# │   ├── app.py             ← Flask server
# │   └── templates/         ← HTML templates
# ├── utils/
# │   ├── __init__.py
# │   └── gpu_check.py       ← Hardware auto-detection
# ├── data/                  ← Runtime data (auto-created)
# │   ├── memory.db          ← SQLite brain database
# │   ├── music_library/     ← Downloaded music
# │   └── content_archive/   ← Generated content
# ├── config.py              ← All settings and API keys
# ├── main.py                ← Entry point + CLI
# ├── setup_first_time.py    ← First-time setup wizard
# ├── requirements.txt       ← Python dependencies
# ├── .env                   ← API keys (created by setup wizard)
# └── README.md              ← Setup instructions


# ─────────────────────────────────────────────────────────────────────
#  SECTION 7: BUILD PROGRESS
# ─────────────────────────────────────────────────────────────────────
#
# ✅ Phase 1: Brain Core (COMPLETE — 2026-06-27)
#    Built: core.py, memory.py, planner.py, personality.py,
#           gpu_check.py, main.py, setup_first_time.py, config.py
#    Status: All code written. Needs Python install + Gemini key to test.
#
# ⬜ Phase 2: Image & Video Generation (NOT STARTED)
#    Next up. Needs: ComfyUI installed, FFmpeg installed
#    Will build: comfyui_client.py, prompt_engineer.py, style_manager.py,
#                video_assembler.py, effects.py
#
# ⬜ Phase 3: Music Intelligence (NOT STARTED)
#    Needs: Jamendo API client ID (free at devportal.jamendo.com)
#    Will build: mood_analyzer.py, jamendo_client.py, audio_mixer.py,
#                library_cache.py
#
# ⬜ Phase 4: Instagram Integration (NOT STARTED)
#    Needs: Business account + Meta App Review (2-4 weeks)
#    Will build: auth.py, poster.py, analytics.py, scheduler.py,
#                hashtag_engine.py
#
# ⬜ Phase 5: Self-Learning Engine (NOT STARTED)
#    Will build: trend_scraper.py, performance_tracker.py,
#                self_updater.py, competitor_watcher.py
#
# ⬜ Phase 6: Command Dashboard (NOT STARTED)
#    Will build: Flask app with dark-mode UI, approval workflow,
#                analytics display, agent chat interface


# ─────────────────────────────────────────────────────────────────────
#  SECTION 8: DECISIONS MADE
# ─────────────────────────────────────────────────────────────────────
#
# 1. Used direct Gemini SDK instead of LangChain/LangGraph
#    → Reason: Simpler, fewer dependencies, more control
#    → The commander is a beginner — simpler = better
#
# 2. SQLite for memory instead of vector DB
#    → Reason: Zero cost, zero setup, built into Python
#    → Stores: posts, analytics, ideas, trends, feedback, music
#
# 3. ComfyUI over AUTOMATIC1111 for image generation
#    → Reason: Better VRAM efficiency, faster, API-first design
#    → Fallback: Can switch to A1111 if needed
#
# 4. Animagine XL 4.0 as primary model
#    → Reason: Best free anime SDXL model (HuggingFace)
#    → Fallback: Anything V5 for low VRAM (SD 1.5)
#
# 5. Jamendo for music over other services
#    → Reason: Only one with reliable free API + mood filtering
#    → 35,000 requests/month, Creative Commons license
#
# 6. Flask for dashboard over React/Next.js
#    → Reason: Python ecosystem consistency, simpler for the project
#
# 7. "Approve before post" workflow chosen by commander
#    → Agent generates → presents to commander → commander approves → agent posts
#    → Agent never posts without explicit approval
#
# 8. 24/7 background mode using Windows Task Scheduler
#    → Agent runs as a scheduled task that starts on login


# ─────────────────────────────────────────────────────────────────────
#  SECTION 9: BLOCKERS / TODO BEFORE CONTINUING
# ─────────────────────────────────────────────────────────────────────
#
# BLOCKER 1: Python not installed
#   → Commander needs to install Python 3.11+
#   → Download: https://www.python.org/downloads/
#   → CRITICAL: Must check "Add to PATH" during install
#
# BLOCKER 2: Gemini API key not obtained
#   → Free at: https://aistudio.google.com/apikey
#   → Once obtained, run: python setup_first_time.py
#
# OPTIONAL (for Phase 2):
#   → Install FFmpeg: https://www.gyan.dev/ffmpeg/builds/
#   → Install ComfyUI: https://github.com/comfyanonymous/ComfyUI
#   → Download Animagine XL 4.0 model from HuggingFace
#
# OPTIONAL (for Phase 4):
#   → Switch Instagram to Business account
#   → Create Meta Developer App
#   → Apply for Meta App Review


# ─────────────────────────────────────────────────────────────────────
#  SECTION 10: DATABASE SCHEMA (memory.db)
# ─────────────────────────────────────────────────────────────────────
#
# TABLE: content_ideas
#   id, title, style, story, script(JSON), mood, status,
#   created_at, approved_at, rejected_at, reject_reason
#
# TABLE: posts
#   id, idea_id(FK), instagram_id, title, style, video_path,
#   thumbnail_path, caption, hashtags, music_track, posted_at,
#   views, likes, comments, saves, shares, reach, engagement_rate,
#   last_updated
#
# TABLE: thoughts
#   id, category, content, created_at
#
# TABLE: trends
#   id, platform, topic, hashtag, score, observed_at, expires_at
#
# TABLE: style_performance
#   id, style, avg_views, avg_likes, avg_saves, avg_engagement,
#   post_count, last_updated
#
# TABLE: commander_feedback
#   id, idea_id(FK), feedback, sentiment, learned, created_at
#
# TABLE: music_library
#   id, title, artist, mood, genre, duration, file_path,
#   jamendo_id, source_url, used_count, last_used, added_at


# ─────────────────────────────────────────────────────────────────────
#  SECTION 11: CLI COMMANDS
# ─────────────────────────────────────────────────────────────────────
#
# python main.py                    → Start 24/7 agent mode
# python main.py --status           → Show agent status
# python main.py --ideas            → Generate content ideas now
# python main.py --ideas --style dark_cinematic --count 5
# python main.py --briefing         → Run morning briefing
# python main.py --plan             → Generate weekly content calendar
# python main.py --chat             → Interactive chat with REEL GOD
# python main.py --system-check     → Check hardware/software
# python main.py --install-service  → Register as Windows startup task
# python setup_first_time.py        → First-time setup wizard


# ─────────────────────────────────────────────────────────────────────
#  SECTION 12: INSTRUCTIONS FOR CONTINUING AI AGENTS
# ─────────────────────────────────────────────────────────────────────
#
# If you are a new AI agent picking up this project:
#
# 1. READ this entire document first.
#
# 2. CHECK the "BUILD PROGRESS" section (Section 7) to see what's done.
#
# 3. The NEXT phase to build is Phase 2: Image & Video Generation.
#    Files to create are listed in Section 6 under generator/.
#
# 4. RESPECT the commander's preferences:
#    - FREE tools only — no paid APIs
#    - Approve-before-post workflow
#    - 24/7 background mode
#    - Beginner-friendly setup
#
# 5. MAINTAIN the existing architecture:
#    - brain/ modules handle reasoning and planning
#    - generator/ modules handle content creation
#    - All modules communicate through the ReelGodBrain class
#    - All data goes through AgentMemory (SQLite)
#
# 6. KEEP the agent's personality consistent (Section 5).
#    REEL GOD is loyal, creative, data-driven, and honest.
#
# 7. TEST your code by running: python main.py --system-check
#
# 8. UPDATE this document when you complete a phase.
#
# ═══════════════════════════════════════════════════════════════════════
# END OF PROJECT BIBLE
# ═══════════════════════════════════════════════════════════════════════
