# REEL GOD — Content Sources & How to Verify

This guide explains the **new royalty-free sources**, how to turn them on, how to
**check everything is working**, and what it takes to ship REEL GOD as a real
**agent** or a **downloadable application**.

---

## 1. Where REEL GOD gets its media now

The Instagram Reel Creator can build a Reel / Post / Story from **three** sources:

| Tab | What it does | Copyright | Works on a server? |
|-----|--------------|-----------|--------------------|
| 🌸 **From Anime (internet)** | Downloads anime clips from YouTube via `yt-dlp` | ⚠️ Copyrighted — for personal experiments only | Only with YouTube cookies (datacenter IPs are bot-blocked) |
| 🎥 **Stock (royalty-free)** *(NEW)* | HD video/photos from **Pexels** + **Pixabay** | ✅ Free to reuse & repost | ✅ Yes — no bot-blocking |
| 📤 **Upload Photo / Video** | Your own file → Reel/Post/Story | ✅ You own it | ✅ Yes |

**Music** now prefers **Jamendo** (Creative-Commons, legal, works on servers)
before falling back to YouTube search and then a built-in track. All 8 genre
choices still work: Auto, Bollywood, Hollywood, Pop, Instrumental, Action,
Romantic, Worldwide.

> ⚖️ **Important honesty note:** downloading full copyrighted anime (or using
> modified apps like ReVanced/Vanced to bypass YouTube Premium) and reposting it
> to Instagram is copyright infringement — Instagram auto-detects it and can take
> down posts or ban the account. The **Stock** and **Upload** tabs are the safe,
> reliable way to publish. The anime tab is kept for personal/offline use.

---

## 2. Turn on the free sources (one-time, 5 minutes)

All keys are **100% free** (no credit card):

1. **Pexels** — sign up at <https://www.pexels.com/api/>, copy your API key.
2. **Pixabay** — log in, open <https://pixabay.com/api/docs/>, copy the key shown.
3. **Jamendo** (music) — create a free app at <https://devportal.jamendo.com>, copy the *Client ID*.

Then set them as environment variables (or paste into a `.env` file next to `config.py`):

```bash
# .env  (same folder as config.py)
PEXELS_API_KEY=your_pexels_key_here
PIXABAY_API_KEY=your_pixabay_key_here
JAMENDO_CLIENT_ID=your_jamendo_client_id_here
```

Restart the dashboard after adding keys. If a key is missing, that source simply
turns off — the app keeps working with the sources you *do* have.

---

## 3. How to check everything is working ✅

### A. Quick automated check (copy-paste into a terminal)

From the project folder, with the virtualenv active:

```bash
python -c "import config; print('Stock sources ON:', config.stock_sources_available())"
```
- Prints `['pexels', 'pixabay']` if both keys are set (or a subset, or `[]` if none).

```bash
python -c "from generator.stock_fetcher import StockFetcher; \
p=StockFetcher().fetch_video('sunrise over mountains'); print('Got clip:', p)"
```
- Prints a real file path under `data/stock_clips/…mp4` → **stock video works**.
- Prints `None` with no key → expected (add a key first).

```bash
python -c "from music.music_fetcher import MusicFetcher; \
p=MusicFetcher().fetch_by_genre('instrumental','emotional'); print('Music:', p)"
```
- Prints an `.mp3` path (a `jamendo_…mp3` if the Jamendo key is set) → **music works**.

### B. Full check through the dashboard (the real test)

1. Start it: `python -m dashboard.app` → open <http://localhost:5000>, log in (password `admin`).
2. Click **🎬 Instagram Reel Creator**.
3. Click the **🎥 Stock (royalty-free)** tab.
   - Green “✅ Sources ready: pexels, pixabay” = keys detected.
   - Yellow “⚠️ No stock source configured” = add a key and restart.
4. Pick **Format** (Reel / Post / Story), a **Mood/Style**, a **Music Genre**,
   and optionally type a directive like `sunrise over mountains`.
5. Click **✨ Create**. Watch the progress bar go Scripting → Fetching → Music →
   Composing → Saving. When done the page reloads and a new item appears in the
   **Compiled Reels Archive** and the **Total Posts** count goes up.
6. **Prove the file is correct** (optional, in a terminal):
   ```bash
   # newest output
   F=$(ls -t data/content_archive/*.mp4 | head -1)
   ffprobe -v error -show_entries stream=codec_name,width,height -of default=nw=1 "$F"
   ```
   Expected: `h264`, and `1080x1920` for Reel/Story or `1080x1080` for Post, with an `aac` audio stream.

### C. What "good" looks like
- **Stock tab** produces a video even with no upload and no anime.
- **Music** comes from Jamendo (legal) when its key is set — check the console log for `Jamendo [...]`.
- Removing all keys still lets **Upload** work — nothing hard-crashes.

---

## 4. Do you want this as an **Agent** or an **Application**?

Both are possible from this same codebase. Here's the plain-English difference and
what each needs.

### Option A — Autonomous **Agent** (runs itself 24/7)
REEL GOD already has the "brain" (`brain/core.py`, `planner.py`, `memory.py`). To
make it a true always-on agent:
- **Scheduler**: run the planner on a timer (the config already has
  `DAILY_POSTING_HOURS`). Use a background loop, `cron`, or a service like
  `systemd` / Windows Task Scheduler.
- **Auto-publish**: finish the Instagram publishing path (`instagram/publisher.py`)
  with the Instagram Graph API (needs a Meta app + a Business/Creator account).
- **Approval gate**: per your project rule "agent suggests, commander approves" —
  keep a review step (e.g. a Telegram/dashboard "Approve" button) before it posts.
- **Hosting**: a small always-on box (a mini PC at home, or a cheap VPS). Note
  the anime/YouTube path needs residential IP or cookies; the **stock** path works
  anywhere.

*Best if:* you want it to plan, create, and (after approval) post on its own.

### Option B — Distributable **Application** (you click a button)
Package the dashboard so anyone can install and run it:
- **Desktop app**: wrap the Flask dashboard with **PyInstaller** (one `.exe` /
  `.app`) or **pywebview** for a native window. Ship `ffmpeg` alongside it.
- **Web app**: deploy the Flask + Socket.IO server (Render, Railway, Fly.io, or a
  VPS with `gunicorn`+`eventlet`). Add real user accounts instead of the single
  `admin` password.
- **Config UI**: add a Settings screen so users paste their own API keys instead
  of editing `config.py`.

*Best if:* you (or others) want a tool to open and create reels on demand.

### Recommended next step
Start with **Option B (desktop app via PyInstaller)** — it's the smallest jump
from what exists today and gives you a clickable product. Layer on the **Agent**
scheduler/auto-post later once the Instagram Graph API app is approved.

---

*Questions or want me to build one of these? Just ask REEL GOD's dev (Devin).* 
