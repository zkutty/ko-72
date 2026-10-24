"""Make an editorial layout proof with complete food lists and a working glossary."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from build_proof import (
    ACCENTS, BOOK, INK, PAGE_H, PAGE_W, PILOTS, PROOFS, ROOT, RULE, STONE,
    art_page, draw_paragraph, fonts, load, page_background,
)


FOOD_FIELDS = (("FRUIT", "fruits"), ("VEGETABLES", "vegetables"), ("FISH & SEAFOOD", "fish"))


def first_sentence(value: str) -> str:
    return value.split(". ", 1)[0].rstrip(".") + "."


def text_page(pdf: canvas.Canvas, season: dict, content: dict | None, number: int) -> None:
    page_background(pdf)
    left, right, width = 36, PAGE_W - 36, PAGE_W - 72
    accent = ACCENTS[season["major_season"]]
    pdf.setFillColor(accent)
    pdf.rect(left, 565, 20, 2, stroke=0, fill=1)
    pdf.setFont("Helvetica", 7.2)
    pdf.drawString(left + 27, 563, f"{season['major_season'].upper()}  /  MICRO-SEASON {season['id']:02d}")
    pdf.setFillColor(INK)
    pdf.setFont("ArialUnicode", 23)
    pdf.drawString(left, 526, season["name_jp"])
    y = draw_paragraph(pdf, season["name_en"], left, 515, width, "Georgia", 17, 20)
    pdf.setFillColor(STONE)
    pdf.setFont("ArialUnicode", 8)
    pdf.drawString(left, y - 9, season["name_romaji"])
    y -= 28
    pdf.setStrokeColor(RULE)
    pdf.line(left, y, right, y)
    y -= 14

    if content is None:
        pdf.setFillColor(accent)
        pdf.setFont("Georgia", 10)
        pdf.drawString(left, y - 10, "EDITORIAL COPY PENDING")
        y -= 32
        pdf.setFillColor(STONE)
        y = draw_paragraph(pdf, "Fruit, vegetables, fish, dishes, nature, culture, and haiku remain unfilled until this season's source letter is available and reviewed.", left, y, width, "Helvetica", 9, 13, STONE)
        y -= 25
        for heading, _ in FOOD_FIELDS:
            pdf.setFont("Helvetica", 8)
            pdf.drawString(left, y, heading)
            pdf.line(left + 110, y - 2, right, y - 2)
            y -= 43
    else:
        y = draw_paragraph(pdf, content["summary"], left, y, width, "Georgia", 9.2, 13)
        y -= 7
        y = draw_paragraph(pdf, "NATURE  /  " + first_sentence(content["nature_notes"]), left, y, width, "ArialUnicode", 8.2, 11.4)
        y -= 13
        pdf.setFillColor(accent)
        pdf.setFont("Georgia", 11)
        pdf.drawString(left, y, "Seasonal food")
        y -= 14
        food_top = y
        col_w = (width - 14) / 3
        bottoms = []
        for index, (heading, field) in enumerate(FOOD_FIELDS):
            x = left + index * (col_w + 7)
            cy = food_top
            pdf.setFillColor(accent)
            pdf.setFont("Helvetica-Bold", 7)
            pdf.drawString(x, cy, heading)
            cy -= 13
            labels = content["seasonal_produce"][field]
            if not labels:
                raise ValueError(f"Season {season['id']} has no {field}")
            for label in labels:
                cy = draw_paragraph(pdf, label, x, cy, col_w - 2, "ArialUnicode", 7.5, 9.2)
                cy -= 4
            bottoms.append(cy)
        y = min(bottoms) - 10
        pdf.setStrokeColor(RULE)
        pdf.line(left, y, right, y)
        y -= 15
        dish_names = "; ".join(d["name"] for d in content["seasonal_dishes"])
        y = draw_paragraph(pdf, "AT THE TABLE  /  " + dish_names, left, y, width, "ArialUnicode", 8.1, 11.5)
        y -= 10
        y = draw_paragraph(pdf, "CULTURE  /  " + first_sentence(content["cultural_note"]), left, y, width, "ArialUnicode", 8.1, 11.5)
        y -= 13
        pdf.setStrokeColor(RULE)
        pdf.line(left, y, right, y)
        y -= 15
        y = draw_paragraph(pdf, content["haiku"]["japanese"], left, y, width, "ArialUnicode", 10, 14)
        y -= 5
        y = draw_paragraph(pdf, content["haiku"]["english"], left, y, width, "GeorgiaItalic", 8.5, 11.5, STONE)

    if y < 48:
        raise ValueError(f"Food spread overflows for season {season['id']}: {y:.1f}")
    pdf.setFillColor(STONE)
    pdf.setFont("Helvetica", 6.3)
    pdf.drawString(left, 25, "EDITORIAL EXCERPTS / ALL FOOD LIST ITEMS SHOWN / UNVERIFIED DRAFT")
    pdf.drawRightString(right, 25, f"{number:03d}")
    pdf.showPage()


def build_seasons(seasons: dict, cache: dict, art: dict) -> None:
    pdf = canvas.Canvas(str(PROOFS / "ko-four-season-food-layout.pdf"), pagesize=(PAGE_W, PAGE_H))
    pdf.setTitle("Kō — two-page season layout with food sections")
    page_background(pdf)
    pdf.setFillColor(INK)
    pdf.setFont("Georgia", 36)
    pdf.drawString(36, 465, "Kō")
    pdf.setFont("Georgia", 19)
    pdf.drawString(36, 425, "The year, in seventy-two")
    pdf.setStrokeColor(RULE)
    pdf.line(36, 403, PAGE_W - 36, 403)
    pdf.setFillColor(STONE)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(36, 378, "FOOD-INCLUSIVE TWO-PAGE SEASON PILOT")
    pdf.drawString(36, 50, "DESIGN PROOF / EDITORIAL EXCERPTS / NOT FOR PRINT")
    pdf.showPage()
    for offset, sid in enumerate(PILOTS):
        source = cache.get(str(sid))
        content = source.get("en", source) if source else None
        art_page(pdf, ROOT / art[str(sid)]["path"], 2 + offset * 2)
        text_page(pdf, seasons[sid], content, 3 + offset * 2)
    pdf.save()


def glossary_cover(pdf: canvas.Canvas, image_path: Path, count: int) -> None:
    page_background(pdf)
    pdf.setFillColor(INK)
    pdf.setFont("Georgia", 27)
    pdf.drawString(36, 553, "Food of the")
    pdf.drawString(36, 519, "seventy-two seasons")
    pdf.setFillColor(STONE)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(36, 487, "WORKING GLOSSARY / FRUIT · VEGETABLES · FISH & SEAFOOD")
    image = ImageReader(str(image_path))
    iw, ih = image.getSize()
    image_w = PAGE_W - 36
    image_h = image_w * ih / iw
    pdf.drawImage(image, 18, 255, width=image_w, height=image_h)
    pdf.setStrokeColor(RULE)
    pdf.line(36, 235, PAGE_W - 36, 235)
    draw_paragraph(pdf, f"{count} distinct source labels from currently cached season letters. Every listed fruit, vegetable, and fish has an entry and season cross-reference. Names, duplicate aliases, Japanese spellings, and descriptions need editorial and source review before print.", 36, 214, PAGE_W - 72, "Georgia", 9.5, 14)
    pdf.setFillColor(STONE)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(36, 48, "ILLUSTRATED STUDIES: LOQUAT · FAVA BEANS · HORSE MACKEREL")
    pdf.drawString(36, 29, "DESIGN PROOF / IMAGE SUBJECTS AND COPY UNVERIFIED")
    pdf.showPage()


def build_glossary(glossary: dict, catalog: dict, image_path: Path) -> None:
    pdf = canvas.Canvas(str(PROOFS / "ko-food-glossary-draft.pdf"), pagesize=(PAGE_W, PAGE_H))
    pdf.setTitle("Kō — working fruit, vegetable, and fish glossary")
    glossary_cover(pdf, image_path, glossary["entry_count"])
    page_number = 2
    for category, title in (("fruit", "Fruit"), ("vegetable", "Vegetables"), ("fish", "Fish & seafood")):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        for start in range(0, len(entries), 12):
            page_background(pdf)
            pdf.setFillColor(INK)
            pdf.setFont("Georgia", 23)
            pdf.drawString(36, 556, title)
            pdf.setFillColor(STONE)
            pdf.setFont("Helvetica", 7)
            pdf.drawRightString(PAGE_W - 36, 558, f"WORKING GLOSSARY / {start + 1}–{min(start + 12, len(entries))} OF {len(entries)}")
            y = 522
            for entry in entries[start:start + 12]:
                pdf.setFillColor(INK)
                name_font = "ArialUnicode" if any(ord(ch) > 127 for ch in entry["display_name"]) else "Georgia"
                pdf.setFont(name_font, 9.5)
                pdf.drawString(36, y, entry["display_name"][:48])
                pdf.setFillColor(STONE)
                pdf.setFont("Helvetica", 7)
                refs = ", ".join(f"{sid:02d}" for sid in entry["season_ids"])
                pdf.drawRightString(PAGE_W - 36, y, refs)
                if len(entry["catalog_candidates"]) == 1:
                    item = catalog[entry["catalog_candidates"][0]]
                    detail = f"{item.get('name_romaji') or '—'}  /  catalog name match; description pending review"
                else:
                    detail = "Name or alias mapping pending editorial review"
                draw_paragraph(pdf, detail, 36, y - 6, PAGE_W - 72, "ArialUnicode", 7.2, 9, STONE)
                pdf.setStrokeColor(RULE)
                pdf.line(36, y - 27, PAGE_W - 36, y - 27)
                y -= 37
            pdf.setFont("Helvetica", 6.5)
            pdf.setFillColor(STONE)
            pdf.drawString(36, 27, "SEASON NUMBERS ARE CANONICAL IDS / COPY AND IDENTITIES UNVERIFIED")
            pdf.drawRightString(PAGE_W - 36, 27, f"{page_number:03d}")
            pdf.showPage()
            page_number += 1
    pdf.save()


def main() -> None:
    fonts()
    PROOFS.mkdir(exist_ok=True)
    seasons = {s["id"]: s for s in load(ROOT / "data" / "seasons.json")["seasons"]}
    cache = load(ROOT / "data" / "content_cache.json")
    art = load(BOOK / "art_manifest.json")["entries"]
    glossary = load(BOOK / "glossary.json")
    catalog = load(ROOT / "data" / "ingredients.json")
    if glossary["source_seasons"] != len(cache):
        raise ValueError("Glossary is stale")
    build_seasons(seasons, cache, art)
    build_glossary(glossary, catalog, BOOK / "art" / "glossary" / "food-triptych-draft.png")
    print("Built food-inclusive season layout and working glossary proofs")


if __name__ == "__main__":
    main()
