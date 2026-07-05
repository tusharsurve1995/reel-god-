# 🤖 REEL GOD — AI Agent Development & Deployment Log

This document serves as a handoff log for any AI coding assistant (Antigravity, Windsurf, Devin, etc.) working on the **REEL GOD** project. It details the project's state, active repository, configurations, architectural decisions, and current deployment status.

---

## 📌 1. Repository & Deployment Information

* **Active Repository**: `https://github.com/tusharsurve1995/reel-god-` (⚠️ **NOTE**: Must include the trailing hyphen `-`). The repository `reel-god` (without the hyphen) is outdated and unused.
* **Production Cloud Host**: Deployed on **Render** (https://render.com) using the Infrastructure-as-Code `render.yaml` Blueprint file.
  * **Build Command**: `pip install -r requirements.txt`
  * **Start Command**: `gunicorn --worker-class eventlet -w 1 dashboard.app:app --bind 0.0.0.0:$PORT --timeout 600`
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
