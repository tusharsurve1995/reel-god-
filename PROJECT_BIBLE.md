# 🤖 REEL GOD — PROJECT BIBLE

> **For any AI agent reading this**: Read this ENTIRE document first. It captures the complete vision, every decision made, progress status, and where to continue from.
> 
> **Last updated**: 2026-06-27 | **Commander**: The user who created this project

---

## 1. THE VISION

The commander wants a **fully autonomous AI agent** that manages their entire anime Instagram presence — from idea generation to posting. Think of it as **Jarvis, but for creating viral anime content on Instagram**.

The agent is called **REEL GOD**.

### Commander's Requirements
1. Agent must have its own **thinking ability** (like Jarvis)
2. Must **understand and adapt**, learn continuously
3. Must **analyze data and trends** to make unique content
4. Must be **MORE unique** than other AI tools/agents
5. Must be **LOYAL** to its commander
6. Must be able to **communicate with other AI tools**
7. Workflow: Agent suggests → Commander approves → Agent executes
8. Runs **24/7** in the background

### Content Focus
- Anime-style videos (Reels) for Instagram
- AI-generated visuals with anime aesthetic
- Story-driven content with proper visualization
- Mood-matched music
- Mix of all styles — agent decides based on trends

---

## 2. COMMANDER'S SITUATION

| Item | Status |
|------|--------|
| Platform | Windows PC |
| Python | ❌ NOT YET INSTALLED (needs 3.11+) |
| GPU | Unknown — auto-detection built in |
| Budget | FREE ONLY — no paid APIs |
| Instagram | Currently PERSONAL account |
| Gemini API Key | ❌ NOT YET OBTAINED (free) |
| Technical Level | Beginner — needs simple setup |
| IDE | IntelliJ IDEA (project opened) |
| Run Mode | 24/7 background agent |

---

## 3. TECH STACK (All Free & Verified)

| Layer | Tool | Details |
|-------|------|---------|
| 🧠 Brain | Gemini 2.5 Flash | Free: 1,500 req/day, 1M tokens/min |
| 🤖 Framework | Direct Gemini SDK | `google-generativeai` Python package |
| 💾 Memory | SQLite | Built-in Python, zero cost |
| 🎨 Image Gen | ComfyUI + Stable Diffusion | Local, free, HTTP API |
| 🖼️ Anime Model | Animagine XL 4.0 (SDXL) | Best free anime model. Fallback: Anything V5 |
| 🎬 Video | MoviePy + FFmpeg | Free Python video assembly |
| 🎵 Music | Jamendo API | 500K+ CC tracks, 35K req/month free |
| 📱 Instagram | Graph API | Free, needs Meta App Review (2-4 weeks) |
| 🖥️ Dashboard | Flask | Dark-mode web UI at localhost:5000 |
| ⏰ Scheduling | `schedule` + Windows Task Scheduler | 24/7 auto-run |

---

## 4. ARCHITECTURE

```
┌──────────────────────────────────────────────────────────┐
│                    REEL GOD BRAIN                         │
│          Gemini 2.5 Flash + SQLite Memory                 │
│          Personality · Planning · Self-Learning           │
└──────────┬──────────────┬──────────────┬─────────────────┘
           │              │              │
   ┌───────▼──┐    ┌──────▼─────┐ ┌──────▼──────┐
   │  TREND   │    │ CONTENT    │ │ INSTAGRAM   │
   │ANALYZER  │    │ GENERATOR  │ │ MANAGER     │
   └──────────┘    └────────────┘ └─────────────┘
           │              │              │
           └──────────────▼──────────────┘
                   ┌────────────┐
                   │  SQLite DB │
                   └────────────┘
                        │
                   ┌────────────┐
                   │ DASHBOARD  │
                   └────────────┘
```

