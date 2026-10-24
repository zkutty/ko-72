"""Track required book sections for all 72 seasons without inventing missing copy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "section_inventory.json"
TEXT = ("opening", "nature_notes", "cultural_note", "haiku")
LISTS = ("fruits", "vegetables", "fish")


def build() -> dict:
    seasons = json.loads((ROOT / "data" / "seasons.json").read_text())["seasons"]
    cache = json.loads((ROOT / "data" / "content_cache.json").read_text())
    if len(seasons) != 72 or {s["id"] for s in seasons} != set(range(1, 73)):
        raise ValueError("Expected exactly 72 canonical season IDs")
    entries = []
    for season in seasons:
        sid = season["id"]
        raw = cache.get(str(sid))
        content = raw.get("en", raw) if raw else None
        sections = {}
        for name in TEXT:
            value = content.get(name) if content else None
            present = bool(value)
            if name == "haiku":
                present = isinstance(value, dict) and bool(value.get("japanese") and value.get("english"))
            sections[name] = "source_available" if present else "pending_source"
        produce = content.get("seasonal_produce", {}) if content else {}
        for name in LISTS:
            value = produce.get(name)
            sections[name] = "source_available" if isinstance(value, list) and bool(value) else "pending_source"
        dishes = content.get("seasonal_dishes") if content else None
        sections["dishes"] = "source_available" if isinstance(dishes, list) and bool(dishes) else "pending_source"
        entries.append({
            "season_id": sid,
            "season_name": season["name_en"],
            "source_letter": "cached" if content else "pending",
            "sections": sections,
            "book_edit": "not_started",
            "fact_review": "not_started",
        })
    return {"status": "working_draft", "required_sections": [*TEXT, *LISTS, "dishes"], "entries": entries}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.check:
        if not OUTPUT.exists() or json.loads(OUTPUT.read_text()) != result:
            raise SystemExit("book/section_inventory.json is stale; run book/build_sections.py")
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    available = sum(e["source_letter"] == "cached" for e in result["entries"])
    print(f"{len(result['entries'])} season templates; {available} cached letters; {72 - available} pending")


if __name__ == "__main__":
    main()
