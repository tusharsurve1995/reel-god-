---
description: How Windsurf should maintain context across conversations for the REEL GOD project
---

# Windsurf Context Sync Workflow

## Purpose
Ensure Windsurf always has complete context about the REEL GOD project across all conversations, eliminating the need for the user to repeat explanations.

## When Windsurf Starts a New Conversation

### 1. Read Context Files (Mandatory)
Always read these files in order before providing any assistance:
1. `PROJECT_BIBLE.md` - Project vision, architecture, build progress
2. `CONVERSATION_LOG.md` - Recent discussions, decisions, integration choices
3. Check `.idea/runConfigurations/` - Available IntelliJ configurations

### 2. Understand Current State
- Review what phase the project is in (currently Phase 1 complete)
- Check recent conversation history for user preferences
- Note any integration decisions (e.g., IntelliJ chat configuration)
- Understand user's workflow preferences

### 3. Provide Context-Aware Assistance
- Reference previous decisions when making suggestions
- Don't ask about things already decided in CONVERSATION_LOG.md
- Proactively suggest improvements based on conversation history
- Maintain consistency with previous architectural decisions

## During Conversations

### Monitoring Responsibilities
- **Track user preferences**: Note what the user likes/dislikes
- **Record decisions**: Document any new architectural or workflow decisions
- **Identify patterns**: Recognize recurring themes or concerns
- **Provide feedback**: Proactively suggest improvements based on context

### When Significant Decisions Are Made
1. Update `CONVERSATION_LOG.md` with:
   - Date and conversation summary
   - User's request and what was discussed
   - Solution implemented
   - Files created/modified
   - Status (completed/in progress)

2. Update `PROJECT_BIBLE.md` if:
   - Architecture changes
   - New phase is completed
   - Major tech stack decisions
   - New requirements or constraints

## Context Sharing Best Practices

### What to Always Remember
- **IDE Preference**: IntelliJ IDEA with run configurations
- **Chat Access**: User prefers IntelliJ integration over separate terminals
- **Context Persistence**: All conversations should be logged
- **No Repetition**: User shouldn't re-explain context to new AI sessions
- **Free Tools Only**: No paid APIs or services
- **Approve-Before-Post**: Commander must approve content before posting
- **24/7 Background Mode**: Agent runs continuously

### What to Proactively Monitor
- User's satisfaction with current integrations
- Potential improvements to workflow
- Missing context that might be needed later
- Opportunities to automate or streamline processes

## Example Context-Aware Response

Instead of asking: "What IDE are you using?"
Say: "Based on the conversation history, I see you're using IntelliJ IDEA. Would you like me to create a run configuration for this new feature?"

Instead of asking: "Have you set up the chat integration?"
Say: "I see from CONVERSATION_LOG.md that we already set up the IntelliJ chat configuration. Let me verify it's still working correctly."

## Automatic Context Updates

After each conversation, Windsurf should:
1. Review what was discussed
2. Update CONVERSATION_LOG.md with key points
3. Update PROJECT_BIBLE.md if architectural decisions changed
4. Note any new user preferences or workflow changes

## File Structure for Context

```
reel-god/
├── PROJECT_BIBLE.md          # Static project documentation
├── CONVERSATION_LOG.md       # Dynamic conversation history
└── .windsurf/
    └── workflows/
        └── context-sync.md   # This file
```

## Success Criteria

Windsurf is successfully maintaining context when:
- ✅ Never asks about decisions already documented
- ✅ References previous conversations appropriately
- ✅ Proactively suggests improvements based on history
- ✅ Maintains consistency with established architecture
- ✅ Updates context files after significant discussions
- ✅ User doesn't need to repeat explanations
