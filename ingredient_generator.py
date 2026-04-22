"""
Generate one-time lookup entries for every seasonal ingredient and dish that
appears in data/content_cache.json.

The produce (fruits, vegetables, fish) and dishes that Kō features don't change
year to year, so we only need to write prose about each unique item once. This
script walks the existing content cache, dedupes by a stable slug, and calls
Claude for any item not yet recorded in data/ingredients.json or data/dishes.json.

Usage:
    python ingredient_generator.py            # generate for any new items
    python ingredient_generator.py --force    # regenerate even if already present
    python ingredient_generator.py --dry-run  # print what would be generated
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DATA_DIR       = Path(__file__).parent / "data"
CACHE_PATH     = DATA_DIR / "content_cache.json"
INGREDIENTS_P  = DATA_DIR / "ingredients.json"
DISHES_P       = DATA_DIR / "dishes.json"

MODEL = "claude-opus-4-5"

SYSTEM_PROMPT = """You are a poetic writer with deep knowledge of Japanese food \
culture, traditional seasonal produce, and the shichijūni-kō calendar. Your \
prose is concrete, sensory, and quietly precise — wabi-sabi in register. You \
never resort to generic descriptions; you find the particular detail that \
makes a reader recognize the thing.

Always respond with valid JSON only — no markdown, no preamble, no explanation."""


def slugify(s: str) -> str:
    """Stable key for an ingredient or dish string.

    Keeps romaji and English tokens, drops punctuation. Both the generator and
    the archive builder MUST use this function so keys align.
    """
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# ── discovery ─────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def collect_items(cache: dict) -> tuple[dict, dict]:
    """Walk every cached season and return two dicts keyed by slug.

    Returns (ingredients, dishes), where each value is the canonical source
    string (with category for ingredients).
    """
    ingredients: dict[str, dict] = {}
    dishes: dict[str, dict] = {}

    for season in cache.values():
        produce = season.get("seasonal_produce", {})
        for category, items in produce.items():
            # category is "fruits" / "vegetables" / "fish"
            singular = {"fruits": "fruit", "vegetables": "vegetable", "fish": "fish"}.get(category, category)
            for raw in items:
                key = slugify(raw)
                if not key:
                    continue
                if key not in ingredients:
                    ingredients[key] = {"source": raw, "category": singular}

        for d in season.get("seasonal_dishes", []):
            raw = d.get("name", "")
            key = slugify(raw)
            if not key:
                continue
            if key not in dishes:
                dishes[key] = {"source": raw}

    return ingredients, dishes


# ── Claude calls ──────────────────────────────────────────────────────────────

def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def generate_ingredient(client: anthropic.Anthropic, raw: str, category: str) -> dict:
    user_prompt = f"""Write a short reference entry for this Japanese seasonal {category}:

Source string (as it appears in our newsletter): "{raw}"

Return a JSON object with exactly these fields:

{{
  "name_en": "Common English name (singular, e.g. 'Bamboo shoot')",
  "name_jp": "Japanese kanji or kana (e.g. '筍')",
  "name_romaji": "romanized Japanese (e.g. 'takenoko')",
  "category": "{category}",
  "peak": "A short phrase naming the peak period (e.g. 'Mid-spring, when the \
grain rains soften the earth')",
  "note": "Two concise sentences. The first grounds the reader in what this \
{category} actually is and why it's prized right now — one sensory or culinary \
detail that makes it specific. The second places it in the rhythm of the \
Japanese year or kitchen."
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message.content[0].text)


def generate_dish(client: anthropic.Anthropic, raw: str) -> dict:
    user_prompt = f"""Write a short reference entry for this traditional Japanese dish:

Source string (as it appears in our newsletter): "{raw}"

Return a JSON object with exactly these fields:

{{
  "name_en": "Plain-English gloss of the dish (e.g. 'Bamboo-shoot rice')",
  "name_jp": "Japanese kanji or kana (e.g. '筍ご飯')",
  "name_romaji": "romanized Japanese (e.g. 'takenoko gohan')",
  "season": "A short phrase for when the dish is made (e.g. 'Mid-spring, during the first bamboo harvest')",
  "note": "Two concise sentences. The first describes what the dish actually \
is — the cooking method and the one or two ingredients that define it. The \
second tells the reader why it belongs to a particular moment of the Japanese \
year, grounded in a concrete detail."
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message.content[0].text)


# ── main ──────────────────────────────────────────────────────────────────────

def run(force: bool = False, dry_run: bool = False) -> dict:
    """Generate any missing ingredient / dish entries. Safe to call repeatedly.

    Returns a small stats dict so callers (e.g. season_mailer) can log.
    """
    if not CACHE_PATH.exists():
        log.warning("No content cache at %s — skipping ingredient generation.", CACHE_PATH)
        return {"ingredients_added": 0, "dishes_added": 0}

    cache = _load_json(CACHE_PATH)
    discovered_ing, discovered_dish = collect_items(cache)

    existing_ing  = _load_json(INGREDIENTS_P)
    existing_dish = _load_json(DISHES_P)

    ing_todo  = {k: v for k, v in discovered_ing.items()  if force or k not in existing_ing}
    dish_todo = {k: v for k, v in discovered_dish.items() if force or k not in existing_dish}

    log.info(
        "Discovered %d ingredients (%d new) and %d dishes (%d new) across %d seasons.",
        len(discovered_ing), len(ing_todo),
        len(discovered_dish), len(dish_todo),
        len(cache),
    )

    if dry_run:
        for k, v in ing_todo.items():
            log.info("  [ingredient] %s  ←  %s", k, v["source"])
        for k, v in dish_todo.items():
            log.info("  [dish]       %s  ←  %s", k, v["source"])
        return {"ingredients_added": 0, "dishes_added": 0}

    if not ing_todo and not dish_todo:
        log.info("Everything already generated. Nothing to do.")
        return {"ingredients_added": 0, "dishes_added": 0}

    client = _client()
    added_ing = 0
    added_dish = 0

    for i, (key, meta) in enumerate(ing_todo.items(), 1):
        log.info("Ingredient %d/%d · %s (%s)", i, len(ing_todo), meta["source"], meta["category"])
        try:
            entry = generate_ingredient(client, meta["source"], meta["category"])
        except Exception as e:
            log.error("  failed: %s — skipping.", e)
            continue
        entry["source"] = meta["source"]
        existing_ing[key] = entry
        _save_json(INGREDIENTS_P, existing_ing)
        added_ing += 1

    for i, (key, meta) in enumerate(dish_todo.items(), 1):
        log.info("Dish %d/%d · %s", i, len(dish_todo), meta["source"])
        try:
            entry = generate_dish(client, meta["source"])
        except Exception as e:
            log.error("  failed: %s — skipping.", e)
            continue
        entry["source"] = meta["source"]
        existing_dish[key] = entry
        _save_json(DISHES_P, existing_dish)
        added_dish += 1

    log.info(
        "Done. %d ingredients and %d dishes on disk.",
        len(existing_ing), len(existing_dish),
    )
    return {"ingredients_added": added_ing, "dishes_added": added_dish}


def main() -> None:
    parser = argparse.ArgumentParser(description="Kō ingredient / dish lookup generator")
    parser.add_argument("--force", action="store_true", help="Regenerate entries that already exist")
    parser.add_argument("--dry-run", action="store_true", help="List work without calling Claude")
    args = parser.parse_args()
    run(force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
