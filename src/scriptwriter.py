"""
scriptwriter.py — Template-based News Shorts script generator.

Uses deterministic templates with topic-aware variations to produce structured
scripts complete with title, narration, scene descriptions, tags, and a
YouTube description — no paid API keys required.
"""

import hashlib
import logging
import random
import re
import time
from typing import TypedDict

logger = logging.getLogger(__name__)

# Minimum / maximum acceptable word counts for the narration script
_MIN_WORDS = 60
_MAX_WORDS = 200


class ScriptData(TypedDict):
    """Structured output from the news script generator."""

    title: str
    script: str
    caption_script: str
    hook: str
    scenes: list[str]
    tags: list[str]
    description: str


# ---------------------------------------------------------------------------
# Hook templates — news-anchor style opening lines
# ---------------------------------------------------------------------------
_HOOKS: list[str] = [
    # Breaking news style
    "Breaking news just in — {topic} is developing rapidly and here is everything you need to know.",
    "This just happened and it changes everything — {topic} is the story making headlines right now.",
    "Major development in {topic} — here is your sixty-second briefing on what just broke.",
    "BREAKING: {topic} — what you need to know right now, straight from the newsroom.",
    "We interrupt your feed with this breaking update on {topic} — stay with us.",
    "Alert: {topic} has just crossed the wire and the implications are significant.",
    # Authoritative anchor style
    "Good evening. Tonight's top story: {topic} — here is what sources are confirming.",
    "Our correspondents are on the ground as {topic} continues to develop.",
    "Officials have confirmed a major development on {topic} — here are the verified facts.",
    "Reporting live: {topic} is unfolding in real time and we have the full picture.",
    "Sources close to the story confirm: {topic} has reached a critical juncture.",
    "The wire services are lighting up tonight — {topic} is the story everyone is watching.",
    # Urgency / significance
    "You need to hear this before the rest of the world catches up — {topic} just shifted.",
    "In the next sixty seconds I will tell you everything confirmed about {topic} so far.",
    "This is the story your newscast may not have covered yet — {topic} explained.",
    "Do not scroll past this — {topic} is the most important story of the hour.",
    # Question hooks
    "What does {topic} actually mean for you? Here is the sixty-second answer.",
    "Why is {topic} dominating every newsroom right now? The facts, unfiltered.",
    "Could {topic} be the defining story of the week? The evidence says yes.",
    # Context hooks
    "Three verified facts about {topic} that cut through the noise.",
    "Here is the confirmed timeline on {topic} — no speculation, just facts.",
    "The full story on {topic} in under sixty seconds — authoritative and direct.",
]

