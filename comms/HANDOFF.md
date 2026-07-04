# 🔄 AI HANDOFF DOCUMENT
> **Read this FIRST when you are asked to continue work on this project.**

---

## Current Status
- **Last Active Agent**: Devin (Cascade/Backup #2 role)
- **Session Date**: 2026-07-04
- **Reason for Handoff**: Hardening & polish pass on the web app — security (session cookie flags, auto-generated secret key, login rate-limiting, upload size cap, CORS config), robust error handling (JSON 401/404/413/500 + `/healthz`), stronger password/username rules, UI/text polish, and docs. Cross-platform web-app PR #5 is merged into main.

---

## What Was Done — 2026-07-04 (Devin, session 4: hardening & polish)

Branch → PR (see GitHub). Built on top of merged PR #5.

### 🛡️ Security
- `dashboard/security.py` (NEW) — dependency-free `LoginRateLimiter` (per-IP sliding
  window + lockout), `ensure_secret_key` (auto-generates & persists a strong random
  `DASHBOARD_SECRET_KEY` when the insecure placeholder is used), `client_ip` helper.
- `dashboard/app.py` — hardened session cookies (`HttpOnly`, `SameSite=Lax`,
  `Secure` via env), `PERMANENT_SESSION_LIFETIME`, `MAX_CONTENT_LENGTH` upload cap,
  configurable Socket.IO CORS, login route now rate-limited (429 on lockout).
- `config.py` — new hardening settings (all env-overridable).

### 🧯 Error handling / robustness
- JSON error handlers for 404/413/500; API `login_required` now returns 401 JSON
  (not an HTML redirect) so the frontend can detect expired sessions.
- `/healthz` liveness endpoint (used by `render.yaml`).
- Safe JSON parsing (`_json_body()` replaces every `request.json or {}`).
- `save_env_var` now writes to an absolute `.env` path (CWD-independent).
- Fixed a bare `except:` and an f-string-without-placeholders lint warning.

### 🔐 Auth rules
- `dashboard/auth.py` — shared `_validate_credentials` (username regex 3–32 chars,
  password ≥ `MIN_PASSWORD_LENGTH`), applied to create + change-password.

### 🎨 UI / text
- Login: dynamic error messages (incl. lockout), "show password" toggle.
- Register: password-requirement hint + `minlength`.
- Settings: new "Security & Access" info card.

### 📄 Docs
- `docs/DEPLOYMENT.md` (NEW) — deploy + security guide + full env-var table.

### Verified (local)
✅ `pyflakes` clean; app imports; `/healthz` ok; API 401/404 JSON; login success →
   302; 8 failed logins → 429 lockout; settings authed 200.

---

## What Was Done — 2026-07-04 (Devin, session 3: use-it-everywhere web app)

Goal: let the commander use REEL GOD on **mobile, laptop, anywhere** from **one common codebase**.

### ✅ Responsive UI (mobile-friendly)
- `dashboard/static/style.css` — creator "Format/Style/Music" row and copilot keyframe
  grid now stack on phones; source tabs go full-width; smaller headings/padding on
  narrow screens. Inline grids given classes (`.creator-grid-3`, `.copilot-keyframes-grid`).

### ✅ PWA (installable on phone + laptop, no App Store)
- `dashboard/static/manifest.webmanifest`, `dashboard/static/sw.js` (service worker:
  cache-first static, network-only pages/API so live agent state is never stale).
- `dashboard/static/icons/` — generated app icons (192/512/apple-touch/favicon).
- Served at root via `/manifest.webmanifest` and `/sw.js` routes (`Service-Worker-Allowed: /`).
- PWA `<head>` + SW registration added to `index.html` / `login.html`.

### ✅ Secure multi-account login (safe to expose publicly)
- `dashboard/auth.py` (NEW) — `users` table in SQLite, **hashed** passwords
  (werkzeug), bootstrap admin seeded from `COMMANDER_USERNAME`/`COMMANDER_PASSWORD`.
- `login` now takes username + password; `/register` (open only on first run, then
  logged-in add-user); one shared workspace.

### ✅ In-app Settings page (`/settings`)
- Set free API keys (Gemini/Pexels/Pixabay/Jamendo) in the UI — saved to `.env` +
  live `os.environ` + `config` module, so they apply **without a restart**.
- Change your password; add more logins. Endpoints: `/api/settings`,
  `/api/account/password`, `/api/account/create`.

### ✅ Deploy config
- `Procfile`, `render.yaml` (free tier), `gunicorn`+`eventlet` in requirements,
  `$PORT` + `DASHBOARD_SECRET_KEY` read from env.

### Next steps / ideas
- Deploy to Render (needs the commander's account) → permanent public URL.
- Optional: full multi-tenant (separate content per account) is a bigger refactor.

---

## What Was Done — 2026-07-04 (Devin, session 2: royalty-free sources)

### ✅ New legal, server-friendly content sources
- **`generator/stock_fetcher.py` (NEW)** — `StockFetcher` pulls HD **royalty-free**
  video + photos from **Pexels** and **Pixabay** (both free API keys). Caches to
  `data/stock_clips/`, degrades gracefully to `None` when no key is set, and maps
  each mood/style to good cinematic search terms.
- **`generator/reel_studio.py`** — new `source="stock"` path: fetch stock video
  (or fall back to a stock photo → Ken-Burns base clip) for the chosen format/mood.
- **`music/music_fetcher.py`** — music now prefers **Jamendo Creative-Commons**
  (`_jamendo_fetch`, legal + works on servers) BEFORE YouTube search and SoundHelix.
  Added `GENRE_TO_JAMENDO_TAGS` mapping all 8 genres to CC tags.
- **`config.py`** — `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `stock_sources_available()`.
- **Dashboard** — new **🎥 Stock (royalty-free)** source tab + `/api/creator/stock`
  endpoint; `/api/creator/options` now reports which stock sources are configured,
  and the UI shows a ✅/⚠️ status line.
- **`docs/CONTENT_SOURCES.md` (NEW)** — beginner guide: what changed, how to get the
  free keys, **how to verify everything works** (CLI + dashboard + ffprobe), and a
  comparison of shipping REEL GOD as an **agent** vs a **desktop/web application**.

### ⚖️ Deliberately NOT done (declined for legal/ToS reasons)
- **ReVanced / Vanced / YouTube-Premium bypass** — violates YouTube ToS; not integrated.
- **Anime piracy/streaming sites (AnimeSalt, gogoanime, etc.)** — reposting copyrighted
  anime is infringement and gets Instagram accounts banned. Kept the existing anime tab
  (personal use) but steered the product to legal **Stock** + **Upload** paths.

---

## What Was Done — 2026-07-04 (Devin, session 1: Instagram Reel Creator)

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
