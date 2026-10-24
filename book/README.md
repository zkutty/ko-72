# Kō illustrated book pilot

This directory holds a design pilot for a future 72-season book. The newsletter and website do not consume these files.

## Files

- `BOOK_BRIEF.md` — format, editorial scope, sequence, and decision gates.
- `ART_DIRECTION.md` — proposed illustration grammar and pilot subject briefs.
- `art_manifest.json` and `prompts/` — source image paths, exact prompts, provenance, checksums, dimensions, and review notes.
- `inventory.json` — generated snapshot of all 72 source/art states; do not edit by hand.
- `art/source/` — original 1024 × 1536 pilot PNGs. These are design-resolution drafts, not final print exports.
- `proofs/` — a one-page contact sheet and nine-page four-season spread proof (title page plus four spreads).

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
