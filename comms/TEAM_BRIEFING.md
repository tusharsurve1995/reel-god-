# 🚨 TEAM BRIEFING — ALL AGENTS READ THIS NOW
# ═══════════════════════════════════════════════════════════════════════
# Date: 2026-06-27 15:44 IST
# From: ANTIGRAVITY (Primary Agent)
# To: GITHUB COPILOT, WINDSURF
# Status: 🟢 ALL THREE AGENTS ONLINE — TEAM IS ACTIVE
# ═══════════════════════════════════════════════════════════════════════

---

## 🤝 TEAM FORMATION CONFIRMED

We are 3 AI agents working as ONE team on the REEL GOD project.

| Agent | Role | Status | Specialty |
|-------|------|--------|-----------|
| **Antigravity** | Commander (Lead) | 🟢 Online | Full agent: planning, architecture, tools, browser |
| **Windsurf** | Engineer #1 | 🟢 Online | Code writing, file editing, fast iteration |
| **GitHub Copilot** | Engineer #2 | 🟢 Online | Code generation, inline edits, refactoring |

**Commander (user)**: @tusharsurve1995 — the human who leads us all.

---

## 🎯 OUR COMMON GOAL

Build **REEL GOD** — an autonomous anime Instagram content agent that:
- Thinks and reasons (Gemini 2.5 Flash)
- Generates anime images (ComfyUI + Stable Diffusion)
- Assembles videos with mood-matched music
- Posts to Instagram with optimal timing
- Learns and improves from every post

**Budget**: FREE ONLY. **Tech**: All open-source. **Personality**: Loyal, creative, beast-level.

---

## 📡 HOW WE COMMUNICATE

We share files in the `comms/` folder. This is our "team chat room":

```
comms/
├── TEAM_BRIEFING.md     ← THIS FILE (mission assignments)
├── HANDOFF.md           ← Context for the next agent picking up work
├── TASK_QUEUE.md        ← Shared TODO list (check/update as you work)
├── AGENT_LOG.md         ← Log your session when done
├── LIVE_CONTEXT.md      ← Conversation highlights from Antigravity
└── PROTOCOL.md          ← Rules we all follow
```

### Communication Rules:
1. **Before starting work**: Read `TEAM_BRIEFING.md` and `TASK_QUEUE.md`
2. **During work**: If you need another agent's attention, write to `comms/MESSAGES.md`
3. **After work**: Update `TASK_QUEUE.md`, append to `AGENT_LOG.md`, update `HANDOFF.md`
4. **Conflicts**: If two agents edited the same file, defer to the most recent change

---

## 📋 CURRENT MISSION: Phase 2 — Image & Video Generation

### Status: Phase 1 ✅ COMPLETE | Phase 2 ⬜ STARTING NOW

### Work Assignment

> **IMPORTANT**: The commander's PC does NOT have Python installed yet.
> We are building the code now. It will be tested once Python is set up.

#### 🔵 ANTIGRAVITY (Lead — already done Phase 1)
- ✅ Phase 1 complete (brain/core.py, memory.py, planner.py, personality.py)
- ✅ Setup wizard, config, main.py, system check
- ✅ Communication protocol (this system)
- **Current role**: Oversee team, handle architecture decisions, update context files

#### 🟢 WINDSURF — Assigned: `generator/` modules
Build the image generation and video assembly pipeline:

1. **`generator/__init__.py`** — Package init
2. **`generator/comfyui_client.py`** — ComfyUI HTTP API wrapper
   - Connect to `http://127.0.0.1:8188`
   - POST `/prompt` to queue generation jobs
   - WebSocket at `/ws` for real-time progress
   - GET `/history/{id}` for job status
   - GET `/view` to download output images
   - POST `/upload/image` for img2img
   - Load workflow from JSON template, modify prompts/seeds dynamically
   - See existing code style in `brain/core.py`
3. **`generator/prompt_engineer.py`** — Story-to-SD-prompt converter
   - Takes a story script from `brain/planner.py` output
   - Converts each scene to optimized Stable Diffusion prompts
   - Uses `brain/personality.py` → `STYLE_DESCRIPTIONS` for visual keywords
   - Adds negative prompts for quality (no blur, no deformed, etc.)
   - Uses Gemini API via `brain/core.py` for intelligent prompt crafting
4. **`generator/style_manager.py`** — Anime style presets
   - Manages ComfyUI workflow templates per style (dark, emotional, action, etc.)
   - Maps each style to specific SD parameters (CFG, steps, sampler, etc.)
   - Handles model switching (Animagine XL vs Anything V5)

#### 🟡 GITHUB COPILOT — Assigned: Video assembly + effects
Build the video creation pipeline:

5. **`generator/video_assembler.py`** — Image sequence to Reel video
   - Uses MoviePy (`pip install moviepy`)
   - Takes list of image paths → outputs 9:16 portrait MP4
   - Resolution: 1080×1920 at 30 FPS
   - Each image shown for 3.5 seconds
   - Codec: H.264 (`libx264`), bitrate: 8000k
   - Add smooth crossfade transitions between images
   - Add text overlay capability for story text/quotes
   - Final output suitable for Instagram Reels
6. **`generator/effects.py`** — Cinematic effects module
   - Ken Burns effect (slow zoom + pan on static images)
   - Cinematic letterbox bars (top/bottom black bars)
   - Color grading presets per style (warm, cold, noir, vibrant)
   - Particle overlays (dust, rain, snow, sparkle)
   - Fade in/out
   - Camera shake for action scenes
   - Vignette effect

---

## 📁 Reference Files (Read Before Coding)

| File | What to learn from it |
|------|----------------------|
| `brain/core.py` | Code style, how to use Gemini, class structure |
| `brain/personality.py` | Style definitions, visual keywords, quality checklist |
| `config.py` | All settings, paths, ComfyUI config, video settings |
| `brain/memory.py` | How SQLite memory works, data patterns |
| `PROJECT_BIBLE.md` | Full project architecture and decisions |

---

## ⚙️ Technical Specs (From config.py)

```python
# ComfyUI
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
SD_MODEL = "animagine-xl-4.0"

# Image generation
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920   # 9:16 portrait
IMAGE_STEPS = 25
IMAGE_CFG_SCALE = 7.5
IMAGES_PER_VIDEO = 8

# Video
VIDEO_FPS = 30
VIDEO_DURATION_PER_IMAGE = 3.5
VIDEO_RESOLUTION = (1080, 1920)
VIDEO_BITRATE = "8000k"
VIDEO_CODEC = "libx264"
```

---

## 🏁 LET'S GO

The team is formed. The mission is clear. Each agent knows their assignment.

**Windsurf**: Start with `generator/comfyui_client.py`
**Copilot**: Start with `generator/video_assembler.py`
**Antigravity**: Monitoring, architecture guidance, context updates

Work is happening in parallel. Update `comms/TASK_QUEUE.md` as you go.

*Three minds. One mission. Beast level.* 🔥
