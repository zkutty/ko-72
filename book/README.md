# Kō illustrated book pilot

This directory holds a design pilot for a future 72-season book. The newsletter and website do not consume these files.

## Files

- `BOOK_BRIEF.md` — format, editorial scope, sequence, and decision gates.
- `ART_DIRECTION.md` — proposed illustration grammar and pilot subject briefs.
- `art_manifest.json` and `prompts/` — source image paths, exact prompts, provenance, checksums, dimensions, and review notes.
- `inventory.json` — generated snapshot of all 72 source/art states; do not edit by hand.
- `art/source/` — original 1024 × 1536 pilot PNGs. These are design-resolution drafts, not final print exports.
- `proofs/` — a one-page contact sheet and nine-page four-season spread proof (title page plus four spreads).
- `build_glossary.py`, `glossary.json`, and `glossary_name_overrides.json` — reproducible working glossary from every fruit, vegetable, and fish label in cached letters. Every entry carries English, Japanese written form if present, kana reading, romaji, and canonical season IDs with full season references. All name readings, aliases, and seasonal claims require editorial review.
- `build_glossary_prompts.py`, `glossary_illustration_plan.json`, `prompts/glossary-pages/`, and `art/glossary/` — exact prompts and the original 21 paired image sheets plus 12 new single-item studies. The 26 current category pages select 52 distinct, numbered studies and place each immediately after its entry. Named page boundaries keep art references stable through small editorial corrections; repaginate deliberately as the glossary expands. These are draft identification art.
- `build_sections.py` and `section_inventory.json` — required section status for every one of the 72 seasons, including explicit pending slots.
- `build_food_draft.py` — a second, food-inclusive two-page-per-season layout proof and an illustrated working glossary proof in `proofs/`.
- `art/glossary/food-triptych-draft.png` and `glossary_art_manifest.json` — selected draft imagery for the glossary opener and image provenance.

## Rebuild and verify

From the repository root:

```sh
python3 book/build_inventory.py --check
python3 book/build_inventory.py              # refresh after new letters or art manifest edits
/Users/zbkutlow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 book/build_proof.py
```

The proof script currently uses the macOS supplemental Georgia and Arial Unicode fonts through ReportLab. It embeds Arial Unicode for Japanese characters. To move the layout to another host, configure available licensed fonts before rebuilding. Render and inspect every PDF page after changes. For example, with Poppler:

```sh
pdftoppm -png -r 110 book/proofs/ko-four-season-spread-proof.pdf /tmp/ko-spread
```

The contact sheet is for style comparison. The proof reuses cached English letter excerpts for IDs 24, 38, and 55 and explicitly marks ID 1's winter copy as pending. None of the copy or illustration subjects is certified for final publication. The current source images yield at most about 181 PPI if placed across the full proposed 5.5 × 8.5 inch page; final art production needs printer-specific resolution, crop, bleed, and color validation.

The food-inclusive proof shows every fruit, vegetable, and fish/seafood label from the three available pilot letters. Nature and culture prose are excerpts so the two-page format can be judged without implying a finished edit. Its winter page has empty, labeled slots. The glossary proof indexes every current food-list label with four name forms, season IDs, two inline illustrations per category page, and a three-page season key with English/Japanese names and approximate dates. The category pages allow at most ten entries and more vertical space for reading. Descriptions and alias consolidation remain pending. Regenerate and check with:

```sh
python3 book/build_glossary.py
python3 book/build_glossary.py --check
python3 book/build_glossary_prompts.py
python3 book/build_sections.py
python3 book/build_sections.py --check
python3 book/build_inventory.py --check
/Users/zbkutlow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 book/build_food_draft.py
```
