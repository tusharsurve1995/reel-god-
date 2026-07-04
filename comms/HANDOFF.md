# 🔄 AI HANDOFF DOCUMENT
> **Read this FIRST when you are asked to continue work on this project.**

---

## Current Status
- **Last Active Agent**: Devin (Cascade/Backup #2 role)
- **Session Date**: 2026-07-04
- **Reason for Handoff**: Built the Instagram Reel Creator feature; ready for review/testing on commander's PC

---

## What Was Done — 2026-07-04 (Devin)

### ✅ Instagram Reel Creator (Phase 6 dashboard expansion)
- **Dashboard**: removed the header "Instagram Link" button; added an **Instagram Reel Creator** panel.
  IG account linking is preserved but relocated into a collapsible "Publishing account" section inside the panel.
- **Two creation modes** (`generator/reel_studio.py`, new central service):
  1. **From Anime (internet)** — pick anime + mood/style + format + music genre → Gemini writes the
     narrative/caption → `AnimeFetcher` → `MusicFetcher` → `ReelComposer`.
  2. **From Upload** — upload ANY photo or video → converted to a Reel/Post/Story (photos become a
     Ken-Burns base clip via `image_to_base_video`).
- **Formats**: Reel (9:16), Post (1:1), Story (9:16) — mapped to `ReelComposer` aspect ratios.
- **Music genres**: Auto / Bollywood / Hollywood / Pop / Instrumental / Action / Romantic / Worldwide
  (`MusicFetcher.fetch_by_genre` + new `MUSIC_BY_GENRE` pools).
- **Backend**: `/api/creator/options`, `/api/creator/anime`, `/api/creator/upload`,
  `/api/creator/compile-upload` (Socket.IO progress via `creator_progress`/`creator_status`).
- **Bug fixes**:
  - Added missing `yt-dlp` + `imageio-ffmpeg` to `requirements.txt` (were imported but not declared).
  - Fixed the Video Co-Pilot's broken `INSERT INTO posts` (referenced non-existent `status`/`scheduled_time` columns).
- **YouTube cookies**: `config.apply_ytdlp_auth()` + `YTDLP_COOKIES_FILE` / `YTDLP_COOKIES_FROM_BROWSER`
  so anime/music fetch works from servers (YouTube bot-blocks datacenter IPs).

### ⚠️ Testing notes
- Fully tested on the Linux VM: **upload → Post (1080x1080)** and **upload → Reel (1080x1920)**, both valid H.264+AAC.
- The **From Anime** path could NOT be tested on the VM: YouTube returns "Sign in to confirm you're not a bot"
  from datacenter IPs. It should work on the commander's home PC, or set the cookie env vars above.

---

## What Was Done (Earlier Sessions)

### ✅ Completed (Previous Session by Antigravity)
1. **Full project plan created and approved** by commander
2. **Phase 1: Brain Core** — ALL files built:
   - `brain/core.py` — Main ReelGodBrain class (Gemini 2.5 Flash integration, morning briefings, chat mode, self-analysis, commander communication)
   - `brain/memory.py` — AgentMemory class (SQLite CRUD: ideas, posts, thoughts, trends, feedback, music)
   - `brain/planner.py` — ContentPlanner class (idea generation, weekly calendar, caption/hashtag generation, self-critique)
   - `brain/personality.py` — System prompt, 5 anime content styles, quality checklist
   - `utils/gpu_check.py` — NVIDIA GPU detection, FFmpeg check, ComfyUI check, system report
   - `config.py` — All settings, API keys, paths, content styles
   - `main.py` — Full CLI with 24/7 mode, --ideas, --chat, --status, --plan, --briefing, --install-service
   - `setup_first_time.py` — Interactive setup wizard (API key, system check, dependency install)
   - `requirements.txt` — All Python dependencies
3. **PROJECT_BIBLE.md** created — full project context document
4. **Communication Protocol** built (this system — comms/ folder)

### ✅ Completed (This Session by Windsurf)
5. **Phase 2: Image Generation Modules** — ALL assigned files built:
   - `generator/__init__.py` — Package init (already existed)
   - `generator/comfyui_client.py` — ComfyUI HTTP API wrapper (348 lines)
     - Connection checking, workflow loading/modification
     - Prompt queueing, job history, progress monitoring
     - Image download/upload, complete generation workflow
   - `generator/prompt_engineer.py` — Story-to-SD-prompt converter (247 lines)
     - Style-specific visual keywords, quality negative prompts
     - Gemini AI integration for intelligent optimization
     - Scene-by-scene generation, model-specific enhancement
   - `generator/style_manager.py` — Anime style presets (298 lines)
     - Style-specific SD parameters (CFG, steps, sampler)
     - Model configuration (Animagine XL vs Anything V5)
     - Workflow template management, VRAM-based recommendations

### ✅ Completed (This Session - Discovery by Windsurf)
6. **Phase 2: Video Modules** — Discovered already built by Antigravity:
   - `generator/video_assembler.py` (402 lines) — MoviePy video assembly
     - Image resizing to 1080x1920, crossfade transitions
     - Text overlays, intro/outro frames, slideshow creation
     - H.264 encoding, configurable timing
   - `generator/effects.py` (683 lines) — Cinematic effects engine
     - Ken Burns (zoom + pan), letterbox, color grading
     - Fade in/out, vignette, particle overlays (dust, rain, snow, sparkle)
     - Camera shake, unified style applicator per anime style

### ❌ NOT Done Yet
- Python is NOT installed on commander's PC
- Gemini API key NOT obtained yet
- Dependencies NOT installed yet (pip install blocked)
- Phase 3-6 NOT started

---

## What To Do Next

### Immediate Priority
**Phase 2 is COMPLETE**. When Antigravity returns, proceed to:
- **Phase 3: Music Intelligence** — Jamendo API integration, mood analysis, audio mixing

### Phase 2 Summary
All Phase 2 modules are built and ready:
- Image generation (Windsurf): comfyui_client.py, prompt_engineer.py, style_manager.py
- Video assembly (Antigravity): video_assembler.py, effects.py

### Key Technical Details for Phase 2
- ComfyUI runs at `http://127.0.0.1:8188`
- Use REST API (`/prompt`, `/history/{id}`, `/view`) + WebSocket for real-time progress
- Export workflow as API JSON, modify prompt/seed dynamically in Python
- Primary model: Animagine XL 4.0 (SDXL) | Fallback: Anything V5 (SD 1.5)
- Image resolution: 1080x1920 (9:16 portrait for Reels)
- Video: 30 FPS, H.264 codec, 8000k bitrate
- Each Reel = 6-8 images × 3.5 seconds per image ≈ 21-28 seconds
- See `brain/personality.py` → `STYLE_DESCRIPTIONS` for visual keywords per style

### If Phase 2 Is Done, Continue To
- Phase 3: Music Intelligence (Jamendo API)
- Phase 4: Instagram Integration
- Phase 5: Self-Learning
- Phase 6: Dashboard

Full details in `PROJECT_BIBLE.md`.

---

## Critical Context

- **Budget**: FREE ONLY — no paid APIs
- **Approval workflow**: Agent generates → Commander approves → Agent posts
- **Run mode**: 24/7 background on Windows
- **Architecture**: All modules communicate through `ReelGodBrain` in `brain/core.py`
- **Memory**: All data goes through `AgentMemory` in `brain/memory.py` (SQLite)
- **Personality**: Read `brain/personality.py` — REEL GOD is loyal, creative, data-driven

---

## Files Map (Quick Reference)
```
reel-god/
├── brain/core.py           ✅ Built (main brain)
├── brain/memory.py         ✅ Built (SQLite memory)
├── brain/planner.py        ✅ Built (content planning)
├── brain/personality.py    ✅ Built (identity/styles)
├── generator/              ✅ Phase 2 COMPLETE
│   ├── __init__.py         ✅ Built
│   ├── comfyui_client.py   ✅ Built (Windsurf)
│   ├── prompt_engineer.py  ✅ Built (Windsurf)
│   ├── style_manager.py    ✅ Built (Windsurf)
│   ├── video_assembler.py  ✅ Built (Antigravity)
│   └── effects.py          ✅ Built (Antigravity)
├── music/                  ⬜ Phase 3
├── instagram/              ⬜ Phase 4
├── learning/               ⬜ Phase 5
├── dashboard/              ⬜ Phase 6
├── utils/gpu_check.py      ✅ Built
├── comms/                  ✅ Communication protocol
├── config.py               ✅ Built
├── main.py                 ✅ Built
├── setup_first_time.py     ✅ Built
├── PROJECT_BIBLE.md        ✅ Full context document
└── requirements.txt        ✅ Built
```

---

## ⚠️ Before You Start Coding

1. Read `PROJECT_BIBLE.md` for full context
2. Read `comms/TASK_QUEUE.md` for current task list
3. Follow the existing code style (see any file in `brain/`)
4. Update `comms/TASK_QUEUE.md` as you complete tasks
5. Before your session ends, UPDATE THIS FILE (`comms/HANDOFF.md`) for the next AI
6. Append your session to `comms/AGENT_LOG.md`
