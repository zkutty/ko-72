"""Validate the per-page illustration selection and save exact generation prompts."""

from __future__ import annotations

import json
import math
from pathlib import Path


BOOK = Path(__file__).resolve().parent
MAX_ENTRIES = 12


def pages_for(entries: list[dict]) -> list[list[dict]]:
    page_count = math.ceil(len(entries) / MAX_ENTRIES)
    base, extra = divmod(len(entries), page_count)
    sizes = [base + (index < extra) for index in range(page_count)]
    pages = []
    cursor = 0
    for size in sizes:
        pages.append(entries[cursor:cursor + size])
        cursor += size
    return pages


def prompt_for(item: dict) -> str:
    left, right = item["items"]
    return (
        "Use case: illustration-story. Asset type: two separate ingredient spot illustrations "
        "for one Kō book glossary page. Make a WIDE LANDSCAPE two-panel study on warm lightly "
        "textured washi paper. LEFT HALF: " + left["subject"] + ". RIGHT HALF: " + right["subject"] + ". "
        "Exactly one named subject study in each half, with a clear central gutter and generous "
        "empty paper around each. Show identifiable natural form and anatomy; do not invent extra "
        "species, foods, hands, utensils, plates, scenery, labels, numbers, letters, logos, or borders. "
        "Style: quiet Japanese natural-history field illustration, fine slightly broken dark-brown "
        "sumi ink line, diluted watercolor/mineral pigment, restrained pigment pooling, modest paper "
        "grain. Warm washi #f5f3ee, ink #1a1a18; muted natural local subject colors. The two halves "
        "must be visually independent so they can be clipped into separate labeled image frames. "
        "This is draft illustrative art, not a certified identification plate."
    )


def main() -> None:
    glossary = json.loads((BOOK / "glossary.json").read_text())
    plan_path = BOOK / "glossary_illustration_plan.json"
    plan = json.loads(plan_path.read_text())
    expected = {}
    for category in ("fruit", "vegetable", "fish"):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        for index, page in enumerate(pages_for(entries), 1):
            expected[(category, index)] = {e["display_name"] for e in page}
    observed = set()
    labels_seen = set()
    prompts = BOOK / "prompts" / "glossary-pages"
    prompts.mkdir(parents=True, exist_ok=True)
    for item in plan["entries"]:
        key = (item["category"], item["page"])
        if key not in expected or key in observed:
            raise ValueError(f"Invalid or duplicate page selection: {key}")
        if len(item["items"]) != 2:
            raise ValueError(f"Exactly two studies required on {key}")
        for study in item["items"]:
            if study["label"] not in expected[key]:
                raise ValueError(f"{study['label']} is not indexed on {key}")
            identity = (item["category"], study["label"])
            if identity in labels_seen:
                raise ValueError(f"Repeated illustration subject: {identity}")
            labels_seen.add(identity)
        stem = f"{item['category']}-{item['page']:02d}"
        item["image_path"] = f"book/art/glossary/pages/{stem}.png"
        item["prompt_path"] = f"book/prompts/glossary-pages/{stem}.txt"
        (prompts / f"{stem}.txt").write_text(prompt_for(item) + "\n")
        observed.add(key)
    if observed != set(expected):
        raise ValueError(f"Illustration plan missing pages: {sorted(set(expected) - observed)}")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(observed)} glossary pages planned, {len(labels_seen)} distinct labeled studies")


if __name__ == "__main__":
    main()
