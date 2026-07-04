"""
REEL GOD — Instagram Caption Builder
=====================================
Builds perfectly formatted Instagram captions for every mood type.
Includes: emotional hook, quote, anime credit, music credit, hashtag block.
"""
from typing import Optional

# ── MOOD-SPECIFIC HASHTAG BLOCKS ─────────────────────────────────────────────
MOOD_HASHTAGS = {
    "romantic": (
        "#animelove #animeromance #yourlieinapril #shigatsu #violetevergarden "
        "#animecouples #animeheart #animeromantic #animefeelings #animeemotion"
    ),
    "emotional": (
        "#animecry #animesad #animefeelings #animetears #animemood "
        "#animeemotion #sadanime #animeheart #animeworld #animemoments"
    ),
    "motivational": (
        "#animemotivation #animequotes #naruto #animeinspiration #animerise "
        "#nevergivup #animemindset #animewisdom #animegoals #believeit"
    ),
    "sacrifice": (
        "#animehero #animesacrifice #attackontitan #animemoments #animeepic "
        "#giveyourhearts #animelegend #animecharacter #animedrama #animetears"
    ),
    "epic_action": (
        "#animebattle #animeaction #demonslayer #jujutsukaisen #animepower "
        "#animeepic #animefight #animehype #animeadrenaline #animeclip"
    ),
    "dark_cinematic": (
        "#animedark #animedrama #attackontitan #animemysterious #animeatmosphere "
        "#animemood #darkanimeedit #animecinematic #animescene #deepanime"
    ),
    "mystical": (
        "#animemystery #animefantasy #animespirit #animemystic #animemagic "
        "#animedestiny #animeworld #spiritanime #animeuniverse #animebeautiful"
    ),
    "happy": (
        "#animehappy #animesmile #animejoy #animefun #animefriends "
        "#animelaughter #animelife #animegood #animewarm #animelove"
    ),
}

ANIME_HASHTAGS = {
    "demon_slayer":         "#demonslayer #kimetsu #tanjiro #nezuko #zenitsu #inosuke",
    "attack_on_titan":      "#aot #attackontitan #eren #levi #mikasa #erwin",
    "naruto":               "#naruto #uzumaki #ninjaworld #narutoshippuden #believe",
    "your_lie_in_april":    "#yourlieinapril #shigatsu #kaori #kousei #piano",
    "violet_evergarden":    "#violetevergarden #kyoani #dolls #emotionalletter",
    "fullmetal_alchemist":  "#fmab #fullmetalalchemist #edward #alphonse #equivalent",
    "re_zero":              "#rezero #emilia #rem #subaru #witchofenvy",
    "one_piece":            "#onepiece #luffy #zoro #nakama #pirateship",
    "jujutsu_kaisen":       "#jjk #jujutsukaisen #gojo #yuji #sukuna",
    "hunter_x_hunter":      "#hxh #hunterxhunter #gon #killua #hisoka",
    "sword_art_online":     "#sao #swordartonline #kirito #asuna",
}

COMMON_HASHTAGS = (
    "#anime #animereels #animeedit #animecommunity #otaku "
    "#animegram #animeworld #weeb #animelover #animevideo"
)

