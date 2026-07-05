# 🤖 REEL GOD — AI Agent Development & Deployment Log

This document serves as the central handoff log for any AI coding assistant (Antigravity, Windsurf, Devin, etc.) working on the **REEL GOD** project. 

---

## ⚠️ CRITICAL RULES FOR INCOMING AI ASSISTANTS

Every AI assistant taking over this codebase **MUST** strictly adhere to the following workflow:

1. **READ BEFORE STARTING**: Before making any source code changes or running commands, read this document and `docs/STORYBOARD_TRACKER.md` fully. Understand the active repository and the architecture constraints (e.g. FFmpeg vs MoviePy, SQLite schema, mobile PWAs).
2. **DOCUMENT YOUR WORK**: As you implement changes, update this log. Add a entry under the **Changelog** section detailing exactly what you changed, why you changed it, and how it improves the system.
3. **PUSH TO GIT BEFORE LEAVING**: Before completing your turn/session, stage all files, write a clear descriptive commit message, and push your changes to the active GitHub repository (`https://github.com/tusharsurve1995/reel-god-`). Do not leave unstaged or uncommitted code behind.
4. **SAFETY FIRST**: Always verify syntax correctness (e.g., `py -m py_compile`) and test the dashboard server locally before pushing. Prevent encoding crashes in Windows terminals by keeping console logs plain-text/ASCII-friendly.

---

## 📌 1. Repository & Deployment Information

* **Active Repository**: `https://github.com/tusharsurve1995/reel-god-` (⚠️ **NOTE**: Must include the trailing hyphen `-`). The repository `reel-god` (without the hyphen) is outdated and unused.
* **Production Cloud Host**: Deployed on **Render** (https://render.com) using the Infrastructure-as-Code `render.yaml` Blueprint file.
  * **Production URL**: `https://reel-god.onrender.com` (Use this for daily mobile access!)
  * **Build Command**: `pip install -r requirements.txt`
  * **Start Command**: `python dashboard/app.py`
  * **Environment Variable Requirements**: Requires `GEMINI_API_KEY` set in the Render environment settings.

---

## ⚙️ 2. Architectural Blueprint

### A. Video Render Pipeline (`fast_generate.py`)
* Replaced `MoviePy` with a direct, native `FFmpeg` command line generator.
* **Why?** MoviePy ran visual filters in single-threaded Python space, leaking memory (~1.5 GB RAM) and causing process hangs.
* **FFmpeg Pipeline advantages**: Uses only ~100 MB RAM, compiles 1080x1920 (HD+) videos in under 30 seconds, automatically wraps overlay text to prevent screen cutoffs, and normalizes audio track volume to **-14 LUFS** (Instagram broadcast standard).

### B. Command Dashboard (`dashboard/`)
* **Backend (`dashboard/app.py`)**: Flask + Socket.IO server running on port `5000`. Set up with cross-origin access enabled to allow network accessibility.
* **Frontend Mobile Optimization (`dashboard/templates/index.html` & `app.js`)**:
  * Configured as a **Progressive Web App (PWA)** via `manifest.webmanifest` and `sw.js` so it can be installed on iOS/Android home screens as a full-screen, native-feeling app.
  * **Socket.IO Transport**: Client socket connection is explicitly locked to `transports: ['websocket']`. This prevents mobile Chrome from displaying a spinning "loading" state caused by long-polling HTTP requests.
  * **Windows Terminal Fix**: Removed console emojis and added `os.environ["PYTHONIOENCODING"] = "utf-8"` in `app.py` and `brain/core.py` to prevent `UnicodeEncodeError` crashes on Windows host consoles.

### C. Storyboard & Posting Tracker (`docs/STORYBOARD_TRACKER.md` + DB Schema)
* The database (`brain/memory.py`) contains a safe SQLite migration adding `feedback` (TEXT) and `is_posted` (INTEGER/BOOLEAN) columns.
* The dashboard features an interactive **Storyboard & Posting Tracker** where the Commander can:
  * Check posting status (`Draft` vs `Posted`).
  * Enter views, likes, comments, and saves metrics.
  * Write text notes / audience feedback.
  * Read **Instagram Audio Recommendations** derived from the local audio file name to search for the matching music track in the Instagram app.

### D. Personality & Theme Directive
* The agent is strictly locked to generating **Motivational Anime** content (focusing on rise-from-failure stories, determination, e.g., Naruto, Rock Lee, Deku).
* Configuration restricted via `config.py` (`CONTENT_STYLES = ["motivational"]`) and updated system prompt rules in `brain/personality.py`.

---

## 🛠️ 3. Current Work Status & Action Items

- [x] Redesign Dashboard UI to include Storyboard & Posting Tracker.
- [x] Configure PWA and Socket.IO for mobile browser deployment.
- [x] Enable 24/7 Cloud Deployment on Render.
- [ ] **Next Step: ComfyUI Asset Generation Integration**
  - Connect `fast_generate.py` with ComfyUI API to automatically generate anime images/clips based on generated prompts.
- [ ] **Next Step: Instagram Publishing API**
  - Enhance the "Direct Post to IG" button to automate uploading when Instagram credentials are saved.
- [ ] **Next Step: Self-Learning Loop**
  - Write a background processor that queries the SQLite database to analyze post engagement rates (Views vs. Likes/Saves) entered by the commander, adapting future script generation based on what goes viral.

---

## 📜 4. Handoff History & Changelog

### July 5, 2026 (Antigravity Agent)
* **Mobile & Cloud Deployment**: Configured and deployed the application to Render via `render.yaml` (Blueprint) pointing to the active repository `tusharsurve1995/reel-god-`. Resolved Gunicorn+Eventlet entrypoint loader failures on Render by simplifying the start command to direct execution via `python dashboard/app.py`.
* **Mobile UX (Socket.IO Fix)**: Forced the Socket.IO client in `app.js` to connect using pure `websocket` transport, preventing infinite browser page loading spin on mobile Chrome.
* **Storyboard Tracker UI**: Redesigned the "Compiled Reels Archive" template block into a glassmorphic Storyboard Tracker. Created a new SQLite migration inside `brain/memory.py` to support `is_posted` and `feedback` storage. Added interactive views/likes/saves/comments and notes saving capabilities to feed the self-learning loops.
* **Console Safety**: Fixed a `UnicodeEncodeError` crash during server launch on Windows consoles by configuring `PYTHONIOENCODING=utf-8` on process boot and sanitizing terminal Panel emojis.
* **Handoff Rules**: Defined strict rules requiring incoming assistants to read logs first, document their updates, verify stability, and push to GitHub before ending their turn.