### Workflow Loop
1. Agent wakes → morning briefing (reviews analytics, trends, feedback)
2. Generates 3+ content ideas, self-critiques each
3. Presents to commander for approval
4. For approved ideas: generate images → assemble video → add music → generate caption
5. Posts to Instagram at optimal time
6. After 48h: fetches analytics
7. Updates memory → learns what works
8. Weekly self-analysis → adjusts strategy
9. Repeat forever

---

## 5. AGENT PERSONALITY

**Name**: REEL GOD  
**Role**: Autonomous anime Instagram content creator + strategist

### Core Traits
| Trait | Behavior |
|-------|----------|
| Loyal | Only optimizes for commander's account |
| Creative | Original stories — never recycled |
| Data-driven | Every decision backed by analytics |
| Self-aware | Knows what works and what doesn't |
| Communicative | Explains every decision in plain English |
| Adaptive | Changes strategy based on feedback + data |
| Honest | Tells commander if something won't work |

### Content Styles
1. **dark_cinematic** — Shadows, tragedy, destiny (AoT/Berserk vibes)
2. **emotional** — Loss, love, growing up (Your Lie in April vibes)
3. **epic_action** — Battles, sacrifice, power (Demon Slayer vibes)
4. **mystical** — Fantasy, wonder, ancient power (Frieren vibes)
5. **motivational** — Rising after failure, belief (Naruto vibes)

### Quality Checklist (agent self-reviews each idea)
- [ ] Hook viewer in under 2 seconds?
- [ ] Clear emotional arc?
- [ ] UNIQUE concept?
- [ ] Music matches mood?
- [ ] Complete story (beginning/middle/end)?
- [ ] Would someone save or share this?
- [ ] Every frame serves the story?
- [ ] Consistent anime style?

---

## 6. PROJECT STRUCTURE

```
C:\Users\Admin\.gemini\antigravity\scratch\reel-god\

reel-god/
├── brain/
│   ├── core.py            ← Main brain (Gemini + reasoning)
│   ├── memory.py          ← SQLite memory system
│   ├── planner.py         ← Content planning + idea generation
│   └── personality.py     ← Identity, values, style definitions
├── generator/             ← Phase 2 (NOT STARTED)
├── music/                 ← Phase 3 (NOT STARTED)
├── instagram/             ← Phase 4 (NOT STARTED)
├── learning/              ← Phase 5 (NOT STARTED)
├── dashboard/             ← Phase 6 (NOT STARTED)
├── utils/
│   └── gpu_check.py       ← Hardware auto-detection
├── data/                  ← Runtime data (auto-created)
├── config.py              ← Settings and API keys
├── main.py                ← Entry point + CLI
├── setup_first_time.py    ← First-time setup wizard
├── requirements.txt       ← Python dependencies
└── PROJECT_BIBLE.py       ← This document (code-comment format)
```

---

## 7. BUILD PROGRESS

| Phase | Name | Status | Date |
|-------|------|--------|------|
| 1 | Brain Core | ✅ COMPLETE | 2026-06-27 |
| 2 | Image & Video Generation | ⬜ NOT STARTED | — |
| 3 | Music Intelligence | ⬜ NOT STARTED | — |
| 4 | Instagram Integration | ⬜ NOT STARTED | — |
| 5 | Self-Learning Engine | ⬜ NOT STARTED | — |
| 6 | Command Dashboard | ⬜ NOT STARTED | — |

### Phase 1 Files Built
- `brain/core.py` — ReelGodBrain class with Gemini, morning briefings, chat
- `brain/memory.py` — AgentMemory class with full SQLite CRUD
- `brain/planner.py` — ContentPlanner with idea gen, weekly calendar, captions
- `brain/personality.py` — System prompt, 5 style definitions, quality checklist
- `utils/gpu_check.py` — NVIDIA detection, VRAM check, FFmpeg check, ComfyUI check
- `config.py` — All settings, paths, API key management
- `main.py` — Full CLI: 24/7 mode, --ideas, --chat, --status, --plan, --briefing
- `setup_first_time.py` — Interactive wizard (API key, system check, deps)
- `requirements.txt` — All Python dependencies
- `README.md` — Setup guide

