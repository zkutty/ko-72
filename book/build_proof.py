"""Build the four-season design proof and contact sheet from local source data."""

from __future__ import annotations

import html
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
BOOK = Path(__file__).resolve().parent
PROOFS = BOOK / "proofs"
PAGE_W, PAGE_H = 5.5 * 72, 8.5 * 72
WASHI = colors.HexColor("#f5f3ee")
INK = colors.HexColor("#1a1a18")
STONE = colors.HexColor("#888780")
RULE = colors.HexColor("#d8d5ce")
ACCENTS = {
    "spring": colors.HexColor("#6b8f71"),
    "summer": colors.HexColor("#c9734a"),
    "autumn": colors.HexColor("#d4a853"),
    "winter": colors.HexColor("#4a7fa5"),
}
PILOTS = [24, 38, 55, 1]


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def fonts() -> None:
    font_dir = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("Georgia", str(font_dir / "Georgia.ttf")))
    pdfmetrics.registerFont(TTFont("GeorgiaItalic", str(font_dir / "Georgia Italic.ttf")))
    pdfmetrics.registerFont(TTFont("ArialUnicode", str(font_dir / "Arial Unicode.ttf")))


def page_background(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(WASHI)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)


def draw_paragraph(pdf: canvas.Canvas, value: str, x: float, top: float,
                   width: float, font: str, size: float, leading: float,
                   color: colors.Color = INK) -> float:
    style = ParagraphStyle("book", fontName=font, fontSize=size, leading=leading,
                           textColor=color, spaceAfter=0, allowWidows=0, allowOrphans=0)
    paragraph = Paragraph(html.escape(value), style)
    _, height = paragraph.wrap(width, PAGE_H)
    paragraph.drawOn(pdf, x, top - height)
    return top - height


def art_page(pdf: canvas.Canvas, image_path: Path, page_number: int) -> None:
    page_background(pdf)
    image = ImageReader(str(image_path))
    iw, ih = image.getSize()
    scale = min(PAGE_W / iw, PAGE_H / ih)
    w, h = iw * scale, ih * scale
    pdf.drawImage(image, (PAGE_W - w) / 2, (PAGE_H - h) / 2,
                  width=w, height=h, preserveAspectRatio=True, mask="auto")
    pdf.setFont("Georgia", 8)
    pdf.setFillColor(STONE)
    pdf.drawString(28, 19, f"Kō   /   {page_number:03d}")
    pdf.showPage()


def text_page(pdf: canvas.Canvas, season: dict, content: dict | None,
              page_number: int) -> None:
    page_background(pdf)
    accent = ACCENTS[season["major_season"]]
    left, right = 42, PAGE_W - 42
    width = right - left
    y = PAGE_H - 43

    pdf.setFillColor(accent)
    pdf.rect(left, y + 3, 18, 2, fill=1, stroke=0)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(left + 25, y, f"{season['major_season'].upper()}  /  MICRO-SEASON {season['id']:02d}")
    y -= 44
    pdf.setFillColor(INK)
    pdf.setFont("ArialUnicode", 28)
    pdf.drawString(left, y, season["name_jp"])
    y -= 37
    y = draw_paragraph(pdf, season["name_en"], left, y, width, "Georgia", 21, 24)
    y -= 8
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(STONE)
    pdf.drawString(left, y, season["name_romaji"])
    y -= 21
    pdf.setStrokeColor(RULE)
    pdf.setLineWidth(0.5)
    pdf.line(left, y, right, y)
    y -= 19

    if content is None:
        y = draw_paragraph(pdf,
            "EDITORIAL COPY PENDING", left, y, width, "Georgia", 11, 16, accent)
        y -= 14
        y = draw_paragraph(pdf,
            "The winter letter is not in the source cache yet. This spread tests image scale, type hierarchy, margins, and the winter palette only.",
            left, y, width, "Georgia", 11, 17)
        y -= 20
        y = draw_paragraph(pdf,
            "No seasonal observations, food notes, cultural claims, or haiku have been invented for this proof.",
            left, y, width, "Helvetica", 9.5, 14, STONE)
    else:
        y = draw_paragraph(pdf, content["opening"], left, y, width,
                           "Georgia", 10.2, 15.1)
        y -= 13
        y = draw_paragraph(pdf, content["nature_notes"], left, y, width,
                           "Helvetica", 9, 13.4)
        y -= 13
        y = draw_paragraph(pdf, content["cultural_note"], left, y, width,
                           "Helvetica", 9, 13.4)
        y -= 17
        pdf.setStrokeColor(RULE)
        pdf.line(left, y, right, y)
        y -= 18
        y = draw_paragraph(pdf, content["haiku"]["japanese"], left, y, width,
                           "ArialUnicode", 11.5, 18)
        y -= 7
        y = draw_paragraph(pdf, content["haiku"]["english"], left, y, width,
                           "GeorgiaItalic", 9.5, 14, STONE)

    if y < 55:
        raise ValueError(f"Text overflow on season {season['id']}: bottom={y:.1f}")
    pdf.setFont("Helvetica", 6.6)
    pdf.setFillColor(STONE)
    pdf.drawString(left, 27, "DESIGN PROOF  ·  COPY AND SUBJECTS NOT FACT-CHECKED")
    pdf.drawRightString(right, 27, f"{page_number:03d}")
    pdf.showPage()


