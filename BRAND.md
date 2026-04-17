# Kō Brand Kit
> Japan's 72 micro-seasons, one at a time

---

## Identity

| | |
|---|---|
| Name | Kō |
| Kanji | 候 |
| Tagline | Japan's 72 micro-seasons, one at a time |
| Subject line format | `Kō · {season_name_en} ({name_romaji})` |
| Email from-name | Kō |

---

## Color Palette

| Name | Hex | Usage |
|---|---|---|
| Ink | `#1a1a18` | Email header bg, dark surfaces |
| Earth | `#4a3728` | Subheadings, rich accents |
| Persimmon | `#c9734a` | Summer accent |
| Harvest gold | `#d4a853` | Autumn accent |
| Bamboo | `#6b8f71` | Spring accent |
| Winter sky | `#4a7fa5` | Winter accent |
| Washi | `#f5f3ee` | Email body bg, light surfaces |
| Stone | `#888780` | Muted text, secondary elements |
| Deep ink | `#2c2c2a` | Body text on light backgrounds |

### Seasonal Accent Colors

Applied to the season label line in the email header, and to section accents throughout:

| Season | Color name | Hex |
|---|---|---|
| Spring | Bamboo | `#6b8f71` |
| Summer | Persimmon | `#c9734a` |
| Autumn | Harvest gold | `#d4a853` |
| Winter | Winter sky | `#4a7fa5` |

In code:
```python
ACCENT_COLORS = {
    "Spring": "#6b8f71",
    "Summer": "#c9734a",
    "Autumn": "#d4a853",
    "Winter": "#4a7fa5",
}
```

---

## Typography

### Rules
- **Season names, opening paragraphs, haiku** → serif (`Georgia, 'Times New Roman', serif`)
- **UI labels, metadata, section headers, body copy** → sans-serif (`system-ui, -apple-system, sans-serif`)
- Never mix serif and sans-serif within the same element

### Scale

| Role | Size | Weight | Style | Color |
|---|---|---|---|---|
| Logo "Kō" | 22px | 400 | serif | Washi `#f5f3ee` |
| Season label | 11px uppercase, 0.1em tracking | 500 | sans | Seasonal accent |
| Display (season name) | 26–32px | 400 | serif | Washi `#f5f3ee` |
| Romaji subtitle | 14px | 400 | sans | Stone `#888780` |
| Body copy | 15px, line-height 1.8 | 400 | sans | Deep ink `#2c2c2a` |
| Haiku | 15px, line-height 2.2 | 400 | serif italic | Stone `#888780` |
| Footer / meta | 11px | 400 | sans | Stone `#888780` |

---

## Email Header Structure

Dark band — background: Ink `#1a1a18`, padding: 32px 36px 28px

1. **Logo row** — "Kō" in 22px serif Washi + "候" in 14px sans Stone, baseline-aligned, gap 10px
2. **Hairline rule** — 0.5px, `#333330`, margin 20px 0
3. **Season label** — `Spring · Micro-season 01 of 72 · Feb 4` in 11px uppercase, 0.1em tracking, seasonal accent color
4. **Season name** — serif 26px, Washi `#f5f3ee`, weight 400, letter-spacing -0.01em
5. **Romaji / kanji** — 14px sans, Stone `#888780`

---

## Email Body Structure

Light band — background: Washi `#f5f3ee`, padding: 28px 36px, max-width: 600px centered

Section order:
1. Opening paragraph (serif, 17px, generous line-height)
2. Nature notes (sans body)
3. Produce table — 3 columns: Fruits / Vegetables / Fish, seasonal accent color headers
4. Seasonal dishes — dish name in bold, description in muted text below
5. Cultural note — left-border accent in seasonal color, slightly inset
6. Haiku — centered, serif italic, Stone, generous vertical whitespace
7. Closing line — centered, 13px, Stone
8. Footer — "View in browser · Archive · Unsubscribe", 11px, Stone, centered

Section dividers: `0.5px solid #d8d5ce`

---

## Voice & Tone

**Observational, specific, never enthusiastic.**
More field notes than lifestyle blog. Lead with nature, then food, then culture.

### Do
- "The warbler has not yet appeared, but the ice is listening."
- "Buri — yellowtail — reaches its peak fat content in winter. The Japanese call this kan-buri, the cold-season fish."
- "A stillness breaks that has held since the solstice — not warmth exactly, but the memory of it."

### Don't
- "Spring is here! Check out these amazing seasonal foods you need to try right now."
- "Yellowtail is a popular fish in Japan that people eat in winter because it tastes good."
- Exclamation marks, superlatives, lifestyle-magazine energy

---

## Archive & Web

- Archive index title: `Kō · All Seasons`
- Archive page title: `Kō — {season_name_en}`
- Nav: `← All seasons` link back to `/archive/index.html`
- Same Ink header / Washi body aesthetic as email
- Responsive, mobile-first, max-width 600px with auto side margins

---

## Usage Notes for Claude Code

When any prompt touches `templates/email.html`, `templates/archive_page.html`, or any file that generates content:

1. Read this file first
2. Apply `ACCENT_COLORS` mapping based on `season.major_season`
3. Pass `accent_color` as a template variable
4. Follow the typography split — serif for season names and haiku, sans for everything else
5. Match the voice guidelines when writing or evaluating generated content
