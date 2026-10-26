"""Make an editorial layout proof with complete food lists and a working glossary."""

from __future__ import annotations

import argparse
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


def glossary_cover(pdf: canvas.Canvas, image_path: Path, count: int,
                   source_count: int, page_count: int, study_count: int) -> None:
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
    pdf.drawImage(image, 18, 255, width=image_w, height=image_h, mask="auto")
    pdf.setStrokeColor(RULE)
    pdf.line(36, 235, PAGE_W - 36, 235)
    draw_paragraph(pdf, f"{count} foods consolidated from {source_count} source labels in currently cached season letters. Every listed fruit, vegetable, and fish has a name, a short food note, and season cross-reference. Food identities, Japanese spellings, and catalogue-derived notes need editorial and source review before print.", 36, 214, PAGE_W - 72, "Georgia", 9.5, 14)
    pdf.setFillColor(STONE)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(36, 48, f"{study_count} ITEM STUDIES / TWO ON EACH OF {page_count} CATEGORY PAGES")
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
    for part in range(3):
        page_background(pdf)
        pdf.setFillColor(INK)
        pdf.setFont("Georgia", 22)
        pdf.drawString(36, 551, "Season key")
        pdf.setFillColor(STONE)
        pdf.setFont("Helvetica", 7)
        pdf.drawString(36, 532, "CANONICAL KO IDS  /  APPROXIMATE START DATES")
        for column in range(2):
            for row in range(12):
                sid = part * 24 + column * 12 + row + 1
                season = seasons[sid]
                x = 36 + column * 164
                y = 498 - row * 35
                pdf.setFillColor(ACCENTS[season["major_season"]])
                pdf.rect(x, y - 2, 16, 2, stroke=0, fill=1)
                fitted_text(pdf, f"{sid:02d}", x, y + 6, 19, "Helvetica-Bold", 8, INK)
                fitted_text(pdf, season["name_en"], x + 23, y + 6, 137, "Georgia", 9, INK)
                fitted_text(pdf, season["name_jp"], x + 23, y - 7, 33,
                            "ArialUnicode", 7.5, STONE)
                pdf.setFillColor(STONE)
                pdf.setFont("Helvetica", 7)
                pdf.drawString(x + 65, y - 7,
                               f"{season['start_month']:02d}/{season['start_day']:02d}  ·  {season['major_season']}")
        pdf.setFillColor(STONE)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawString(36, 27, "DATES VARY SLIGHTLY BY YEAR / GLOSSARY REFERENCES SOURCE LETTERS")
        pdf.drawRightString(PAGE_W - 36, 27, f"{number:03d}")
        pdf.showPage()
        number += 1
    return number


def glossary_entry(pdf: canvas.Canvas, entry: dict, x: float, y: float,
                   width: float, selected_number: int | None,
                   seasons: dict[int, dict], description: str) -> float:
    """Set the complete name, season reference, and source-derived food note."""
    accent = ACCENTS[seasons[entry["season_ids"][0]]["major_season"]]
    if selected_number is not None:
        fitted_text(pdf, f"{selected_number:02d}", x, y, 13, "Helvetica-Bold", 7, accent)
    content_x = x + (17 if selected_number is not None else 0)
    text_width = width - (17 if selected_number is not None else 0)
    fitted_text(pdf, entry["english"], content_x, y, text_width, "Georgia", 10.4)
    written = f"{entry['kanji']}  ·  {entry['kana']}" if entry["kanji"] else entry["kana"]
    fitted_text(pdf, written, content_x, y - 12.5, text_width, "ArialUnicode", 8.8)
    ids = ", ".join(f"{sid:02d}" for sid in entry["season_ids"])
    fitted_text(pdf, f"{entry['romaji']}   /   KŌ {ids}", content_x, y - 24.5,
                text_width, "ArialUnicode", 7.3, STONE)
    bottom = draw_paragraph(pdf, description, content_x, y - 32,
                            text_width, "Georgia", 7.6, 9.2, INK)
    # The next title ascends above its baseline; allow room below the note.
    return y - bottom + 16


def floating_study(pdf: canvas.Canvas, image: ImageReader,
                   image_size: tuple[int, int], entry: dict,
                   number: int, x: float, top: float) -> None:
    """Draw an unframed cutout whose exclusion zone spans the nearby text."""
    frame_w, frame_h = 88, 70
    iw, ih = image_size
    scale = min(frame_w / iw, frame_h / ih)
    scaled_w, scaled_h = iw * scale, ih * scale
    pdf.drawImage(image, x + (frame_w - scaled_w) / 2,
                  top - frame_h + (frame_h - scaled_h) / 2,
                  width=scaled_w, height=scaled_h, mask="auto")
    fitted_text(pdf, f"{number:02d} / {entry['english']}", x, top - 79,
                frame_w, "ArialUnicode", 6.2, STONE)


def prepare_cutout(path: Path, panel: int | str, output: Path) -> None:
    """Crop transparent padding for typesetting; keep source art untouched."""
    with Image.open(path) as source:
        art = source.convert("RGBA")
    if panel in (0, 1):
        alpha = art.getchannel("A")
        width, height = art.size
        # The separator between the two studies may sit off exact center.
        candidates = range(round(width * .43), round(width * .57))
        split = min(candidates, key=lambda col: sum(
            alpha.getpixel((col, row)) > 20 for row in range(0, height, 5)))
        art = art.crop((0, 0, split, height) if panel == 0
                       else (split, 0, width, height))
    visible = art.getchannel("A").point(lambda value: 255 if value > 18 else 0)
    bounds = visible.getbbox()
    if not bounds:
        raise ValueError(f"Blank glossary cutout: {path}")
    padding = round(max(art.size) * .015)
    art = art.crop((max(0, bounds[0] - padding), max(0, bounds[1] - padding),
                    min(art.width, bounds[2] + padding),
                    min(art.height, bounds[3] + padding)))
    if max(art.size) > 480:
        art.thumbnail((480, 480), Image.Resampling.LANCZOS)
    art.save(output, format="PNG", optimize=True)