# ── MOOD OPENING HOOKS ────────────────────────────────────────────────────────
# These appear before the quote — the emotional punch that stops the scroll
MOOD_HOOKS = {
    "romantic": [
        "Some people come into your life and change everything. 🌸",
        "The kind of love that doesn't need words. 💕",
        "He never knew his world could feel this warm. 🌅",
    ],
    "emotional": [
        "This one will break your heart in the most beautiful way. 💙",
        "Some farewells are spoken in silence. 🌧️",
        "The scenes that made us cry without warning. 💫",
    ],
    "motivational": [
        "They counted him out. He counted every rep. 🔥",
        "Success tastes sweeter when they said you couldn't. 💪",
        "Every great story starts with someone refusing to quit. ⚡",
    ],
    "sacrifice": [
        "He had nothing left to lose — so he gave everything. 🗡️",
        "Some heroes don't survive the story. Their legend does. 👑",
        "The moment he chose others over himself. 💛",
    ],
    "epic_action": [
        "The moment your blood turns to adrenaline. ⚔️",
        "Power earned through pain and purpose. 🌪️",
        "This is what it looks like when the will refuses to break. 🔥",
    ],
    "dark_cinematic": [
        "In the darkest hours, the truest characters are revealed. 🌑",
        "Some destinies are forged in shadow. 🖤",
        "He walked into the darkness so others wouldn't have to. 🌘",
    ],
    "mystical": [
        "Some power isn't learned — it's awakened. ✨",
        "Between worlds, a bond beyond understanding. 🌌",
        "Where the ordinary world ends, the true journey begins. 🔮",
    ],
    "happy": [
        "Life is better when you share it with people who get you. 🌸",
        "Sometimes joy is the most powerful form of rebellion. 🌟",
        "This is what healing looks like. 🌈",
    ],
}


def build_caption(
    reel_meta: dict,
    mood: Optional[str] = None,
    hook_index: int = 0,
) -> str:
    """
    Build a full, formatted Instagram caption from reel metadata.

    Args:
        reel_meta: dict with keys: title, quote, purpose, anime, style,
                   music_name (optional), music_mood (optional)
        mood: override mood/style if different from reel_meta['style']
        hook_index: which hook to pick (0=first, rotates per post)

    Returns:
        Full formatted caption string ready for Instagram.
    """
    style  = mood or reel_meta.get("style", "epic_action")
    # Normalize style aliases
    if style == "romance":
        style = "romantic"

    title  = reel_meta.get("title", "Anime Reel")
    quote  = reel_meta.get("quote", "")
    purpose = reel_meta.get("purpose", "")
    anime  = reel_meta.get("anime", "")
    music_name = reel_meta.get("music_name", reel_meta.get("music", ""))

    # Pick emotional hook
    hooks = MOOD_HOOKS.get(style, MOOD_HOOKS["epic_action"])
    hook  = hooks[hook_index % len(hooks)]

    # Build hashtag block
    mood_tags  = MOOD_HASHTAGS.get(style, "")
    anime_tags = ANIME_HASHTAGS.get(anime, "")
    all_tags   = f"{mood_tags}\n{anime_tags}\n{COMMON_HASHTAGS}".strip()

    # Music credit
    music_credit = ""
    if music_name:
        music_credit = f"🎵 Music: {music_name}"

    # Anime credit
    anime_display = anime.replace("_", " ").title() if anime else ""
    anime_credit = f"📺 Anime: {anime_display}" if anime_display else ""

    # Assemble — Instagram best practice: hook → story → quote → credits → tags
    lines = [
        f"✦ {title.upper()} ✦",
        "",
        hook,
        "",
    ]

    # Add purpose line if it's meaningful
    if purpose and purpose not in title:
        # Shorten purpose to just the emotional tagline part
        purpose_clean = purpose.split("—")[-1].strip() if "—" in purpose else purpose
        lines.append(f"💬 {purpose_clean}")
        lines.append("")

    # Quote (the hero line)
    if quote:
        lines.append(f'"{quote}"')
        lines.append("")

    # Divider + credits
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if music_credit:
        lines.append(music_credit)
    if anime_credit:
        lines.append(anime_credit)
    lines.append("")
    lines.append(all_tags)

    return "\n".join(lines)


def build_story_caption(reel_meta: dict) -> str:
    """Shorter caption for Instagram Stories (no hashtag spam, just the hook)."""
    style  = reel_meta.get("style", "epic_action")
    if style == "romance":
        style = "romantic"
    title  = reel_meta.get("title", "")
    quote  = reel_meta.get("quote", "")
    hooks  = MOOD_HOOKS.get(style, MOOD_HOOKS["epic_action"])

    return f"{hooks[0]}\n\n\"{quote}\"\n\n✦ {title} ✦"
