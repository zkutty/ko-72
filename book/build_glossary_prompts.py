"""Validate the per-page illustration selection and save exact generation prompts."""

from __future__ import annotations

import json
import math
from pathlib import Path


BOOK = Path(__file__).resolve().parent
MAX_ENTRIES = 10


def pages_for(entries: list[dict], category: str | None = None) -> list[list[dict]]:
    if category is not None:
        plan = json.loads((BOOK / "glossary_illustration_plan.json").read_text())
        boundaries = [item["end_label"] for item in plan["entries"] if item["category"] == category]
        if not boundaries:
            raise ValueError(f"No glossary page boundaries for {category}")
        pages = []
        cursor = 0
        for boundary in boundaries:
            end = next((i + 1 for i in range(cursor, len(entries))
                        if entries[i]["display_name"] == boundary), None)
            if end is None:
                raise ValueError(f"Missing glossary page boundary {category}:{boundary}")
            page = entries[cursor:end]
            if not page or len(page) > MAX_ENTRIES:
                raise ValueError(f"Unreadable glossary page {category}:{boundary} has {len(page)} entries")
            pages.append(page)
            cursor = end
        if cursor != len(entries):
            raise ValueError(f"Unpaged glossary entries in {category}: {len(entries) - cursor}")
        return pages
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
    return (
        "Use case: illustration-story. Asset type: one ingredient spot illustration "
        "for a Kō book glossary page. Make a LANDSCAPE natural-history study on warm lightly "
        "textured washi paper. Subject: " + item["subject"] + ". "
        "Exactly one named subject study, centered with generous empty paper around it. "
        "Show identifiable natural form and anatomy; do not invent extra "
        "species, foods, hands, utensils, plates, scenery, labels, numbers, letters, logos, or borders. "
        "Style: quiet Japanese natural-history field illustration, fine slightly broken dark-brown "
        "sumi ink line, diluted watercolor/mineral pigment, restrained pigment pooling, modest paper "
        "grain. Warm washi #f5f3ee, ink #1a1a18; muted natural local subject colors. "
        "This is draft illustrative art, not a certified identification plate."
    )


def main() -> None:
    glossary = json.loads((BOOK / "glossary.json").read_text())
    plan_path = BOOK / "glossary_illustration_plan.json"
    plan = json.loads(plan_path.read_text())
    expected = {}
    for category in ("fruit", "vegetable", "fish"):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        for index, page in enumerate(pages_for(entries, category), 1):
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
            if study["origin"] == "new_inline_art":
                path = BOOK / "prompts" / "glossary-pages" / Path(study["prompt_path"]).name
                path.write_text(prompt_for(study) + "\n")
            elif study["origin"] != "paired_pilot_art" or study["panel"] not in (0, 1):
                raise ValueError(f"Invalid source art for {identity}")
            if not (BOOK.parent / study["prompt_path"]).exists():
                raise ValueError(f"Missing prompt for {identity}")
        observed.add(key)
    if observed != set(expected):
        raise ValueError(f"Illustration plan missing pages: {sorted(set(expected) - observed)}")
    print(f"{len(observed)} glossary pages planned, {len(labels_seen)} distinct labeled studies")


if __name__ == "__main__":
    main()
