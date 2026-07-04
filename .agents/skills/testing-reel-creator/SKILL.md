---
name: testing-reel-creator
description: Test the REEL GOD "Instagram Reel Creator" dashboard end-to-end (photo/video upload → Reel/Post/Story with multi-genre music). Use when verifying Reel Creator UI or the compose pipeline.
---

# Testing the Instagram Reel Creator

End-to-end test of the dashboard Creator panel: upload media → pick format/style/genre →
Create → verify a new item lands in the archive with correct video properties.

## Prerequisites / setup
- Start the dashboard: `cd <repo> && . .venv/bin/activate && python -m dashboard.app`
  (it binds `0.0.0.0:5000`; startup can take ~10s while the Gemini brain initializes).
- Health check: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login` → expect `200`.
- Login password = `COMMANDER_PASSWORD` env (default `admin`).
- A ready-made test image lives at `data/uploads/test_photo.jpg`. If missing, create one:
  `python -c "from PIL import Image; Image.new('RGB',(1280,720),(30,30,60)).save('data/uploads/test_photo.jpg')"`

## Fast, reliable path (avoids external flakiness)
- Choose **Upload Photo/Video** (not "From Anime") — the anime path fetches from YouTube, which
  **blocks datacenter/VM IPs** ("confirm you're not a bot"). It may work on residential IPs or with
  `YTDLP_COOKIES_FILE` / `YTDLP_COOKIES_FROM_BROWSER` set, but do not rely on it in CI/VM.
- Pick **Style = Motivational** — motivational music is usually cached in `data/music_library/`
  (`motivational_testcache.mp3`), so the "select music" stage doesn't need a live download.
- Gemini free tier caps at ~20 req/day; when exhausted the narrative falls back to a built-in
  template (log line: "Narrative AI unavailable ... using template"). This is expected, not a failure.

## UI flow
1. Header button "🎬 Instagram Reel Creator" opens the panel (confirm no legacy "Instagram Link" button).
2. Click the "📤 Upload Photo / Video" tab → drop-zone appears.
3. Clicking the drop-zone opens a native GTK file dialog. Fastest selection: press `Ctrl+L` and type
   the absolute path (e.g. `/home/ubuntu/repos/reel-god-actual/data/uploads/test_photo.jpg`) then Enter.
   Drop-zone should read "✓ <name> (image) ready".
4. Set Format (Reel 9:16 / Post 1:1 / Story 9:16), Mood/Style, Music Genre (auto + 7 genres).
5. Click "✨ Create". A progress bar advances: Scripting → Converting → Selecting music → Composing →
   Rendering → Saving. Button shows "⏳ Creating...".
6. On completion the page auto-reloads; the new item appears in "Compiled Reels Archive" and the
   "Total Posts" counter increments.

## Verification (objective)
- Find the newest output: `find data/content_archive -name '*.mp4' -mmin -5`.
- **IMPORTANT**: rendering on a CPU-only VM is slow (~100s). The mp4's `moov` atom is written LAST,
  so `ffprobe` returns "moov atom not found" until the mux fully finishes. Poll until it succeeds
  rather than concluding failure. Example poll loop:
  ```bash
  for i in $(seq 1 30); do ffprobe -v error -show_entries stream=width,height -of csv=p=0 "$F" && break; sleep 10; done
  ```
- Expected properties by format: Reel/Story = `1080x1920`, Post = `1080x1080`; codec `h264` + audio `aac`.
- Image uploads run through `image_to_base_video()` which rounds scaled dims to even numbers to keep
  x264 happy — if you see "width/height not divisible by 2" that guard regressed.

## Testing the "Stock (royalty-free)" source (Pexels/Pixabay)
- The Stock tab reads its state from `config.stock_sources_available()`, which only sees keys that
  were in the environment **when the Flask process started**. If you add `PEXELS_API_KEY` /
  `PIXABAY_API_KEY` mid-session you MUST restart the dashboard for the tab to activate — otherwise it
  keeps showing the ⚠️ "no source configured" warning. Restart, then reload the page.
- No-key checks (no restart needed): the Stock tab shows a ⚠️ warning, and clicking Create logs
  `Creator failed to start: No royalty-free stock source configured` in the console — a handled
  error, not a crash. Good graceful-degradation assertions.
- Live golden path: type a directive (e.g. "sunrise over mountains") → Create. Watch the backend log
  for `Downloading stock media: pixabay_<id>` / `✓ Stock media ready: ...`. Pixabay/Pexels are
  reachable from datacenter VMs (unlike YouTube), so this path actually works in CI/VM.
- Stock HD sources can be large (tens of MB), so the re-encode is slower than an image upload — poll
  the output file rather than assuming failure.
- **Music caveat:** the fetch order is Jamendo CC → YouTube → smart matcher → SoundHelix. Without
  `JAMENDO_CLIENT_ID` (Jamendo skips gracefully) and with YouTube blocked on the VM, music falls back
  to a static SoundHelix track. That's expected; add `JAMENDO_CLIENT_ID` to verify CC music.

## Recording tips
- Maximize the window first: `wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz`.
- Do login BEFORE starting the recording (it's setup, not a test assertion).
- Annotate: setup (logged in), test_start per test, and consolidated assertions
  (panel opens w/ genres; photo uploaded; pipeline runs; new Post saved + count increments).

## Devin Secrets Needed
- `GEMINI_API_KEY` — for AI narrative/captions. Optional for a smoke test (template fallback covers it),
  but needed to verify real AI-authored scripts.
- (Optional) `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` — free keys that enable the "Stock
  (royalty-free)" source. Pixabay is reachable from VMs, so this is the best live end-to-end path.
- (Optional) `JAMENDO_CLIENT_ID` — free key to verify Creative-Commons music (else music falls back
  to a static SoundHelix track on the VM).
- (Optional) `YTDLP_COOKIES_FILE` / `YTDLP_COOKIES_FROM_BROWSER` — only to test the "From Anime"
  internet-fetch path from a server.
