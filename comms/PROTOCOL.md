# ═══════════════════════════════════════════════════════════════════════
# 🔗 MULTI-AI COMMUNICATION PROTOCOL
# ═══════════════════════════════════════════════════════════════════════
#
# This protocol enables Antigravity, GitHub Copilot, and Windsurf to
# work together as a relay team on the REEL GOD project.
#
# ─── HOW IT WORKS ─────────────────────────────────────────────────────
#
# All 3 AI agents share this project directory. They communicate through
# files in the comms/ folder. When one AI hits its limit or runs out of
# tokens, it writes a HANDOFF file. The commander then opens the next AI
# and says: "Read comms/HANDOFF.md and continue the work."
#
# ┌────────────────┐    comms/     ┌────────────────┐
# │  ANTIGRAVITY   │───────────────│ GITHUB COPILOT │
# │  (Primary)     │  shared files │  (Backup #1)   │
# └───────┬────────┘               └───────┬────────┘
#         │         comms/                  │
#         └──────────────────┬──────────────┘
#                            │
#                   ┌────────▼───────┐
#                   │   WINDSURF     │
#                   │  (Backup #2)   │
#                   └────────────────┘
#
# ─── THE PROTOCOL ─────────────────────────────────────────────────────
#
# 1. HANDOFF.md     → Written by outgoing AI, read by incoming AI.
#                      Contains: what was done, what's next, context.
#
# 2. TASK_QUEUE.md  → Shared task list. Any AI can add/complete tasks.
#
# 3. AGENT_LOG.md   → Activity log. Each AI appends what it did.
#
# 4. PROJECT_BIBLE.md → Master context document (already exists).
#
# ─── PRIORITY ORDER ───────────────────────────────────────────────────
#
# 1st: ANTIGRAVITY  (primary — has full tools, browser, subagents)
# 2nd: GITHUB COPILOT (backup — good for code generation)
# 3rd: WINDSURF     (backup — good for code editing & chat)
#
# When Primary hits token limit → Commander switches to Backup #1
# When Backup #1 hits limit → Commander switches to Backup #2
# When all refresh → Cycle back to Primary
#
# ─── RULES FOR ALL AI AGENTS ──────────────────────────────────────────
#
# 1. ALWAYS read HANDOFF.md first when asked to continue work.
# 2. ALWAYS read PROJECT_BIBLE.md if you need full project context.
# 3. ALWAYS update TASK_QUEUE.md when you complete or add tasks.
# 4. ALWAYS write to AGENT_LOG.md what you did in this session.
# 5. BEFORE stopping, ALWAYS write a new HANDOFF.md for the next AI.
# 6. NEVER contradict decisions in PROJECT_BIBLE.md without commander approval.
# 7. NEVER delete or overwrite another AI's log entries.
# 8. Use the SAME code style and architecture as existing code.
#
# ═══════════════════════════════════════════════════════════════════════