def build_spreads(seasons: dict[int, dict], cache: dict, art: dict) -> None:
    path = PROOFS / "ko-four-season-spread-proof.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    pdf.setTitle("Kō — four-season book spread proof")
    page_background(pdf)
    pdf.setFillColor(INK)
    pdf.setFont("Georgia", 39)
    pdf.drawString(44, PAGE_H - 155, "Kō")
    pdf.setFont("ArialUnicode", 31)
    pdf.drawString(120, PAGE_H - 153, "候")
    pdf.setStrokeColor(RULE)
    pdf.line(44, PAGE_H - 177, PAGE_W - 44, PAGE_H - 177)
    pdf.setFont("Georgia", 21)
    pdf.drawString(44, PAGE_H - 225, "The Year, in Seventy-Two")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(STONE)
    pdf.drawString(44, PAGE_H - 255, "FOUR-SEASON ILLUSTRATED BOOK PILOT")
    pdf.drawString(44, 65, "24 OCTOBER 2026  /  DESIGN PROOF")
    pdf.showPage()

    for offset, sid in enumerate(PILOTS):
        season = seasons[sid]
        image_path = ROOT / art[str(sid)]["path"]
        entry = cache.get(str(sid))
        content = entry.get("en", entry) if isinstance(entry, dict) else None
        art_page(pdf, image_path, 2 + offset * 2)
        text_page(pdf, season, content, 3 + offset * 2)
    pdf.save()


def build_contact(seasons: dict[int, dict], art: dict) -> None:
    path = PROOFS / "ko-four-season-contact-sheet.pdf"
    w, h = 11 * 72, 5.5 * 72
    pdf = canvas.Canvas(str(path), pagesize=(w, h))
    pdf.setTitle("Kō — four-season illustration contact sheet")
    pdf.setFillColor(WASHI)
    pdf.rect(0, 0, w, h, fill=1, stroke=0)
    pdf.setFont("Georgia", 19)
    pdf.setFillColor(INK)
    pdf.drawString(30, h - 35, "Kō / Four seasons")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(STONE)
    pdf.drawRightString(w - 30, h - 31, "ILLUSTRATION SYSTEM — DRAFT PILOTS")
    card_w = 165
    gap = 25
    x0 = (w - (4 * card_w + 3 * gap)) / 2
    for i, sid in enumerate(PILOTS):
        season = seasons[sid]
        x = x0 + i * (card_w + gap)
        y = 52
        image = ImageReader(str(ROOT / art[str(sid)]["path"]))
        iw, ih = image.getSize()
        image_h = 246
        image_w = image_h * iw / ih
        pdf.drawImage(image, x + (card_w - image_w) / 2, y + 42,
                      width=image_w, height=image_h)
        pdf.setStrokeColor(ACCENTS[season["major_season"]])
        pdf.setLineWidth(2)
        pdf.line(x, y + 35, x + card_w, y + 35)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(STONE)
        pdf.drawString(x, y + 22, f"{season['major_season'].upper()} / {sid:02d}")
        pdf.setFillColor(INK)
        draw_paragraph(pdf, season["name_en"], x, y + 12, card_w,
                       "Georgia", 8.5, 10.5)
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(STONE)
    pdf.drawString(30, 15, "Visual pilots only. Subject accuracy, final crop, color, and print resolution remain open.")
    pdf.save()


def main() -> None:
    fonts()
    PROOFS.mkdir(exist_ok=True)
    seasons = {s["id"]: s for s in load(ROOT / "data" / "seasons.json")["seasons"]}
    cache = load(ROOT / "data" / "content_cache.json")
    art = load(BOOK / "art_manifest.json")["entries"]
    for sid in PILOTS:
        if art[str(sid)]["status"] != "draft":
            raise ValueError(f"Pilot {sid} is not a draft image")
    build_spreads(seasons, cache, art)
    build_contact(seasons, art)
    print("Built four-season spread proof and contact sheet")


if __name__ == "__main__":
    main()