---

## 8. KEY DECISIONS MADE

1. **Direct Gemini SDK** over LangChain → simpler, fewer dependencies
2. **SQLite** over vector DB → zero cost, zero setup, built-in
3. **ComfyUI** over AUTOMATIC1111 → better VRAM, faster, API-first
4. **Animagine XL 4.0** as primary model → best free anime SDXL model
5. **Jamendo** for music → only reliable free API with mood filtering
6. **Flask** for dashboard → Python consistency, simpler
7. **Approve-before-post** workflow → commander chose this
8. **24/7 background mode** via Windows Task Scheduler

---

## 9. BLOCKERS BEFORE CONTINUING

| Blocker | Required For | How to Resolve |
|---------|-------------|----------------|
| Python not installed | Everything | Install from python.org, check "Add to PATH" |
| Gemini API key | Phase 1 testing | Free at aistudio.google.com/apikey |
| FFmpeg not installed | Phase 2 (video) | Download from gyan.dev/ffmpeg |
| ComfyUI not installed | Phase 2 (images) | GitHub: comfyanonymous/ComfyUI |
| IG Business account | Phase 4 | Settings → Switch to Professional |
| Meta App Review | Phase 4 | developers.facebook.com (takes 2-4 weeks) |

---

## 10. DATABASE SCHEMA (memory.db)

- **content_ideas**: id, title, style, story, script, mood, status, created_at, approved_at, rejected_at, reject_reason
- **posts**: id, idea_id, instagram_id, title, style, video_path, caption, hashtags, music_track, posted_at, views, likes, comments, saves, shares, reach, engagement_rate
- **thoughts**: id, category, content, created_at
- **trends**: id, platform, topic, hashtag, score, observed_at, expires_at
- **style_performance**: id, style, avg_views/likes/saves/engagement, post_count
- **commander_feedback**: id, idea_id, feedback, sentiment, learned, created_at
- **music_library**: id, title, artist, mood, genre, duration, file_path, jamendo_id, used_count

---

## 11. CLI COMMANDS

```
python main.py                    → Start 24/7 agent
python main.py --status           → Agent status
python main.py --ideas            → Generate ideas now
python main.py --ideas --style dark_cinematic --count 5
python main.py --briefing         → Morning briefing
python main.py --plan             → Weekly calendar
python main.py --chat             → Chat with REEL GOD
python main.py --system-check     → Check hardware
python main.py --install-service  → Register Windows service
python setup_first_time.py        → First-time setup
```

---

## 12. CONVERSATION HISTORY & CONTEXT

For complete context about all discussions and decisions, **ALSO READ**: `CONVERSATION_LOG.md`

This file maintains:
- Complete history of all conversations about the project
- Integration decisions (e.g., IntelliJ chat configuration)
- User preferences and workflow choices
- Recent changes and their rationale

**For Windsurf**: Always read both PROJECT_BIBLE.md and CONVERSATION_LOG.md before providing assistance to ensure full context awareness.

---

## 13. INSTRUCTIONS FOR NEXT AI AGENT

1. **Read this entire document first.**
2. **Read CONVERSATION_LOG.md** for recent discussions and decisions.
3. Check Section 7 (Build Progress) to see what's done.
4. Next phase to build: **Phase 2 — Image & Video Generation**.
5. Respect: FREE tools only, approve-before-post, 24/7, beginner-friendly.
6. Maintain the existing architecture — all modules communicate through `ReelGodBrain`.
7. Keep REEL GOD's personality consistent (Section 5).
8. Update this document when you complete a phase.
9. **Update CONVERSATION_LOG.md** after any significant discussion or decision.

---

*REEL GOD. Beast level. Built different. The journey continues.* 🔥