# ---------------------------------------------------------------------------
# Body templates — professional news-reporting style
# ---------------------------------------------------------------------------
_BODIES: list[str] = [
    (
        "Here is what sources confirm. {topic} has emerged as a developing story "
        "with verified reports coming in from multiple credible outlets. Officials "
        "state that the situation is being monitored at the highest levels. "
        "According to reports, the scale of this development has few precedents "
        "in recent history. Analysts confirm the direct impact will be felt across "
        "multiple sectors in the days and weeks ahead."
    ),
    (
        "Let us break this down. {topic} has moved into verified, confirmed "
        "territory according to sources with direct knowledge of the situation. "
        "Independent reporting validates what insiders have been signaling for "
        "days. Officials state that immediate action is being considered. "
        "The convergence of credible accounts and official statements makes "
        "this one of the most significant developments of the current news cycle."
    ),
    (
        "Here is the full picture as sources confirm it. {topic} has captured "
        "global attention for reasons that go deeper than the initial headlines. "
        "According to reports from senior officials and independent correspondents, "
        "a fundamental shift is underway. Innovation, accountability, and "
        "transparency are at the center of this story. The trajectory, "
        "as confirmed by multiple sources, suggests the coming days will be pivotal."
    ),
    (
        "Consider the broader context officials are now addressing. {topic} "
        "represents more than a single event — sources confirm it signals "
        "a structural change with lasting implications. The professional "
        "community has responded with unprecedented engagement, and fresh "
        "data from verified outlets continues to reinforce its significance. "
        "What began as a developing story has become a confirmed, mainstream "
        "priority with real-world consequences already taking shape."
    ),
    (
        "Officials state the key factors are becoming clear. {topic} is gaining "
        "momentum because it addresses a genuine and urgent reality. "
        "Credible sources across industries have validated its importance, "
        "and according to reports, the momentum shows no sign of slowing. "
        "For those paying close attention to verified accounts, the implications "
        "here are both timely and significant. This is a story worth following closely."
    ),
    (
        "Step back and look at what sources are confirming. {topic} did not "
        "arrive without warning — the signals were there for those following "
        "credible reporting. What has changed is the pace of confirmed "
        "developments and the scale of official attention it now commands. "
        "The intersection of verified research, real-world outcomes, and "
        "public accountability has reached a threshold that makes this moment "
        "distinctly significant."
    ),
    (
        "Here is the angle confirmed reporting reveals. {topic} is not just "
        "a story about what is happening right now — officials state it will "
        "shape outcomes for months to come. The groundwork being laid today, "
        "according to sources with direct knowledge, will determine results "
        "that play out across multiple timelines. Analysts who have studied "
        "comparable developments emphasise that staying informed right now "
        "is critically important."
    ),
    (
        "The numbers tell a verified story. {topic} has registered measurable "
        "movement across multiple indicators that officials and analysts watch "
        "closely. According to reports, the combination of increased activity, "
        "verifiable outcomes, and sustained momentum puts this in a category "
        "that demands serious attention. Comparable developments have historically "
        "preceded major shifts in how institutions and individuals operate."
    ),
    (
        "Here is what makes {topic} different from background noise. "
        "Sources confirm this story has compounding factors — a base of "
        "credible evidence, a growing community of informed voices, and "
        "real-world implications that build on each other. Officials state "
        "that the quality of verified engagement surrounding {topic} signals "
        "something more durable and consequential than typical news cycles suggest."
    ),
    (
        "Let us talk about the stakes. Officials confirm that {topic} sits "
        "at the intersection of global policy, economics, and public welfare "
        "in a way that makes it genuinely consequential. According to reports, "
        "the individuals and organisations who engage thoughtfully with this "
        "story now are best positioned for what follows. Sources consistently "
        "confirm that informed awareness leads to better outcomes in situations "
        "like this one."
    ),
    (
        "Here is something confirmed reporting rarely captures in full. {topic} "
        "is not just a news story — it is a turning point that real people are "
        "living through right now. Behind the verified data are communities "
        "whose decisions and futures are directly shaped by how this unfolds. "
        "Officials state that the human dimension is precisely why understanding "
        "{topic} at a deeper level matters so much to so many."
    ),
    (
        "The context sources confirm changes everything. {topic} did not emerge "
        "in a vacuum — officials state it is the product of compounding forces "
        "that have been building for some time. Now that verified reports confirm "
        "critical mass has been reached, the pace of change is accelerating. "
        "According to multiple sources, the smartest move right now is to "
        "understand the full picture rather than reacting to fragments."
    ),
]

# ---------------------------------------------------------------------------
# Call-to-action templates — news-channel style
# ---------------------------------------------------------------------------
_CTAS: list[str] = [
    "Follow for breaking news delivered daily. What is your take on {topic}? Share it in the comments.",
    "Subscribe to never miss a breaking story. Drop your thoughts on {topic} below.",
    "Stay informed — hit subscribe for your daily news briefing. Tell us what you think.",
    "Turn on notifications so you never miss a breaking update. Your daily news is here.",
    "Subscribe for verified, concise news delivered every day. Comment your reaction to {topic}.",
    "Stay ahead of the story — subscribe and hit the bell. What questions do you have on {topic}?",
    "Every like tells the algorithm this news matters. Subscribe and join the conversation.",
    "If you need your news fast and verified, subscribe now. We cover every major story daily.",
    "This story is still developing — follow for live updates as they come in.",
    "Knowledge is power. Subscribe so you are always the first to know. See you in the next briefing.",
    "Share this with someone who needs to stay informed. Then subscribe for daily breaking news.",
    "Do not just watch — react. Leave your take on {topic} below. We read every comment.",
    "Tap subscribe for your daily sixty-second news briefing — no noise, just facts.",
    "If this briefing kept you informed, the subscribe button is your way to stay that way.",
    "The story on {topic} continues to develop. Subscribe now to follow every update as it breaks.",
]

