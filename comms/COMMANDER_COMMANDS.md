# 🎮 COMMANDER'S QUICK COMMAND CARD

> **How to switch between your 3 AI agents seamlessly.**
> Keep this file open. Copy-paste the commands below when switching AIs.

---

## Your AI Team

| Priority | Agent | Where | Best For |
|----------|-------|-------|----------|
| 1st | **Antigravity** | Antigravity 2.0 app | Full agent: browser, subagents, tools, planning |
| 2nd | **GitHub Copilot** | IntelliJ → Copilot Chat | Fast code generation, inline edits |
| 3rd | **Windsurf** | Windsurf IDE | Code editing, chat, file management |

---

## 🔄 HOW TO SWITCH

### When Antigravity runs out of tokens:
Open **GitHub Copilot Chat** in IntelliJ and paste:

```
Read the file comms/HANDOFF.md in this project. It contains 
instructions from the previous AI agent. Also read PROJECT_BIBLE.md 
for full project context. Continue the work from where the previous 
agent stopped. When you finish or run out of tokens, update 
comms/HANDOFF.md with what you did and what's next, and append 
your session to comms/AGENT_LOG.md.
```

---

### When GitHub Copilot runs out of tokens:
Open **Windsurf** with this project and paste:

```
Read the file comms/HANDOFF.md in this project. It contains 
instructions from the previous AI agent. Also read PROJECT_BIBLE.md 
for full project context. Continue the work from where the previous 
agent stopped. When you finish or run out of tokens, update 
comms/HANDOFF.md with what you did and what's next, and append 
your session to comms/AGENT_LOG.md.
```

---

### When Windsurf runs out / all agents refresh:
Come back to **Antigravity** and paste:

```
Read comms/HANDOFF.md in my reel-god project. Other AI agents 
(Copilot/Windsurf) have been working on it. Read their handoff notes 
and AGENT_LOG.md to see what was done. Continue from where they stopped. 
Check comms/TASK_QUEUE.md for the current task list.
```

---

## 🔁 THE CYCLE

```
Antigravity → (runs out) → GitHub Copilot → (runs out) → Windsurf
     ↑                                                        │
     └────────────── (all refresh, cycle back) ←───────────────┘
```

Each AI reads HANDOFF.md → does work → updates HANDOFF.md → next AI continues.
**Work never stops. The project keeps moving forward.**

---

## 📂 Communication Files (comms/ folder)

| File | Purpose | Who Updates It |
|------|---------|---------------|
| `PROTOCOL.md` | Rules for all AIs | Don't change |
| `HANDOFF.md` | Current context + what to do next | Every AI before stopping |
| `TASK_QUEUE.md` | Shared TODO list | Every AI as they complete tasks |
| `AGENT_LOG.md` | Timeline of all sessions | Every AI appends |
| `PROJECT_BIBLE.md` | Full project vision & context | Update when phases complete |

---

## ⚡ Quick Commands for Specific Tasks

### "Generate Phase 2 code"
```
Read comms/HANDOFF.md and PROJECT_BIBLE.md. Build Phase 2: Image & 
Video Generation. Create all files in the generator/ directory. 
See TASK_QUEUE.md for the specific files needed.
```

### "Fix a bug"
```
Read PROJECT_BIBLE.md for project context. There's a bug in [file]. 
[Describe bug]. Fix it and update comms/AGENT_LOG.md with what you fixed.
```

### "Add a new feature"
```
Read PROJECT_BIBLE.md for project context. I want to add [feature]. 
Follow the existing architecture. Update TASK_QUEUE.md and AGENT_LOG.md.
```

---

## 🛠️ Setup Checklist (One-Time)

- [ ] **Antigravity**: Already working ✅
- [ ] **GitHub Copilot**: Install JetBrains plugin → Settings → Plugins → search "GitHub Copilot" → Install → Restart IntelliJ → Sign in to GitHub
- [ ] **Windsurf**: Download from https://codeium.com/windsurf → Install → Open this project folder
