"""
Kō — social posting.

Called from season_mailer.py once per new micro-season, after the email and
archive have been published. Generates platform-tuned copy via Claude, then
posts to Twitter/X, Reddit, and Are.na.

Each platform is independent: a failure on one never blocks the others, and
nothing here is allowed to abort the calling pipeline. All exceptions are
caught and reduced to a status string in the returned dict.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import anthropic

from content_generator import normalize_content

log = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-opus-4-5"

REDDIT_SUBREDDITS = ("japan", "japanlife", "LearnJapanese")


# ── prompt builders ───────────────────────────────────────────────────────────

def _twitter_prompt(season: dict, content: dict, archive_url: str) -> str:
    haiku = content.get("haiku") or {}
    return f"""Write a tweet announcing the start of this Japanese micro-season for the Kō newsletter.

Season: {season['name_en']} ({season['name_jp']} / {season['name_romaji']})
Season number: {season['id']} of 72
Opening: {content.get('opening', '')}
Haiku (english): {haiku.get('english', '')}
Archive URL: {archive_url}

Rules:
- Max 280 characters including the URL
- Lead with the season name in English and Japanese
- Include the haiku OR a line from the opening — not both
- End with the archive URL
- No hashtag spam — one or two max: #Japan #七十二候
- Tone: quiet, observational — match the Kō voice in BRAND.md
- Respond with only the tweet text, nothing else"""


def _reddit_prompt(season: dict, content: dict, archive_url: str) -> str:
    return f"""Write a Reddit post for r/japan announcing the start of this Japanese micro-season.

Season: {season['name_en']} ({season['name_jp']} / {season['name_romaji']})
Season number: {season['id']} of 72
Nature notes: {content.get('nature_notes', '')}
Seasonal produce: {content.get('seasonal_produce', '')}
Cultural note: {content.get('cultural_note', '')}
Archive URL: {archive_url}

Rules:
- Title: interesting and specific, not clickbait. Example: "Season 21/72 in Japan: the first rainbows appear and bamboo shoots hit their peak"
- Body: 2-3 short paragraphs. Lead with what's happening in nature, then food, then culture.
- End with a single line: "Full season notes, haiku, and seasonal dishes at {archive_url}"
- Do not sound like marketing copy
- Tone: genuinely informative, like a knowledgeable friend
- Respond with JSON: {{"title": "...", "body": "..."}}"""


def _arena_prompt(season: dict, content: dict, archive_url: str) -> str:
    haiku = content.get("haiku") or {}
    return f"""Write a short Are.na block for this Japanese micro-season.

Season: {season['name_en']} ({season['name_jp']})
Opening: {content.get('opening', '')}
Haiku: {haiku.get('japanese', '')} / {haiku.get('romaji', '')} / {haiku.get('english', '')}
Archive URL: {archive_url}

Rules:
- 2-3 sentences max
- Include the haiku
- Sparse and contemplative — Are.na audience appreciates restraint
- End with the archive URL on its own line
- Respond with only the block text, nothing else"""


def _claude_text(prompt: str, max_tokens: int = 600) -> str:
    """Single-shot Claude call returning plain text."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return text.strip()


# ── platform handlers ─────────────────────────────────────────────────────────

def _post_twitter(season: dict, content: dict, archive_url: str) -> str:
    import tweepy

    required = (
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    )
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        return f"skipped: missing env {','.join(missing)}"

    tweet = _claude_text(_twitter_prompt(season, content, archive_url), max_tokens=400)
    if len(tweet) > 280:
        tweet = tweet[:279].rstrip() + "…"

    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    response = client.create_tweet(text=tweet)
    tweet_id = getattr(response, "data", {}).get("id") if hasattr(response, "data") else None
    return f"posted: tweet {tweet_id}" if tweet_id else "posted"


def _post_reddit(season: dict, content: dict, archive_url: str) -> str:
    import praw

    required = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        return f"skipped: missing env {','.join(missing)}"

    raw = _claude_text(_reddit_prompt(season, content, archive_url), max_tokens=900)
    try:
        payload = json.loads(raw)
        title = payload["title"].strip()
        body = payload["body"].strip()
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        return f"failed: could not parse Claude JSON ({e})"

    user_agent = f"ko-72:social_poster:v1 (by /u/{os.environ['REDDIT_USERNAME']})"
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=user_agent,
    )

    errors: list[str] = []
    for sub_name in REDDIT_SUBREDDITS:
        try:
            submission = reddit.subreddit(sub_name).submit(title=title, selftext=body)
            return f"posted: r/{sub_name} ({submission.id})"
        except Exception as e:  # noqa: BLE001 — swallow per-sub failures, try next
            log.warning("Reddit submit to r/%s failed: %s", sub_name, e)
            errors.append(f"r/{sub_name}: {e}")
    return "failed: " + " | ".join(errors)


def _post_arena(season: dict, content: dict, archive_url: str) -> str:
    import requests

    token = os.environ.get("ARENA_ACCESS_TOKEN")
    channel = os.environ.get("ARENA_CHANNEL_SLUG")
    if not token or not channel:
        return "skipped: missing env ARENA_ACCESS_TOKEN/ARENA_CHANNEL_SLUG"

    block_text = _claude_text(_arena_prompt(season, content, archive_url), max_tokens=500)
    title = f"{season['name_en']} · {season['name_jp']}"

    response = requests.post(
        f"https://api.are.na/v2/channels/{channel}/blocks",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"content": block_text, "title": title},
        timeout=30,
    )
    if response.status_code >= 400:
        return f"failed: HTTP {response.status_code} {response.text[:200]}"
    block_id = response.json().get("id")
    return f"posted: block {block_id}" if block_id else "posted"


# ── entry point ───────────────────────────────────────────────────────────────

def post_all(season: dict, content: dict, archive_url: str) -> dict:
    """Generate and publish social posts for a new micro-season.

    Returns a dict of ``{platform_name: status_string}``. Each platform runs
    independently; errors are caught, logged, and reflected in the status.
    """
    flat = normalize_content(content)["en"]

    season_label = f"#{season['id']:02d} {season['name_en']}"
    handlers = (
        ("twitter", _post_twitter),
        ("reddit", _post_reddit),
        ("arena", _post_arena),
    )

    results: dict[str, str] = {}
    for name, handler in handlers:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            status = handler(season, flat, archive_url)
            log.info("[%s] %s — %s — %s", ts, season_label, name, status)
        except Exception as e:  # noqa: BLE001 — never let social posting raise
            status = f"failed: {e}"
            log.warning("[%s] %s — %s — %s", ts, season_label, name, status)
        results[name] = status

    return results