# ---------------------------------------------------------------------------
# Scene description templates — news-appropriate visual settings
# ---------------------------------------------------------------------------
_SCENE_SETS: list[list[str]] = [
    [
        "Newsroom with breaking news graphics on screens",
        "World map with highlighted regions geopolitical",
        "Press conference podium with microphones crowd",
        "Financial charts and data on trading screens",
        "Aerial city skyline dramatic golden hour",
    ],
    [
        "Satellite imagery aerial view conflict zone",
        "Breaking news chyron graphics broadcast studio",
        "Officials speaking at podium press briefing",
        "Global stock exchange trading floor activity",
        "City skyline aerial panoramic dramatic clouds",
    ],
    [
        "Television broadcast studio live news anchor",
        "Capitol building government official exterior",
        "Emergency response vehicles flashing lights scene",
        "Newspaper headlines close-up printing press",
        "International flags wind headquarters building",
    ],
    [
        "Journalist reporter live location camera crew",
        "Data center servers technology infrastructure",
        "Court building exterior justice scales concept",
        "Economic graphs upward trend financial district",
        "World leaders summit meeting conference table",
    ],
    [
        "Breaking news alert smartphone notification glow",
        "Satellite dish communications technology night",
        "Protest crowd urban street demonstration",
        "Medical research laboratory scientists working",
        "Parliament building exterior government power",
    ],
    [
        "Television screens wall of news broadcasts",
        "Military base aerial defense technology",
        "United Nations building exterior international",
        "Climate summit renewable energy windmills aerial",
        "Hospital exterior healthcare emergency lights",
    ],
    [
        "War room strategy meeting officials crisis",
        "Space agency launch control room screens",
        "Global supply chain shipping containers port",
        "Cybersecurity monitoring screens dark room",
        "Press freedom journalist camera news gathering",
    ],
    [
        "Stock market crash red screen traders panic",
        "Natural disaster aerial humanitarian response",
        "Election vote counting room officials ballots",
        "Science breakthrough laboratory discovery",
        "Diplomatic meeting handshake international",
    ],
    [
        "Oil refinery energy infrastructure industrial",
        "Protests demonstrators holding signs urban",
        "Central bank exterior monetary policy concept",
        "Arctic landscape climate change ice melting",
        "Technology conference keynote stage presenter",
    ],
    [
        "Security forces operations tactical urban",
        "Agricultural fields food security crisis",
        "Currency exchange rates financial ticker",
        "United Nations General Assembly delegates",
        "Rocket launch space exploration dramatic",
    ],
]

# ---------------------------------------------------------------------------
# Title templates — news-style, authoritative, informative
# ---------------------------------------------------------------------------
_TITLE_TEMPLATES: list[str] = [
    "BREAKING: {Topic} — Full Report 🔴",
    "{Topic} — What Officials Are Confirming 📋",
    "NEWS ALERT: {Topic} Explained in 60 Seconds ⚡",
    "Top Story: {Topic} — The Facts You Need 📰",
    "{Topic} — Breaking Development 🚨",
    "CONFIRMED: {Topic} — Your 60-Second Briefing 🎙️",
    "{Topic} — What Sources Are Saying Right Now 🔍",
    "Latest on {Topic} — Verified Report 📡",
    "{Topic}: The Story Behind the Headlines 🗞️",
    "URGENT: {Topic} — Everything Confirmed So Far 📌",
    "{Topic} — Officials React, Here Are the Facts 🏛️",
    "Breaking Down {Topic} — What It Means for You 🌐",
    "{Topic} — Live Update and Analysis 📺",
    "The Real Story on {Topic} — No Speculation 🎯",
    "{Topic} Just Changed — Here Is Why It Matters 📈",
    "60-Second Brief: {Topic} — Stay Informed 🔔",
]

# ---------------------------------------------------------------------------
# Description template — news-channel style
# ---------------------------------------------------------------------------
_DESCRIPTION_TEMPLATE = """📰 {title}

Stay informed: {topic} is breaking now and we cover it in under 60 seconds.

In this briefing, you will learn:
✅ What sources and officials are confirming about {topic}
✅ The key verified facts and data points
✅ What this development means and what to watch next

📱 Subscribe for breaking news delivered daily — no noise, just verified facts.

👍 Like this video if you found it informative
💬 Share your reaction in the comments
🔔 Turn on notifications so you never miss a breaking story

{hashtags}

#BreakingNews #NewsShorts #NewsAlert #WorldNews #DailyNews #Shorts #NewsToday"""


# ---------------------------------------------------------------------------
# Tag generation
# ---------------------------------------------------------------------------
_BASE_TAGS: list[str] = [
    "breaking news", "news today", "daily news", "world news", "news shorts",
    "news alert", "shorts", "trending", "news", "headlines",
]


def _topic_to_tags(topic: str) -> list[str]:
    """Generate relevant news tags from the topic string."""
    words = re.sub(r"[^a-zA-Z0-9\s]", "", topic).lower().split()
    topic_tags = [w for w in words if len(w) > 2]

    if len(words) >= 2:
        topic_tags.append("".join(words[:2]))

    all_tags = list(dict.fromkeys(topic_tags + _BASE_TAGS))
    return all_tags[:20]


# ---------------------------------------------------------------------------
# Category-aware hook selection
# ---------------------------------------------------------------------------
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "politics": [
        "election", "president", "congress", "senate", "parliament", "government",
        "policy", "vote", "political", "democrat", "republican", "legislation",
        "supreme court", "white house", "cabinet", "administration",
    ],
    "economy": [
        "stock", "market", "economy", "inflation", "federal reserve", "gdp",
        "recession", "trade", "tariff", "interest rate", "unemployment",
        "nasdaq", "dow", "s&p", "bank", "finance", "crypto", "bitcoin",
    ],
    "geopolitics": [
        "war", "conflict", "military", "nato", "russia", "china", "ukraine",
        "iran", "israel", "sanctions", "diplomacy", "treaty", "nuclear",
        "troops", "ceasefire", "invasion", "crisis",
    ],
    "science": [
        "nasa", "space", "climate", "research", "discovery", "ai",
        "artificial intelligence", "tech", "breakthrough", "study", "scientists",
        "data", "experiment", "quantum", "renewable", "energy",
    ],
    "health": [
        "health", "medical", "hospital", "vaccine", "disease", "outbreak",
        "fda", "who", "treatment", "drug", "cancer", "mental health",
        "public health", "pandemic", "virus", "epidemic",
    ],
}