def build_glossary(glossary: dict, seasons: dict[int, dict], image_path: Path) -> None:
    pdf = canvas.Canvas(str(PROOFS / "ko-food-glossary-draft.pdf"), pagesize=(PAGE_W, PAGE_H))
    proof_images = TemporaryDirectory(prefix="ko-glossary-proof-")
    pdf.setTitle("Kō — illustrated fruit, vegetable, and fish glossary")
    plan_path = BOOK / "glossary_index_illustration_plan.json"
    plan = load(plan_path)
    descriptions = load(BOOK / "glossary_descriptions.json")["entries"]
    missing = {entry["catalog_key"] for entry in glossary["entries"]} - set(descriptions)
    if missing:
        raise ValueError(f"Missing glossary food notes: {sorted(missing)}")
    glossary_cover(pdf, image_path, glossary["entry_count"],
                   glossary["source_label_entries"],
                   len(plan["entries"]), sum(len(p["items"]) for p in plan["entries"]))
    page_number = 2
    art_pages = {(item["category"], item["page"]): item for item in plan["entries"]}
    proof_cache: dict[tuple[str, int | str], tuple[ImageReader, tuple[int, int]]] = {}
    for category, title in (("fruit", "Fruit"), ("vegetable", "Vegetables"), ("fish", "Fish & seafood")):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        cursor = 0
        for page_index, page in enumerate(pages_for(entries, category, plan_path), 1):
            study = art_pages[(category, page_index)]
            for selected in study["items"]:
                path = str(ROOT / selected["image_path"] if selected["origin"] == "new_transparent_art"
                           else BOOK / "art" / "glossary" / "cutouts" /
                           Path(selected["image_path"]).name)
                key = (path, selected["panel"])
                if key not in proof_cache:
                    picture = Path(path)
                    if not picture.exists():
                        raise ValueError(f"Missing glossary illustration: {picture}")
                    proof_picture = Path(proof_images.name) / f"study-{len(proof_cache):02d}.png"
                    with Image.open(picture) as source_image:
                        if "A" not in source_image.getbands():
                            raise ValueError(f"Cutout has no transparency: {picture}")
                    prepare_cutout(picture, selected["panel"], proof_picture)
                    reader = ImageReader(str(proof_picture))
                    proof_cache[key] = (reader, reader.getSize())
            page_background(pdf)
            pdf.setFillColor(INK)
            pdf.setFont("Georgia", 23)
            pdf.drawString(36, 555, title)
            pdf.setFillColor(STONE)
            pdf.setFont("Helvetica", 7)
            pdf.drawRightString(PAGE_W - 36, 557,
                                f"{cursor + 1}–{cursor + len(page)} OF {len(entries)}")
            cursor += len(page)
            pdf.setStrokeColor(RULE)
            pdf.line(36, 538, PAGE_W - 36, 538)
            # Selected entries use an art exclusion zone beside the complete
            # note. The following entry resumes the full text measure.
            y = 520
            for entry in page:
                numbered = next((number for number, item in enumerate(study["items"], 1)
                                 if item["label"] == entry["display_name"]), None)
                side = ("right" if (page_index + numbered) % 2 == 0 else "left") if numbered else None
                x = 136 if side == "left" else 36
                width = 224 if side else 324
                note = descriptions[entry["catalog_key"]]["text"]
                entry_height = glossary_entry(pdf, entry, x, y, width,
                                              numbered, seasons, note)
                if numbered is not None:
                    selected = study["items"][numbered - 1]
                    path = str(ROOT / selected["image_path"] if selected["origin"] == "new_transparent_art"
                               else BOOK / "art" / "glossary" / "cutouts" /
                               Path(selected["image_path"]).name)
                    reader, size = proof_cache[(path, selected["panel"])]
                    floating_study(pdf, reader, size, entry, numbered,
                                   272 if side == "right" else 36, y + 8)
                    # The illustration caption sits 71 pt below the entry
                    # baseline; leave clear space before the next title.
                    entry_height = max(entry_height, 96)
                y -= entry_height
            if y < 42:
                raise ValueError(f"Glossary text overflows on {category} page {page_index}: {y:.1f}")
            pdf.setFont("Helvetica", 6.1)
            pdf.setFillColor(STONE)
            pdf.drawString(36, 27, "STUDIES KEYED TO ENTRIES / KO IDS IN SEASON KEY / DRAFT")
            pdf.drawRightString(PAGE_W - 36, 27, f"{page_number:03d}")
            pdf.showPage()
            page_number += 1
    season_key(pdf, seasons, page_number)
    pdf.save()
    proof_images.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glossary-only", action="store_true")
    args = parser.parse_args()
    fonts()
    PROOFS.mkdir(exist_ok=True)
    seasons = {s["id"]: s for s in load(ROOT / "data" / "seasons.json")["seasons"]}
    cache = load(ROOT / "data" / "content_cache.json")
    art = load(BOOK / "art_manifest.json")["entries"]
    glossary = load(BOOK / "glossary_index.json")
    if glossary["source_seasons"] != len(cache):
        raise ValueError("Glossary is stale")
    if not args.glossary_only:
        build_seasons(seasons, cache, art)
    build_glossary(glossary, seasons, BOOK / "art" / "glossary" / "food-triptych-draft.png")
    print("Built food-inclusive season layout and working glossary proofs")


if __name__ == "__main__":
    main()
