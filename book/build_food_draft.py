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


def glossary_cover(pdf: canvas.Canvas, image_path: Path, count: int,
                   page_count: int, study_count: int) -> None:
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
                   selected_number: int | None, seasons: dict[int, dict]) -> None:
    """Draw one entry as a quiet, fixed-height reading block."""
    content_x = x + 13
    accent = ACCENTS[seasons[entry["season_ids"][0]]["major_season"]]
    if selected_number is not None:
        fitted_text(pdf, str(selected_number), x, y, 9, "Helvetica-Bold", 7.2, accent)
    fitted_text(pdf, entry["english"], content_x, y, 140, "Georgia", 9.4)
    written = f"{entry['kanji']}  ·  {entry['kana']}" if entry["kanji"] else entry["kana"]
    fitted_text(pdf, written, content_x, y - 12, 140, "ArialUnicode", 8.5)
    fitted_text(pdf, entry["romaji"], content_x, y - 22, 140, "ArialUnicode", 7.7, STONE)
    ids = ", ".join(f"{sid:02d}" for sid in entry["season_ids"])
    fitted_text(pdf, f"IN SEASON  {ids}", content_x, y - 32, 140, "Helvetica", 7.2, STONE)
    if entry["display_name"].casefold() != entry["english"].casefold():
        fitted_text(pdf, f"SOURCE  {entry['display_name']}", content_x, y - 42,
                    140, "ArialUnicode", 6.0, STONE)
    pdf.setStrokeColor(RULE)
    pdf.line(content_x, y - 47, x + 153, y - 47)


def inline_study(pdf: canvas.Canvas, image: ImageReader, image_size: tuple[int, int],
                 selected: dict, number: int, x: float, top: float) -> None:
    """Place the matching image immediately after its entry, within its column."""
    frame_w, frame_h = 153, 78
    iw, ih = image_size
    frame_bottom = top - 82
    if selected["panel"] == "full":
        scale = min(frame_w / iw, frame_h / ih)
        scaled_w, scaled_h = iw * scale, ih * scale
        draw_x = x + (frame_w - scaled_w) / 2
        clip_x, clip_w = x, frame_w
    else:
        half_w = min(frame_w, frame_h * (iw / (2 * ih)) * 1.25)
        scaled_w = half_w * 2
        scaled_h = scaled_w * ih / iw
        clip_x, clip_w = x + (frame_w - half_w) / 2, half_w
        draw_x = clip_x - selected["panel"] * half_w
    pdf.saveState()
    clip = pdf.beginPath()
    clip.rect(clip_x, frame_bottom, clip_w, frame_h)
    pdf.clipPath(clip, stroke=0, fill=0)
    pdf.drawImage(image, draw_x, frame_bottom + (frame_h - scaled_h) / 2,
                  width=scaled_w, height=scaled_h)
    pdf.restoreState()
    fitted_text(pdf, f"{number}  {selected['label']}", x, top - 92, frame_w,
                "ArialUnicode", 7.2, STONE)


def build_glossary(glossary: dict, seasons: dict[int, dict], image_path: Path) -> None:
    pdf = canvas.Canvas(str(PROOFS / "ko-food-glossary-draft.pdf"), pagesize=(PAGE_W, PAGE_H))
    proof_images = TemporaryDirectory(prefix="ko-glossary-proof-")
    pdf.setTitle("Kō — illustrated fruit, vegetable, and fish glossary")
    plan = load(BOOK / "glossary_illustration_plan.json")
    glossary_cover(pdf, image_path, glossary["entry_count"],
                   len(plan["entries"]), sum(len(p["items"]) for p in plan["entries"]))
    page_number = 2
    art_pages = {(item["category"], item["page"]): item for item in plan["entries"]}
    proof_cache: dict[str, tuple[ImageReader, tuple[int, int]]] = {}
    for category, title in (("fruit", "Fruit"), ("vegetable", "Vegetables"), ("fish", "Fish & seafood")):
        entries = [e for e in glossary["entries"] if e["category"] == category]
        cursor = 0
        for page_index, page in enumerate(pages_for(entries, category), 1):
            study = art_pages[(category, page_index)]
            for selected in study["items"]:
                path = selected["image_path"]
                if path not in proof_cache:
                    picture = ROOT / path
                    if not picture.exists():
                        raise ValueError(f"Missing glossary illustration: {picture}")
                    proof_picture = Path(proof_images.name) / f"study-{len(proof_cache):02d}.jpg"
                    with Image.open(picture) as source_image:
                        proof_height = round(1400 * source_image.height / source_image.width)
                        source_image.convert("RGB").resize((1400, proof_height)).save(
                            proof_picture, format="JPEG", quality=86, optimize=True)
                    reader = ImageReader(str(proof_picture))
                    proof_cache[path] = (reader, reader.getSize())
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
            pdf.line(198, 515, 198, 49)
            # Each study follows its corresponding entry, so the art moves
            # naturally through the two text columns rather than forming a
            # detached banner at the top of every page.
            midpoint = (len(page) + 1) // 2
            for col_index, column in enumerate((page[:midpoint], page[midpoint:])):
                x = 36 + col_index * 171
                y = 515
                art_count = sum(entry["display_name"] in
                                {item["label"] for item in study["items"]} for entry in column)
                entry_step = min(70, (515 - 48 - art_count * 103) / len(column))
                if entry_step < 52:
                    raise ValueError(f"No readable glossary spacing on {category} page {page_index}")
                for entry in column:
                    numbered = next((i + 1 for i, item in enumerate(study["items"])
                                     if item["label"] == entry["display_name"]), None)
                    glossary_entry(pdf, entry, x, y, numbered, seasons)
                    y -= entry_step
                    if numbered is not None:
                        selected = study["items"][numbered - 1]
                        reader, size = proof_cache[selected["image_path"]]
                        inline_study(pdf, reader, size, selected, numbered, x, y)
                        y -= 103
                if y < 48:
                    raise ValueError(f"Glossary column overflows on {category} page {page_index}: {y}")
            pdf.setFont("Helvetica", 6.1)
            pdf.setFillColor(STONE)
            pdf.drawString(36, 27, "NUMBERED STUDIES FOLLOW THEIR ENTRIES / SEASON KEY AT BACK / DRAFT")
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
