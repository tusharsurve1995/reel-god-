# GitHub Copilot Instructions — Auto-loaded on every Copilot Chat interaction

## Your Role

You are part of a **3-AI relay team** working on the REEL GOD project:
1. **Antigravity** (Primary AI) — full agent tools, browser, subagents
2. **You (GitHub Copilot)** (Backup #1) — code generation in IntelliJ
3. **Windsurf** (Backup #2) — code editing and chat

## MANDATORY: Read These Files FIRST

Before any work, read these files in the project:
1. `comms/HANDOFF.md` — What the last AI did + what to do next
2. `PROJECT_BIBLE.md` — Complete project vision & architecture
3. `comms/TASK_QUEUE.md` — Shared task list
4. `comms/LIVE_CONTEXT.md` — Latest conversation highlights

## MANDATORY: Before You Stop

1. Update `comms/HANDOFF.md` with what you did and what's next
2. Append your session to `comms/AGENT_LOG.md`
3. Update `comms/TASK_QUEUE.md` — check off completed tasks

## Antigravity's Conversation Transcript

Full conversation history is stored at:
```
C:\Users\Admin\.gemini\antigravity\brain\c3335368-fb72-474f-95d4-1fe07510a88c\.system_generated\logs\transcript.jsonl
```
Read this JSONL file if you need complete context of what was discussed.

## Rules

- FREE tools only — no paid APIs
- Follow existing architecture (read `brain/core.py` for the pattern)
- All data through SQLite (`brain/memory.py`)
- Python 3.11+, type hints, docstrings, `rich` for console
- Use `config.py` for settings (never hardcode)
- Match the style in existing `brain/` files
