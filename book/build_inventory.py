"""Build a reproducible book inventory without changing newsletter data."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK = Path(__file__).resolve().parent
INVENTORY = BOOK / "inventory.json"
ART_MANIFEST = BOOK / "art_manifest.json"
PILOT_IDS = {1, 24, 38, 55}
ART_STATES = {"not_started", "draft", "needs_revision", "approved"}


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def nonempty_block(value: object) -> bool:
    return isinstance(value, dict) and bool(value.get("opening"))


def png_dimensions(data: bytes) -> tuple[int, int]:
    if data[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or len(data) < 24:
        raise ValueError("art file is not a valid PNG header")
    return struct.unpack(">II", data[16:24])


def build() -> dict:
    seasons = read_json(ROOT / "data" / "seasons.json")["seasons"]
    cache = read_json(ROOT / "data" / "content_cache.json")
    art = read_json(ART_MANIFEST)
    if art.get("schema_version") != 1 or not isinstance(art.get("entries"), dict):
        raise ValueError("art_manifest.json must have schema_version 1 and entries object")
    ids = [item["id"] for item in seasons]
    if sorted(ids) != list(range(1, 73)) or len(ids) != len(set(ids)):
        raise ValueError("seasons.json must contain each ID 1–72 exactly once")
    if set(cache) - {str(i) for i in ids}:
        raise ValueError("content_cache.json contains an unknown season ID")
    if set(art["entries"]) - {str(i) for i in ids}:
        raise ValueError("art_manifest.json contains an unknown season ID")

    entries = []
    for season in seasons:
        sid = season["id"]
        raw = cache.get(str(sid))
        if raw is None:
            en, ja = False, False
        elif isinstance(raw, dict) and "en" in raw:
            en, ja = nonempty_block(raw.get("en")), nonempty_block(raw.get("ja"))
        else:
            en, ja = nonempty_block(raw), False

        image = art["entries"].get(str(sid), {})
        if not isinstance(image, dict):
            raise ValueError(f"art entry {sid} must be an object")
        state = image.get("status", "not_started")
        if state not in ART_STATES:
            raise ValueError(f"invalid art status for {sid}: {state}")
        if image.get("path"):
            path = ROOT / image["path"]
            if not path.is_file() or not path.resolve().is_relative_to(BOOK):
                raise ValueError(f"missing or outside-book art path for {sid}: {image['path']}")
            data = path.read_bytes()
            if (image.get("width_px"), image.get("height_px")) != png_dimensions(data):
                raise ValueError(f"art dimensions mismatch for {sid}")
            if image.get("sha256") != hashlib.sha256(data).hexdigest():
                raise ValueError(f"art checksum mismatch for {sid}")
            prompt_path = ROOT / image.get("prompt_path", "")
            if (not prompt_path.is_file()
                    or not prompt_path.resolve().is_relative_to(BOOK)
                    or prompt_path.read_text(encoding="utf-8").strip() != image.get("prompt")):
                raise ValueError(f"art prompt mismatch for {sid}")
        elif state != "not_started":
            raise ValueError(f"art path missing for {sid} with status {state}")

        entries.append({
            "id": sid,
            "name_en": season["name_en"],
            "name_jp": season["name_jp"],
            "name_romaji": season["name_romaji"],
            "slug": season["slug"],
            "major_season": season["major_season"],
            "start_month": season["start_month"],
            "start_day": season["start_day"],
            "source_status": "bilingual" if en and ja else "english_only" if en else "unpublished",
            "english_source": en,
            "japanese_source": ja,
            "book_review_status": "not_started",
            "art_status": state,
            "art_path": image.get("path"),
            "pilot": sid in PILOT_IDS,
        })

    counts = {
        "total": len(entries),
        "bilingual": sum(e["source_status"] == "bilingual" for e in entries),
        "english_only": sum(e["source_status"] == "english_only" for e in entries),
        "unpublished": sum(e["source_status"] == "unpublished" for e in entries),
        "art_draft": sum(e["art_status"] == "draft" for e in entries),
        "art_approved": sum(e["art_status"] == "approved" for e in entries),
    }
    return {"schema_version": 1, "counts": counts, "entries": entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if inventory.json is stale")
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not INVENTORY.is_file() or INVENTORY.read_text(encoding="utf-8") != rendered:
            raise SystemExit("book/inventory.json is stale; run python book/build_inventory.py")
        print("book inventory current")
    else:
        INVENTORY.write_text(rendered, encoding="utf-8")
        print("book inventory written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
