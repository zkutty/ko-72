"""Make an editorial layout proof with complete food lists and a working glossary."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from reportlab.lib.utils import ImageReader
from build_glossary_prompts import pages_for
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
    pdf.drawString(36, 48, "42 ITEM STUDIES / TWO ON EACH OF 21 CATEGORY PAGES")
    pdf.drawString(36, 29, "DESIGN PROOF / IMAGE SUBJECTS AND COPY UNVERIFIED")
    pdf.showPage()


def fitted_text(pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float,
                font: str, size: float, color=INK) -> None:
    while size > 6 and pdf.stringWidth(text, font, size) > max_width:
        size -= 0.2
    if pdf.stringWidth(text, font, size) > max_width:
        raise ValueError(f"Glossary text does not fit: {text}")
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, text)


def season_key(pdf: canvas.Canvas, seasons: dict[int, dict], number: int) -> int:
    for half in range(2):
        page_background(pdf)
        pdf.setFillColor(INK)
        pdf.setFont("Georgia", 22)
        pdf.drawString(36, 551, "Season key")
        pdf.setFillColor(STONE)
        pdf.setFont("Helvetica", 7)
        pdf.drawString(36, 532, "CANONICAL KO IDS  /  APPROXIMATE START DATES")
        for column in range(2):
            for row in range(18):
                sid = half * 36 + column * 18 + row + 1
                season = seasons[sid]
                x = 36 + column * 164
                y = 504 - row * 25
                pdf.setFillColor(ACCENTS[season["major_season"]])
                pdf.rect(x, y - 1, 16, 2, stroke=0, fill=1)
                fitted_text(pdf, f"{sid:02d}", x, y + 5, 19, "Helvetica-Bold", 7, INK)
                fitted_text(pdf, season["name_en"], x + 23, y + 5, 137, "Georgia", 8, INK)
                pdf.setFillColor(STONE)
                pdf.setFont("Helvetica", 6.2)
                pdf.drawString(x + 23, y - 5, f"{season['start_month']:02d}/{season['start_day']:02d}  ·  {season['major_season']}")
        pdf.setFillColor(STONE)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawString(36, 27, "DATES VARY SLIGHTLY BY YEAR / GLOSSARY REFERENCES SOURCE LETTERS")
        pdf.drawRightString(PAGE_W - 36, 27, f"{number:03d}")
        pdf.showPage()
        number += 1
    return number


def build_glossary(glossary: dict, seasons: dict[int, dict], image_path: Path) -> None:
    pdf = canvas.Canvas(str(PROOFS / "ko-food-glossary-draft.pdf"), pagesize=(PAGE_W, PAGE_H))
    proof_images = TemporaryDirectory(prefix="ko-glossary-proof-")
    pdf.setTitle("Kō — illustrated fruit, vegetable, and fish glossary")
    glossary_cover(pdf, image_path, glossary["entry_count"])
    page_number = 2
    plan = load(BOOK / "glossary_illustration_plan.json")
    art_pages = {(item["category"], item["page"]): item for item in plan["entries"]}
    for category, title in (("fruit", "Fruit"), ("vegetable", "Vegetables"), ("fish", "Fish & seafood")):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        cursor = 0
        for page_index, page in enumerate(pages_for(entries), 1):
            study = art_pages[(category, page_index)]
            picture = ROOT / study["image_path"]
            if not picture.exists():
                raise ValueError(f"Missing glossary illustration: {picture}")
            proof_picture = Path(proof_images.name) / f"{category}-{page_index:02d}.jpg"
            with Image.open(picture) as source_image:
                proof_height = round(1400 * source_image.height / source_image.width)
                source_image.convert("RGB").resize((1400, proof_height)).save(
                    proof_picture, format="JPEG", quality=86, optimize=True)
            page_background(pdf)
            pdf.setFillColor(INK)
            pdf.setFont("Georgia", 22)
            pdf.drawString(36, 556, title)
            pdf.setFillColor(STONE)
            pdf.setFont("Helvetica", 7)
            pdf.drawRightString(PAGE_W - 36, 558,
                                f"WORKING GLOSSARY / {cursor + 1}–{cursor + len(page)} OF {len(entries)}")
            cursor += len(page)
            # One image sheet contains two independent item studies. Clip each
            # half into a distinct frame without changing the source artwork.
            frame_y, frame_h, frame_w = 466, 69, 155
            source = ImageReader(str(proof_picture))
            iw, ih = source.getSize()
            for index, selected in enumerate(study["items"]):
                x = 36 + index * 173
                pdf.saveState()
                clip = pdf.beginPath()
                clip.rect(x, frame_y, frame_w, frame_h)
                pdf.clipPath(clip, stroke=0, fill=0)
                scaled_w = frame_w * 2
                scaled_h = scaled_w * ih / iw
                pdf.drawImage(source, x - index * frame_w, frame_y + (frame_h - scaled_h) / 2,
                              width=scaled_w, height=scaled_h)
                pdf.restoreState()
                fitted_text(pdf, f"{index + 1}  {selected['label']}", x, 452, frame_w,
                            "ArialUnicode", 7.2, STONE)
            for row_index, entry in enumerate(page):
                y = 426 - row_index * 32
                marker = next((str(i + 1) for i, item in enumerate(study["items"])
                               if item["label"] == entry["display_name"]), "")
                fitted_text(pdf, marker, 36, y, 10, "Helvetica-Bold", 7,
                            ACCENTS[seasons[entry["season_ids"][0]]["major_season"]])
                fitted_text(pdf, entry["english"], 48, y, 174, "Georgia", 8.7)
                written = f"{entry['kanji']}  ·  {entry['kana']}" if entry["kanji"] else entry["kana"]
                fitted_text(pdf, written, 224, y, 132, "ArialUnicode", 8.1)
                fitted_text(pdf, entry["romaji"], 48, y - 11, 159, "ArialUnicode", 7.1, STONE)
                ids = ", ".join(f"{sid:02d}" for sid in entry["season_ids"])
                fitted_text(pdf, f"IN SEASON  {ids}", 209, y - 11, 147, "Helvetica", 6.5, STONE)
                if entry["display_name"].casefold() != entry["english"].casefold():
                    fitted_text(pdf, f"SOURCE  {entry['display_name']}", 48, y - 20, 308,
                                "ArialUnicode", 5.9, STONE)
                pdf.setStrokeColor(RULE)
                pdf.line(36, y - 28, PAGE_W - 36, y - 28)
            pdf.setFont("Helvetica", 6.1)
            pdf.setFillColor(STONE)
            pdf.drawString(36, 27, "IMAGE NUMBERS MATCH ENTRIES / FULL SEASON NAMES IN KEY / DRAFT")
            pdf.drawRightString(PAGE_W - 36, 27, f"{page_number:03d}")
            pdf.showPage()
            page_number += 1
    season_key(pdf, seasons, page_number)
    pdf.save()
    proof_images.cleanup()


def main() -> None:
    fonts()
    PROOFS.mkdir(exist_ok=True)
    seasons = {s["id"]: s for s in load(ROOT / "data" / "seasons.json")["seasons"]}
    cache = load(ROOT / "data" / "content_cache.json")
    art = load(BOOK / "art_manifest.json")["entries"]
    glossary = load(BOOK / "glossary.json")
    if glossary["source_seasons"] != len(cache):
        raise ValueError("Glossary is stale")
    build_seasons(seasons, cache, art)
    build_glossary(glossary, seasons, BOOK / "art" / "glossary" / "food-triptych-draft.png")
    print("Built food-inclusive season layout and working glossary proofs")


if __name__ == "__main__":
    main()
