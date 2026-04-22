"""
Build static HTML archive pages, index, and website homepage.
"""

import json
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ingredient_generator import slugify
from wheel import cardinal_labels

ARCHIVE_DIR = Path(__file__).parent / "archive"
TEMPLATE_DIR = Path(__file__).parent / "templates"
ROOT_DIR     = Path(__file__).parent
DATA_DIR     = ROOT_DIR / "data"

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


def _load_lookup() -> tuple[dict, dict]:
    def _read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return _read(DATA_DIR / "ingredients.json"), _read(DATA_DIR / "dishes.json")


def _slice_lookups(content: dict, ingredients: dict, dishes: dict) -> tuple[dict, dict]:
    """Return only the lookup entries that appear on this season's page.

    Keeps per-page JSON small and annotates each produce / dish item with the
    slug the template needs to render a clickable lookup button.
    """
    page_ing: dict[str, dict] = {}
    page_dish: dict[str, dict] = {}

    for items in content.get("seasonal_produce", {}).values():
        for raw in items:
            key = slugify(raw)
            if key and key in ingredients:
                page_ing[key] = ingredients[key]

    for d in content.get("seasonal_dishes", []):
        key = slugify(d.get("name", ""))
        if key and key in dishes:
            page_dish[key] = dishes[key]

    return page_ing, page_dish


def _keyed_produce(content: dict, ingredients: dict) -> dict:
    """Transform content.seasonal_produce into lists of {raw, key} pairs."""
    out: dict[str, list] = {}
    for category, items in content.get("seasonal_produce", {}).items():
        out[category] = [
            {"raw": raw, "key": slugify(raw) if slugify(raw) in ingredients else None}
            for raw in items
        ]
    return out


def _keyed_dishes(content: dict, dishes: dict) -> list:
    """Transform content.seasonal_dishes into dicts that carry the lookup key."""
    out = []
    for d in content.get("seasonal_dishes", []):
        key = slugify(d.get("name", ""))
        out.append({
            "name": d.get("name", ""),
            "description": d.get("description", ""),
            "key": key if key in dishes else None,
        })
    return out


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

    today = date.today()
    published_date = date(today.year, season["start_month"], season["start_day"]).isoformat()

    all_ingredients, all_dishes = _load_lookup()
    page_ingredients, page_dishes = _slice_lookups(content, all_ingredients, all_dishes)

    html = env.get_template("archive_page.html").render(
        season=season,
        content=content,
        accent_color=_accent(season),
        date_range=_date_range(season),
        duration_days=season["duration_days"],
        published_date=published_date,
        prev=prev,
        next=next_s,
        all_seasons=all_seasons,
        produce=_keyed_produce(content, all_ingredients),
        dishes=_keyed_dishes(content, all_dishes),
        ingredient_lookup=page_ingredients,
        dish_lookup=page_dishes,
    )

    filename = _season_filename(season)
    (ARCHIVE_DIR / filename).write_text(html, encoding="utf-8")
    print(f"Archive page written: archive/{filename}")

    _build_index(env, all_seasons)
    _build_sitemap(all_seasons)


# ── Archive index ──────────────────────────────────────────────────────────────

def _build_index(env: Environment, all_seasons: list) -> None:
    pub_ids = _published_ids(all_seasons)
    published_count = len(pub_ids)
    html = env.get_template("archive_index.html").render(
        all_seasons=all_seasons,
        published_count=published_count,
        published_ids=pub_ids,
    )
    (ARCHIVE_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Archive index updated — {published_count} season(s) published.")


# ── Sitemap ────────────────────────────────────────────────────────────────────

def _build_sitemap(all_seasons: list) -> None:
    today = date.today().isoformat()

    def url(loc: str, changefreq: str, priority: str) -> str:
        return (
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    entries = [
        url("https://ko-72.com/", "weekly", "1.0"),
        url("https://ko-72.com/archive/", "monthly", "0.8"),
    ]
    for s in all_seasons:
        if (ARCHIVE_DIR / _season_filename(s)).exists():
            entries.append(url(
                f"https://ko-72.com/archive/{_season_filename(s)}",
                "yearly", "0.6",
            ))

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    (ROOT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print("Sitemap rebuilt: sitemap.xml")


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
