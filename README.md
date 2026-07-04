# 🤖 REEL GOD — Setup Guide

## Step 1: Install Python (Required First!)

Python is not installed on your PC yet. Here's how to get it:

### Option A — Direct Download (Recommended)
1. Go to: **https://www.python.org/downloads/**
2. Download **Python 3.11** (click the yellow button)
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box that says **"Add Python to PATH"** before clicking Install
5. Click "Install Now"

### Option B — Microsoft Store
1. Open Microsoft Store
2. Search "Python 3.11"
3. Click Get/Install

### Verify Installation
Open a new PowerShell window and type:
```
python --version
```
You should see: `Python 3.11.x`

---

## Step 2: Get Your FREE Gemini API Key

1. Open this link: **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (it looks like: `AIzaSy...`)
5. Keep it safe — you'll enter it in the next step

> 💡 It's 100% free. No credit card. 1,500 requests/day free.

---

## Step 3: Open the Project in PowerShell

```powershell
cd C:\Users\Admin\.gemini\antigravity\scratch\reel-god
```

---

## Step 4: Run First-Time Setup

```powershell
python setup_first_time.py
```

This will:
- Ask for your Gemini API key and test it
- Check your system (GPU, FFmpeg, etc.)
- Install all dependencies automatically
- Create your `.env` config file

---

## Step 5: Start REEL GOD

```powershell
python main.py
```

That's it! REEL GOD will:
1. Do a morning briefing
2. Generate 3 content ideas
3. Start running 24/7 in the background
4. Open dashboard at **http://localhost:5000**

---

## Daily Commands

| Command | What it does |
|---------|-------------|
| `python main.py` | Start 24/7 agent |
| `python main.py --ideas` | Generate ideas right now |
| `python main.py --chat` | Chat with REEL GOD |
| `python main.py --status` | Check agent status |
| `python main.py --plan` | See weekly content plan |
| `python main.py --system-check` | Check GPU & system |

---

## Install FFmpeg (For Video Assembly)

1. Go to: **https://www.gyan.dev/ffmpeg/builds/**
2. Download: `ffmpeg-release-full.7z`
3. Extract it to `C:\ffmpeg`
4. Add `C:\ffmpeg\bin` to your PATH:
   - Search "Environment Variables" in Start Menu
   - Click "Environment Variables"
   - Under System Variables, find "Path" → Edit
   - Add new entry: `C:\ffmpeg\bin`
   - Click OK

---

## Project Location

```
C:\Users\Admin\.gemini\antigravity\scratch\reel-god\
```

Set this as your active workspace in Antigravity to see all files.

---

## What's Built So Far

✅ **Phase 1 — Brain Core** (Complete)
- `brain/core.py` — Main reasoning engine (Gemini 2.5 Flash)
- `brain/memory.py` — SQLite persistent memory
- `brain/planner.py` — Content idea generator & weekly planner
- `brain/personality.py` — REEL GOD's identity & anime knowledge
- `utils/gpu_check.py` — Auto hardware detection
- `main.py` — Full CLI entry point
- `setup_first_time.py` — Setup wizard

🔜 **Phase 2** — Image & Video Generation (ComfyUI + FFmpeg)
🔜 **Phase 3** — Music Intelligence (Jamendo API)
🔜 **Phase 4** — Instagram Integration
🔜 **Phase 5** — Self-Learning Engine
🔜 **Phase 6** — Command Dashboard (Web UI)
