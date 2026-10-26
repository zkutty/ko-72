"""Make one book entry per food while retaining every source label and season.

Only exact catalog IDs, Japanese written form plus reading, or English names
establish an automatic identity. Conflicting names are recorded for review.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

BOOK = Path(__file__).resolve().parent
RAW = BOOK / "glossary.json"
INDEX = BOOK / "glossary_index.json"
REPORT = BOOK / "glossary_duplicate_report.json"
ART = BOOK / "glossary_illustration_plan.json"
PAGE_PLAN = BOOK / "glossary_index_illustration_plan.json"
MAX_ENTRIES = 5


def key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def collapse(raw: dict) -> tuple[dict, dict, dict[tuple[str, str], str]]:
    entries = raw["entries"]
    parent = list(range(len(entries)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(first: int, second: int) -> None:
        parent[find(first)] = find(second)

    for identity in (
        lambda e: (e["category"], e["catalog_key"]),
        lambda e: (e["category"], e["kanji"] or e["kana"], key(e["romaji"])),
        lambda e: (e["category"], key(e["english"])),
    ):
        seen = {}
        for index, entry in enumerate(entries):
            value = identity(entry)
            if value in seen:
                join(index, seen[value])
            else:
                seen[value] = index

    groups = defaultdict(list)
    for index, entry in enumerate(entries):
        groups[find(index)].append(entry)

    canonical = []
    duplicate_groups = []
    label_to_id = {}
    for group in groups.values():
        category = group[0]["category"]
        # Choose the most frequently indexed English form, then a stable tie.
        english = sorted(
            {entry["english"] for entry in group},
            key=lambda name: (-sum(len(e["season_ids"]) for e in group
                                   if key(e["english"]) == key(name)),
                              len(name), key(name)),
        )[0]
        representative = sorted(
            group,
            key=lambda e: (key(e["english"]) != key(english),
                           -len(e["season_ids"]), e["kanji"] is None,
                           key(e["display_name"])),
        )[0]
        labels = list(dict.fromkeys(
            label for entry in group for label in entry["source_labels"]
        ))
        season_refs = {}
        for entry in group:
            for ref in entry["season_refs"]:
                season_refs[ref["id"]] = ref
        catalog_keys = sorted({entry["catalog_key"] for entry in group})
        canonical_id = f"{category}:{catalog_keys[0]}"
        written = {(e["kanji"] or e["kana"], key(e["romaji"])) for e in group}
        english_forms = {key(e["english"]) for e in group}
        needs_review = len(written) > 1 or len(english_forms) > 1
        item = {
            "id": canonical_id,
            "category": category,
            "display_name": english,
            "english": english,
            "kanji": representative["kanji"],
            "kana": representative["kana"],
            "romaji": representative["romaji"],
            "catalog_key": representative["catalog_key"],
            "source_catalog_keys": catalog_keys,
            "source_labels": labels,
            "source_entry_count": len(group),
            "season_ids": sorted(season_refs),
            "season_refs": [season_refs[sid] for sid in sorted(season_refs)],
            "identity_review_status": "needs_editorial_review" if needs_review else "pending",
            "entry_copy_status": "unverified",
            "source_entries": [
                {"label": e["display_name"], "labels": e["source_labels"],
                 "catalog_key": e["catalog_key"],
                 "season_ids": e["season_ids"]} for e in group
            ],
        }
        canonical.append(item)
        for entry in group:
            lookup = (category, entry["display_name"])
            if lookup in label_to_id and label_to_id[lookup] != canonical_id:
                raise ValueError(f"Source label has two identities: {lookup}")
            label_to_id[lookup] = canonical_id
        if len(group) > 1:
            duplicate_groups.append({
                "id": canonical_id,
                "display_name": english,
                "labels": labels,
                "catalog_keys": catalog_keys,
                "season_ids": item["season_ids"],
                "identity_review_status": item["identity_review_status"],
            })

    canonical.sort(key=lambda e: (e["category"], key(e["display_name"])))
    duplicate_groups.sort(key=lambda e: e["id"])
    possible_duplicates = []
    stage_words = {"early", "late", "ripe", "green", "young", "new", "spring", "summer"}
    for left_index, left in enumerate(canonical):
        for right in canonical[left_index + 1:]:
            if left["category"] != right["category"]:
                continue
            reasons = []
            if key(left["romaji"]) == key(right["romaji"]):
                reasons.append("same_romaji")
            if left["kana"] == right["kana"]:
                reasons.append("same_kana")
            left_words = key(left["english"]).split()
            right_words = key(right["english"]).split()
            if ((left_words and left_words[0] in stage_words
                 and " ".join(left_words[1:]) == " ".join(right_words))
                    or (right_words and right_words[0] in stage_words
                        and " ".join(right_words[1:]) == " ".join(left_words))):
                reasons.append("seasonal_stage_name")
            if reasons:
                possible_duplicates.append({"left_id": left["id"], "right_id": right["id"],
                                            "left_name": left["english"],
                                            "right_name": right["english"],
                                            "reasons": reasons, "decision": "review; not merged"})
    index = {
        "status": "working_draft",
        "scope": raw["scope"],
        "source_seasons": raw["source_seasons"],
        "source_mentions": raw["source_mentions"],
        "source_label_entries": len(entries),
        "entry_count": len(canonical),
        "entries": canonical,
    }
    report = {
        "status": "editorial_review_pending",
        "source_label_entries": len(entries),
        "canonical_entries": len(canonical),
        "collapsed_entries": len(entries) - len(canonical),
        "duplicate_groups": duplicate_groups,
        "review_groups": [g["id"] for g in duplicate_groups
                          if g["identity_review_status"] == "needs_editorial_review"],
        "possible_duplicates": possible_duplicates,
        "rule": "Merge exact catalog key, exact Japanese written form and romaji, or exact English name within a category; review divergent forms.",
    }
    validate(raw, index, report)
    return index, report, label_to_id


def validate(raw: dict, index: dict, report: dict) -> None:
    originals = raw["entries"]
    canonical = index["entries"]
    if len(originals) - len(canonical) != report["collapsed_entries"]:
        raise ValueError("Duplicate counts do not reconcile")
    if sum(e["source_entry_count"] for e in canonical) != len(originals):
        raise ValueError("A source entry was lost or counted twice")
    original_records = sorted((e["category"], e["display_name"], e["catalog_key"],
                               tuple(e["source_labels"]), tuple(e["season_ids"]))
                              for e in originals)
    indexed_records = sorted((e["category"], source["label"], source["catalog_key"],
                              tuple(source["labels"]), tuple(source["season_ids"]))
                             for e in canonical for source in e["source_entries"])
    if original_records != indexed_records:
        raise ValueError("Source entries changed during consolidation")
    if sum(len(e["season_ids"]) for e in originals) < len(canonical):
        raise ValueError("Season references were lost")
    for entry in canonical:
        source_ids = {sid for source in entry["source_entries"]
                      for sid in source["season_ids"]}
        if set(entry["season_ids"]) != source_ids:
            raise ValueError(f"Season references changed for {entry['id']}")
    for identity in (
        lambda e: (e["category"], key(e["english"])),
        lambda e: (e["category"], e["kanji"] or e["kana"], key(e["romaji"])),
    ):
        values = [identity(e) for e in canonical]
        if len(values) != len(set(values)):
            raise ValueError("Duplicate identity remains in the printed index")


def paginate(entries: list[dict], illustrated: set[str]) -> list[list[dict]]:
    """Use the fewest readable pages that each have two distinct art subjects."""
    count = len(entries)
    best: list[tuple[int, list[int]] | None] = [None] * (count + 1)
    best[count] = (0, [])
    for start in range(count - 1, -1, -1):
        options = []
        for end in range(start + 1, min(count, start + MAX_ENTRIES) + 1):
            art_count = sum(e["id"] in illustrated for e in entries[start:end])
            if art_count < 2 or best[end] is None:
                continue
            tail_cost, tail_ends = best[end]
            cost = 100 + (MAX_ENTRIES - (end - start)) ** 2 + tail_cost
            options.append((cost, [end, *tail_ends]))
        if options:
            best[start] = min(options, key=lambda option: (option[0], option[1]))
    if best[0] is None:
        raise ValueError("Cannot place two distinct existing studies on every category page")
    pages = []
    cursor = 0
    for end in best[0][1]:
        pages.append(entries[cursor:end])
        cursor = end
    return pages


def illustration_plan(index: dict, source_plan: dict,
                      label_to_id: dict[tuple[str, str], str]) -> dict:
    available = defaultdict(list)
    for page in source_plan["entries"]:
        for study in page["items"]:
            source = (page["category"], study["label"])
            if source not in label_to_id:
                raise ValueError(f"Illustration has no source entry: {source}")
            available[label_to_id[source]].append(study)
    plan = []
    for category in ("fruit", "vegetable", "fish"):
        entries = [e for e in index["entries"] if e["category"] == category]
        for page_number, page in enumerate(paginate(entries, set(available)), 1):
            candidates = [i for i, e in enumerate(page) if available.get(e["id"])]
            first, last = candidates[0], candidates[-1]
            chosen = [page[first], page[last]]
            studies = []
            for entry in chosen:
                # Prefer an exact source label for the chosen display form.
                source = sorted(available[entry["id"]],
                                key=lambda s: (key(s["label"]) != key(entry["display_name"]),
                                               key(s["label"])))[0]
                studies.append({**source, "source_label": source["label"],
                                "label": entry["display_name"], "entry_id": entry["id"]})
            plan.append({"category": category, "page": page_number,
                         "items": studies, "end_label": page[-1]["display_name"]})
    return {"status": "draft", "layout": "At most five canonical foods and two unique keyed studies per category page", "entries": plan}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=RAW)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.loads(args.input.read_text())
    index, report, label_to_id = collapse(raw)
    plan = illustration_plan(index, json.loads(ART.read_text()), label_to_id)
    outputs = ((INDEX, index), (REPORT, report), (PAGE_PLAN, plan))
    for path, payload in outputs:
        if args.check:
            if not path.exists() or json.loads(path.read_text()) != payload:
                raise SystemExit(f"{path} is stale; run book/build_glossary_index.py")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(raw['entries'])} source labels -> {index['entry_count']} foods; "
          f"{report['collapsed_entries']} repeated entries collapsed; "
          f"{len(plan['entries'])} category pages")


if __name__ == "__main__":
    main()