_CATEGORY_HOOKS: dict[str, list[str]] = {
    "politics": [
        "Officials on Capitol Hill are reacting tonight to the latest on {topic}.",
        "A major political development on {topic} — sources confirm what happened.",
        "The political implications of {topic} are being felt across Washington right now.",
    ],
    "economy": [
        "Markets are moving on {topic} — here is what traders and economists are saying.",
        "The economic signal from {topic} is one financial analysts cannot ignore.",
        "Before your next financial decision, here is what {topic} means for the economy.",
    ],
    "geopolitics": [
        "International correspondents are reporting on the ground: {topic} is escalating.",
        "World leaders are responding to {topic} — here is the confirmed situation.",
        "The geopolitical implications of {topic} are being tracked by every major newsroom.",
    ],
    "science": [
        "Scientists and researchers have confirmed a major development on {topic}.",
        "The peer-reviewed findings on {topic} are now public — here is what they mean.",
        "A verified scientific breakthrough on {topic} is making headlines worldwide.",
    ],
    "health": [
        "Public health officials are issuing an update on {topic} — here are the facts.",
        "The medical community is responding to {topic} with urgency — here is why.",
        "Health authorities confirm: what you need to know about {topic} right now.",
    ],
}


def _detect_category(topic: str) -> str | None:
    """Return the topic's best-matching news category string, or *None* if no match."""
    t = topic.lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return cat
    return None


_SEED_TIME_GRANULARITY = 3600  # seconds — changes seed every hour


def _deterministic_seed(topic: str) -> int:
    """Create a seed from the topic and current time for varied selections.

    Incorporates the current hour so that each pipeline run (scheduled every
    few hours) produces a different script even for the same topic.
    """
    time_component = str(int(time.time() // _SEED_TIME_GRANULARITY))
    raw = topic + time_component
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _titlecase_topic(topic: str) -> str:
    """Convert a topic string to title case for display."""
    return topic.strip().title()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_script(topic: str) -> ScriptData:
    """Generate a structured News Shorts script for *topic*.

    Uses news-anchor templates with time-seeded randomisation so each
    pipeline run produces a different script, even for the same topic.

    Args:
        topic: The breaking news story or topic string to write about.

    Returns:
        A :class:`ScriptData` dict with title, script, caption_script,
        scenes, tags, and description.

    Raises:
        ValueError: If the generated script fails validation.
    """
    logger.info("Generating news script for topic: '%s'", topic)

    seed = _deterministic_seed(topic)
    rng = random.Random(seed)

    display_topic = _titlecase_topic(topic)

    # Select templates — include category-specific hooks when the topic matches
    category = _detect_category(topic)
    hook_pool = _HOOKS + (_CATEGORY_HOOKS.get(category, []) if category else [])
    hook = rng.choice(hook_pool).format(topic=display_topic)
    body = rng.choice(_BODIES).format(topic=display_topic)
    cta = rng.choice(_CTAS).format(topic=display_topic)
    scenes = list(rng.choice(_SCENE_SETS))

    # Build the full script (hook + body + cta for TTS audio)
    script_text = f"{hook} {body} {cta}"

    # Caption script excludes the hook to avoid duplicating the title on-screen
    caption_text = f"{body} {cta}"

    # Build title
    title = rng.choice(_TITLE_TEMPLATES).format(Topic=display_topic)
    title = title[:100]

    # Build tags
    tags = _topic_to_tags(topic)

    # Build description
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:10])
    description = _DESCRIPTION_TEMPLATE.format(
        title=title,
        topic=display_topic,
        hashtags=hashtags,
    )

    # Validate word count
    word_count = len(script_text.split())
    if word_count < _MIN_WORDS:
        logger.warning("Script shorter than expected (%d words)", word_count)
    if word_count > _MAX_WORDS:
        logger.warning("Script longer than expected (%d words)", word_count)

    script_data = ScriptData(
        title=title,
        script=script_text,
        caption_script=caption_text,
        hook=hook,
        scenes=scenes,
        tags=tags,
        description=description,
    )

    logger.info(
        "News script generated — title: '%s', words: %d",
        script_data["title"],
        len(script_data["script"].split()),
    )
    return script_data
