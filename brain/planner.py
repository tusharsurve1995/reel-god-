"""
REEL GOD — Content Planner
============================
Generates daily content plans, ideas, and weekly calendars.
Uses Gemini + memory data to produce creative, data-driven content strategies.
"""

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.core import ReelGodBrain

from brain.personality import STYLE_DESCRIPTIONS, QUALITY_CHECKLIST


class ContentPlanner:
    """
    Generates content ideas and weekly plans based on memory and trends.
    """

    def __init__(self, brain: "ReelGodBrain"):
        self.brain = brain
        self.memory = brain.memory

    # ──────────────────────────────────────────────────────────────────────
    #  IDEA GENERATION
    # ──────────────────────────────────────────────────────────────────────

    def generate_ideas(self, count: int = 3, style: str = None) -> list:
        """
        Generate a batch of original anime content ideas.
        Returns a list of idea dicts ready to be saved to memory.
        """
        # Pull context from memory
        memory_snapshot = self.memory.get_full_memory_snapshot()
        style_stats = memory_snapshot.get("style_stats", [])
        active_trends = memory_snapshot.get("active_trends", [])
        recent_posts = memory_snapshot.get("recent_posts", [])
        feedback = memory_snapshot.get("commander_feedback", [])

        # Determine which style to focus on
        if style:
            target_style = style
        else:
            # Pick style based on performance data or rotate
            if style_stats:
                # Occasionally try lower-performing styles to diversify
                import random
                weights = []
                for s in style_stats:
                    eng = s.get("avg_engagement", 0) or 0
                    weights.append(max(eng, 0.1))
                total = sum(weights)
                normalized = [w / total for w in weights]
                target_style = random.choices(
                    [s["style"] for s in style_stats],
                    weights=normalized
                )[0]
            else:
                import random
                target_style = random.choice(list(STYLE_DESCRIPTIONS.keys()))

        style_info = STYLE_DESCRIPTIONS.get(target_style, {})
        
        # Build the generation prompt
        prompt = f"""
Generate {count} ORIGINAL and UNIQUE anime content ideas for Instagram Reels.

━━━ TARGET STYLE ━━━
Style: {style_info.get('name', target_style)} {style_info.get('emoji', '')}
Description: {style_info.get('description', '')}
Visual keywords: {style_info.get('visual_keywords', '')}
Music mood: {style_info.get('music_mood', '')}
Core emotion: {style_info.get('emotion', '')}

━━━ RECENT PERFORMANCE DATA ━━━
{json.dumps(style_stats, indent=2) if style_stats else "No data yet — create the first posts!"}

━━━ CURRENT TRENDS ━━━
{json.dumps([t.get('topic') for t in active_trends[:10]], indent=2) if active_trends else "No trend data yet."}

━━━ RECENT POSTS (avoid repeating these concepts) ━━━
{json.dumps([p.get('title') for p in recent_posts], indent=2) if recent_posts else "No posts yet."}

━━━ COMMANDER FEEDBACK ━━━
{json.dumps([f.get('feedback') for f in feedback[-5:]], indent=2) if feedback else "No feedback yet."}

━━━ QUALITY CHECKLIST (each idea must pass these) ━━━
{chr(10).join(f"• {q}" for q in QUALITY_CHECKLIST)}

━━━ YOUR TASK ━━━
Generate exactly {count} ideas. For EACH idea, provide:

1. TITLE: A punchy, evocative title (5-8 words)
2. STYLE: {target_style}
3. MOOD: The primary emotion (one word)
4. HOOK: The first 2 seconds description — what stops the scroll?
5. STORY: The complete micro-story arc across 6-8 scenes (describe each scene briefly)
6. VISUAL_DIRECTION: How each scene looks — colors, composition, character design
7. MUSIC_DIRECTION: Specific music mood/genre/energy level
8. WHY_IT_WORKS: Why this will resonate and perform well

Format your response as a JSON array:
[
  {{
    "title": "...",
    "style": "{target_style}",
    "mood": "...",
    "hook": "...",
    "story": "Scene 1: ... Scene 2: ... Scene 3: ... Scene 4: ... Scene 5: ... Scene 6: ...",
    "visual_direction": "...",
    "music_direction": "...",
    "why_it_works": "..."
  }}
]

Be ORIGINAL. Be SPECIFIC. Make these ideas feel alive.
"""
        response_text = self.brain.think(prompt)
        
        # Parse the JSON from the response
        ideas = self._parse_ideas_response(response_text)
        
        # Save all ideas to memory
        saved_ids = []
        for idea in ideas:
            idea_id = self.memory.save_idea(
                title=idea.get("title", "Untitled"),
                style=idea.get("style", target_style),
                story=idea.get("story", ""),
                script=json.dumps(idea),  # Store full idea as JSON script
                mood=idea.get("mood", "")
            )
            idea["id"] = idea_id
            saved_ids.append(idea_id)

        self.memory.save_thought(
            f"Generated {len(ideas)} ideas in style '{target_style}'. IDs: {saved_ids}",
            "idea_generation"
        )

        return ideas

    def _parse_ideas_response(self, response_text: str) -> list:
        """Extract JSON array from LLM response."""
        import re
        # Try to find JSON array in the response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return raw response as a single idea
        self.memory.save_thought(
            f"Failed to parse ideas response as JSON. Raw: {response_text[:200]}",
            "error"
        )
        return []

    # ──────────────────────────────────────────────────────────────────────
    #  WEEKLY PLANNING
    # ──────────────────────────────────────────────────────────────────────

    def generate_weekly_calendar(self) -> dict:
        """
        Generate a full week's content strategy and persist it.
        Returns a dict mapping dates to planned content styles/themes.
        """
        # 1. Check if calendar is already planned in the DB
        existing = self.memory.get_active_schedule()
        today_str = datetime.now().strftime('%Y-%m-%d')
        future_slots = [s for s in existing if s["date_str"] >= today_str]
        if future_slots:
            days = []
            for slot in existing:
                days.append({
                    "day": slot["day_name"],
                    "date": slot["date_str"],
                    "style": slot["style"],
                    "theme": slot["theme"],
                    "post_time": slot["post_time"]
                })
            return {"week_strategy": "Retrieved from memory cache.", "days": days}

        today = datetime.now()
        memory = self.memory.get_full_memory_snapshot()

        prompt = f"""
Create a 7-day anime content strategy for Instagram Reels.

Today is {today.strftime('%A, %B %d, %Y')}.

Performance data by style:
{json.dumps(memory.get('style_stats', []), indent=2)}

Commander feedback to keep in mind:
{json.dumps([f.get('feedback') for f in memory.get('commander_feedback', [])[-3:]], indent=2)}

Available styles:
{json.dumps(list(STYLE_DESCRIPTIONS.keys()), indent=2)}

For each day (Monday through Sunday), decide:
1. Which style to use and why
2. A general theme or concept direction
3. The best time to post (9AM / 12PM / 6PM / 9PM)
4. Why this day/style combination makes strategic sense

Format as JSON:
{{
  "week_strategy": "...",
  "days": [
    {{
      "day": "Monday",
      "date": "YYYY-MM-DD",
      "style": "...",
      "theme": "...",
      "post_time": "...",
      "reasoning": "..."
    }}
  ]
}}
"""
        response_text = self.brain.think(prompt)
        
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                calendar = json.loads(json_match.group())
                
                # 2. Persist to database
                for day_data in calendar.get("days", []):
                    day_name = day_data.get("day")
                    date_str = day_data.get("date")
                    style = day_data.get("style")
                    theme = day_data.get("theme")
                    post_time = day_data.get("post_time")
                    
                    # Convert post_time e.g., '6PM' or '06:00 PM' to '18:00' format
                    clean_time = "18:00"  # default
                    if post_time:
                        try:
                            time_str = post_time.strip().upper()
                            if "AM" in time_str or "PM" in time_str:
                                for fmt in ("%I%p", "%I:%M%p", "%I %p", "%I:%M %p"):
                                    try:
                                        t_obj = datetime.strptime(time_str, fmt)
                                        clean_time = t_obj.strftime("%H:%M")
                                        break
                                    except ValueError:
                                        continue
                            else:
                                clean_time = time_str
                        except Exception:
                            pass
                            
                    if day_name and date_str and style and theme:
                        self.memory.save_schedule_day(day_name, date_str, style, theme, clean_time)
                
                self.memory.save_thought(
                    f"Generated and persisted weekly calendar: {json.dumps(calendar.get('week_strategy', ''))[:100]}",
                    "weekly_planning"
                )
                return calendar
            except json.JSONDecodeError:
                pass

        return {"error": "Could not parse calendar", "raw": response_text}

    # ──────────────────────────────────────────────────────────────────────
    #  CAPTION & HASHTAG GENERATION
    # ──────────────────────────────────────────────────────────────────────

    def generate_caption_and_hashtags(self, idea: dict) -> dict:
        """
        Generate an Instagram caption + hashtag set for a content idea.
        """
        prompt = f"""
Write an Instagram caption and hashtag set for this anime Reel:

Title: {idea.get('title')}
Style: {idea.get('style')}
Story: {idea.get('story')}
Mood: {idea.get('mood')}

Requirements:
• Caption: 2-4 lines. Evocative and emotional. End with a question to boost comments.
  Start with a hook line that stops the scroll even in text form.
• Emojis: Use 2-4 relevant emojis naturally within the caption.
• Hashtags: 25-30 hashtags mixing: broad anime tags + niche tags + trending tags.
  Include hashtags in Japanese characters for broader reach (e.g., #アニメ #アニメ編集).

Format as JSON:
{{
  "caption": "...",
  "hashtags": "#tag1 #tag2 #tag3 ..."
}}
"""
        response_text = self.brain.think(prompt)
        
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {
            "caption": f"✨ {idea.get('title', 'Anime Edit')} ✨\n\nWhat does this make you feel? 👇",
            "hashtags": " ".join(
                ["#anime", "#animeedit", "#animeart", "#アニメ", "#アニメ編集",
                 "#animeworld", "#animelover", "#aianime", "#aiart"]
            )
        }

    # ──────────────────────────────────────────────────────────────────────
    #  SELF-CRITIQUE
    # ──────────────────────────────────────────────────────────────────────

    def self_critique_idea(self, idea: dict) -> dict:
        """
        Agent reviews its own idea against the quality checklist.
        Returns critique with score and improvement suggestions.
        """
        prompt = f"""
Review this anime content idea against the quality checklist.

IDEA:
{json.dumps(idea, indent=2)}

QUALITY CHECKLIST:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(QUALITY_CHECKLIST))}

Score each item 1-10.
Provide:
1. Individual scores for each checklist item
2. Overall score (average)
3. Biggest strength
4. Biggest weakness
5. One specific improvement suggestion

Format as JSON:
{{
  "scores": {{
    "hook_power": 0,
    "emotional_arc": 0,
    "originality": 0,
    "music_match": 0,
    "story_completeness": 0,
    "shareability": 0,
    "scene_purpose": 0,
    "style_consistency": 0
  }},
  "overall_score": 0,
  "strength": "...",
  "weakness": "...",
  "improvement": "..."
}}
"""
        response_text = self.brain.think(prompt)
        
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {"overall_score": 7, "error": "Parse failed", "raw": response_text[:200]}
