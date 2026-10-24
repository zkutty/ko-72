"""Build a source-grounded working glossary from the season food lists.

No fuzzy alias merge is attempted: different names may refer to one ingredient,
but that decision needs an editor. The coverage check is exact for every list.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "glossary.json"
CATEGORIES = {"fruits": "fruit", "vegetables": "vegetable", "fish": "fish"}


def key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def build() -> dict:
    cache = json.loads((ROOT / "data" / "content_cache.json").read_text())
    catalog = json.loads((ROOT / "data" / "ingredients.json").read_text())
    matches = defaultdict(list)
    for slug, ingredient in catalog.items():
        matches[(ingredient["category"], key(ingredient["name_en"]))].append(slug)

    entries = {}
    mentions = 0
    for sid, raw in sorted(cache.items(), key=lambda pair: int(pair[0])):
        content = raw.get("en", raw)
        produce = content.get("seasonal_produce") or {}
        for field, category in CATEGORIES.items():
            labels = produce.get(field)
            if not isinstance(labels, list) or not labels:
                raise ValueError(f"Season {sid} is missing its {field} list")
            for label in labels:
                if not isinstance(label, str) or not label.strip():
                    raise ValueError(f"Season {sid} has an invalid {field} label")
                normalized = key(label)
                identity = f"{category}:{normalized}"
                entry = entries.setdefault(identity, {
                    "category": category,
                    "display_name": label.strip(),
                    "source_labels": [],
                    "season_ids": [],
                    "catalog_candidates": matches.get((category, normalized), []),
                    "entry_copy_status": "unverified",
                    "illustration_status": "not_selected",
                })
                if label.strip() not in entry["source_labels"]:
                    entry["source_labels"].append(label.strip())
                if int(sid) not in entry["season_ids"]:
                    entry["season_ids"].append(int(sid))
                mentions += 1

    ordered = sorted(entries.values(), key=lambda item: (item["category"], key(item["display_name"])))
    return {
        "status": "working_draft",
        "scope": "Seasonal produce in currently cached letters; regenerates as the remaining letters arrive",
        "source_seasons": len(cache),
        "source_mentions": mentions,
        "entry_count": len(ordered),
        "unmatched_catalog_names": sum(not e["catalog_candidates"] for e in ordered),
        "entries": ordered,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.check:
        if not OUTPUT.exists() or json.loads(OUTPUT.read_text()) != result:
            raise SystemExit("book/glossary.json is stale; run book/build_glossary.py")
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"{result['source_seasons']} letters, {result['source_mentions']} mentions, "
          f"{result['entry_count']} distinct draft labels, "
          f"{result['unmatched_catalog_names']} without exact catalog-name match")


if __name__ == "__main__":
    main()
