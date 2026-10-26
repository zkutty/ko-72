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
SYLLABLES = {
    "kya": "きゃ", "kyu": "きゅ", "kyo": "きょ", "sha": "しゃ", "shu": "しゅ", "sho": "しょ",
    "cha": "ちゃ", "chu": "ちゅ", "cho": "ちょ", "nya": "にゃ", "nyu": "にゅ", "nyo": "にょ",
    "hya": "ひゃ", "hyu": "ひゅ", "hyo": "ひょ", "mya": "みゃ", "myu": "みゅ", "myo": "みょ",
    "rya": "りゃ", "ryu": "りゅ", "ryo": "りょ", "gya": "ぎゃ", "gyu": "ぎゅ", "gyo": "ぎょ",
    "ja": "じゃ", "ju": "じゅ", "jo": "じょ", "bya": "びゃ", "byu": "びゅ", "byo": "びょ",
    "pya": "ぴゃ", "pyu": "ぴゅ", "pyo": "ぴょ", "shi": "し", "chi": "ち", "tsu": "つ",
    "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お",
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "sa": "さ", "su": "す", "se": "せ", "so": "そ",
    "ta": "た", "te": "て", "to": "と", "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "ha": "は", "hi": "ひ", "fu": "ふ", "he": "へ", "ho": "ほ",
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "ya": "や", "yu": "ゆ", "yo": "よ", "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "wa": "わ", "wo": "を", "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご",
    "za": "ざ", "ji": "じ", "zu": "ず", "ze": "ぜ", "zo": "ぞ",
    "da": "だ", "di": "ぢ", "du": "づ", "de": "で", "do": "ど",
    "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ",
    "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ",
}
MACRONS = str.maketrans({"ā": "aa", "ī": "ii", "ū": "uu", "ē": "ee", "ō": "ou"})


def key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def kana_from_romaji(value: str) -> str:
    source = value.lower().translate(MACRONS).replace("-", "").replace(" ", "")
    result = []
    pos = 0
    while pos < len(source):
        tail = source[pos:]
        if len(tail) > 1 and tail[0] == tail[1] and tail[0] not in "aeioun":
            result.append("っ")
            pos += 1
        elif tail[0] == "n" and (len(tail) == 1 or tail[1] not in "aeiouy"):
            result.append("ん")
            pos += 1
        else:
            for length in (3, 2, 1):
                if tail[:length] in SYLLABLES:
                    result.append(SYLLABLES[tail[:length]])
                    pos += length
                    break
            else:
                raise ValueError(f"Cannot derive kana for {value!r} at {tail!r}")
    return "".join(result)


def has_kanji(value: str) -> bool:
    return any(0x3400 <= ord(ch) <= 0x9FFF for ch in value)


def is_kana(value: str) -> bool:
    return all(0x3040 <= ord(ch) <= 0x30FF or ch in "ー・ " for ch in value)


def build() -> dict:
    cache = json.loads((ROOT / "data" / "content_cache.json").read_text())
    catalog = json.loads((ROOT / "data" / "ingredients.json").read_text())
    seasons = {item["id"]: item for item in json.loads((ROOT / "data" / "seasons.json").read_text())["seasons"]}
    overrides = json.loads((OUTPUT.parent / "glossary_name_overrides.json").read_text())
    matches = defaultdict(list)
    for slug, ingredient in catalog.items():
        for field in ("source", "name_en"):
            matches[(ingredient["category"], key(ingredient[field]), field)].append(slug)

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
                source_matches = matches.get((category, normalized, "source"), [])
                name_matches = matches.get((category, normalized, "name_en"), [])
                if len(source_matches) == 1:
                    slug, match_method = source_matches[0], "catalog_source_exact"
                elif len(name_matches) == 1:
                    slug, match_method = name_matches[0], "catalog_english_exact"
                elif identity in overrides["catalog_aliases"]:
                    slug, match_method = overrides["catalog_aliases"][identity], "explicit_alias"
                else:
                    raise ValueError(f"Unmapped glossary name: {identity}")
                ingredient = catalog[slug]
                jp = ingredient["name_jp"]
                romaji = ingredient["name_romaji"]
                if is_kana(jp):
                    kana, reading_method = jp, "catalog_kana"
                else:
                    kana = overrides["kana_readings"].get(romaji) or kana_from_romaji(romaji)
                    reading_method = "explicit_review_needed" if romaji in overrides["kana_readings"] else "derived_from_catalog_romaji"
                entry = entries.setdefault(identity, {
                    "category": category,
                    "display_name": label.strip(),
                    "english": ingredient["name_en"],
                    "kanji": jp if has_kanji(jp) else None,
                    "kana": kana,
                    "romaji": romaji,
                    "catalog_key": slug,
                    "name_match_method": match_method,
                    "reading_method": reading_method,
                    "name_review_status": "pending",
                    "source_labels": [],
                    "season_ids": [],
                    "entry_copy_status": "unverified",
                    "illustration_status": "not_selected",
                })
                if label.strip() not in entry["source_labels"]:
                    entry["source_labels"].append(label.strip())
                if int(sid) not in entry["season_ids"]:
                    entry["season_ids"].append(int(sid))
                mentions += 1

    ordered = sorted(entries.values(), key=lambda item: (item["category"], key(item["display_name"])))
    for entry in ordered:
        entry["season_refs"] = [
            {
                "id": sid,
                "name_en": seasons[sid]["name_en"],
                "name_jp": seasons[sid]["name_jp"],
                "start_month": seasons[sid]["start_month"],
                "start_day": seasons[sid]["start_day"],
                "major_season": seasons[sid]["major_season"],
            }
            for sid in sorted(entry["season_ids"])
        ]
    return {
        "status": "working_draft",
        "scope": "Seasonal produce in currently cached letters; regenerates as the remaining letters arrive",
        "source_seasons": len(cache),
        "source_mentions": mentions,
        "entry_count": len(ordered),
        "explicit_alias_mappings": sum(e["name_match_method"] == "explicit_alias" for e in ordered),
        "derived_kana_readings": sum(e["reading_method"] == "derived_from_catalog_romaji" for e in ordered),
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
          f"{result['explicit_alias_mappings']} explicit alias mappings, "
          f"{result['derived_kana_readings']} derived kana readings")


if __name__ == "__main__":
    main()
