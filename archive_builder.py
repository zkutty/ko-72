"""
Build static HTML archive pages, index, and website homepage.
"""

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from wheel import cardinal_labels

ARCHIVE_DIR = Path(__file__).parent / "archive"
TEMPLATE_DIR = Path(__file__).parent / "templates"
ROOT_DIR     = Path(__file__).parent

ACCENT_COLORS = {
    "spring": "#6b8f71",
    "summer": "#c9734a",
    "autumn": "#d4a853",
    "winter": "#4a7fa5",
}


def _fmt(month: int, day: int) -> str:
    return date(2000, month, day).strftime("%b %-d")  # "Apr 20"


def _date_range(season: dict) -> str:
    return f"{_fmt(season['start_month'], season['start_day'])} – {_fmt(season['end_month'], season['end_day'])}"


def _season_filename(season: dict) -> str:
    return f"{season['id']:02d}-{season['slug']}.html"


def _accent(season: dict) -> str:
    return ACCENT_COLORS.get(season["major_season"].lower(), "#888780")


def _published_ids(all_seasons: list) -> set:
    return {s["id"] for s in all_seasons if (ARCHIVE_DIR / _season_filename(s)).exists()}


# ── Individual archive page ────────────────────────────────────────────────────

def build_archive(season: dict, content: dict, all_seasons: list) -> None:
    ARCHIVE_DIR.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

    pub_ids = _published_ids(all_seasons)
    # prev = nearest lower published id; next = nearest higher published id
    lower  = [s for s in all_seasons if s["id"] < season["id"] and s["id"] in pub_ids]
    higher = [s for s in all_seasons if s["id"] > season["id"] and s["id"] in pub_ids]
    prev   = lower[-1]  if lower  else None
    next_s = higher[0]  if higher else None

    html = env.get_template("archive_page.html").render(
        season=season,
        content=content,
        accent_color=_accent(season),
        date_range=_date_range(season),
        duration_days=season["duration_days"],
        prev=prev,
        next=next_s,
        all_seasons=all_seasons,
    )

    filename = _season_filename(season)
    (ARCHIVE_DIR / filename).write_text(html, encoding="utf-8")
    print(f"Archive page written: archive/{filename}")

    _build_index(env, all_seasons)


# ── Archive index ──────────────────────────────────────────────────────────────

def _build_index(env: Environment, all_seasons: list) -> None:
    published_count = sum(
        1 for s in all_seasons if (ARCHIVE_DIR / _season_filename(s)).exists()
    )
    html = env.get_template("archive_index.html").render(
        all_seasons=all_seasons,
        published_count=published_count,
    )
    (ARCHIVE_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Archive index updated — {published_count} season(s) published.")


# ── Website homepage ───────────────────────────────────────────────────────────

def build_website(
    season: dict,
    content: dict,
    all_seasons: list,
    worker_url: str = "https://subscribe.ko-72.com",
) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

    # Recent: last 5 published seasons (for the "Recently" block)
    recent = [
        {"season": s, "url": s["url"]}
        for s in all_seasons
        if (ARCHIVE_DIR / _season_filename(s)).exists()
    ][-5:]

    html = env.get_template("website.html").render(
        season=season,
        content=content,
        accent_color=_accent(season),
        date_range=_date_range(season),
        duration_days=season["duration_days"],
        all_seasons=all_seasons,
        recent=recent,
        worker_url=worker_url,
        cardinals=cardinal_labels(),
    )
    (ROOT_DIR / "index.html").write_text(html, encoding="utf-8")
    print("Website homepage rebuilt: index.html")
