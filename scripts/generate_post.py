"""
generate_post.py -- Step 1 of the Forjed daily posting pipeline.

Picks the next unused Quote/Caption pair from tips.csv, overlays the
Quote text onto the single Forjed background image, and saves the
result to posts/. Also updates quote_state.json to mark that quote as
used (the cycle resets automatically once every quote has been used).

Outputs (for the GitHub Actions workflow to pick up) are written to
$GITHUB_OUTPUT: quote_id, image_filename, caption
"""

import csv
import json
import os
import random
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Hashtags appended to every single post, regardless of Theme.
FIXED_HASHTAGS = ["#forjed", "#getforjed"]

# ---- Paths --------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
TIPS_XLSX = ROOT / "tips.xlsx"
TIPS_CSV = ROOT / "tips.csv"
STATE_FILE = ROOT / "quote_state.json"
BACKGROUND_IMAGE = ROOT / "assets" / "backgrounds" / "background.png"
FONT_FILE = ROOT / "assets" / "fonts" / "Oswald-Bold.ttf"
OUTPUT_DIR = ROOT / "posts"

# ---- Text styling ---------------------------------------------------------
FONT_SIZE = 80  # starting size; auto-shrinks to fit if the quote is long
MIN_FONT_SIZE = 36
TEXT_COLOR = "white"
OUTLINE_COLOR = "black"
OUTLINE_WIDTH = 4
HORIZONTAL_MARGIN = 100  # px of padding on each side
VERTICAL_MARGIN = 100


def load_tips_from_xlsx(path):
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise RuntimeError(f"{path.name} appears to be empty")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    tips = []
    for row in rows[1:]:
        if all(cell is None for cell in row):
            continue  # skip blank rows
        tip = {h: ("" if v is None else str(v).strip()) for h, v in zip(headers, row)}
        tips.append(tip)
    return tips


def load_tips_from_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_tips():
    if TIPS_XLSX.exists():
        rows = load_tips_from_xlsx(TIPS_XLSX)
    elif TIPS_CSV.exists():
        rows = load_tips_from_csv(TIPS_CSV)
    else:
        raise FileNotFoundError(
            f"No tips file found. Expected either {TIPS_XLSX.name} or {TIPS_CSV.name} "
            f"at the repo root."
        )

    if not rows:
        raise RuntimeError("Tips file is empty")
    missing = {"Quote ID", "Quote", "Caption"} - set(rows[0].keys())
    if missing:
        raise RuntimeError(f"Tips file is missing expected column(s): {missing}")
    return rows


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"used_quote_ids": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def theme_to_hashtag(theme):
    """'Personal Growth' -> '#PersonalGrowth'. Returns None for blank input."""
    if not theme or not theme.strip():
        return None
    words = re.split(r"\s+", theme.strip())
    tag = "".join(w[:1].upper() + w[1:] if w else "" for w in words)
    tag = re.sub(r"[^A-Za-z0-9_]", "", tag)
    return f"#{tag}" if tag else None


def build_post_text(tip):
    """Caption, then a hashtag line (Theme + Secondary Theme + fixed tags),
    then Source Insight -- each separated by a blank line. Missing pieces
    (blank Theme, no Source Insight, etc.) are simply skipped."""
    caption = (tip.get("Caption") or "").strip()
    theme_tag = theme_to_hashtag(tip.get("Theme", ""))
    secondary_tag = theme_to_hashtag(tip.get("Secondary Theme", ""))
    source_insight = (tip.get("Source Insight") or "").strip()

    hashtags = [t for t in (theme_tag, secondary_tag) if t] + FIXED_HASHTAGS
    hashtag_line = " ".join(hashtags) + " \U0001F525\U0001F525"

    parts = [caption, hashtag_line]
    if source_insight:
        parts.append(source_insight)

    return "\n\n".join(parts)


def pick_next_tip(tips, state):
    used = set(state.get("used_quote_ids", []))
    unused = [t for t in tips if t["Quote ID"] not in used]

    if not unused:
        # Every quote has been used -- start a fresh cycle.
        used = set()
        unused = tips

    chosen = random.choice(unused)
    used.add(chosen["Quote ID"])
    state["used_quote_ids"] = sorted(used)
    return chosen, state


def fit_text(draw, text, max_width, max_height, font_path):
    """Find the largest font size (down to MIN_FONT_SIZE) whose wrapped
    text fits within max_width x max_height. Returns (font, lines)."""
    size = FONT_SIZE
    chosen_font, chosen_lines = None, None

    while size >= MIN_FONT_SIZE:
        font = ImageFont.truetype(str(font_path), size)
        words = text.split()
        lines, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), trial, font=font, stroke_width=OUTLINE_WIDTH)
            if bbox[2] - bbox[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        top, bottom = font.getbbox("Ag")[1], font.getbbox("Ag")[3]
        line_height = bottom - top
        total_height = line_height * len(lines) * 1.3

        chosen_font, chosen_lines = font, lines
        if total_height <= max_height:
            return font, lines
        size -= 4

    # Smallest size still didn't fully fit -- use it anyway, best effort.
    return chosen_font, chosen_lines


def generate_image(quote_text, quote_id):
    if not BACKGROUND_IMAGE.exists():
        raise FileNotFoundError(
            f"Background image not found at {BACKGROUND_IMAGE}. "
            "Add the single Forjed background image there, named exactly 'background.jpg'."
        )
    if not FONT_FILE.exists():
        raise FileNotFoundError(f"Font not found at {FONT_FILE}.")

    img = Image.open(BACKGROUND_IMAGE)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        # Flatten any transparency onto white before we start drawing,
        # since Instagram/Facebook expect a fully opaque image.
        flattened = Image.new("RGB", img.size, "white")
        flattened.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = flattened
    else:
        img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    max_width = img.width - (2 * HORIZONTAL_MARGIN)
    max_height = img.height - (2 * VERTICAL_MARGIN)

    font, lines = fit_text(draw, quote_text, max_width, max_height, FONT_FILE)

    top, bottom = font.getbbox("Ag")[1], font.getbbox("Ag")[3]
    line_height = bottom - top
    line_spacing = line_height * 1.3
    total_text_height = line_spacing * len(lines)

    y = (img.height - total_text_height) / 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=OUTLINE_WIDTH)
        line_width = bbox[2] - bbox[0]
        x = (img.width - line_width) / 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=TEXT_COLOR,
            stroke_width=OUTLINE_WIDTH,
            stroke_fill=OUTLINE_COLOR,
        )
        y += line_spacing

    OUTPUT_DIR.mkdir(exist_ok=True)
    filename = f"{quote_id}.jpg"
    output_path = OUTPUT_DIR / filename
    img.save(output_path, "JPEG", quality=92)
    return filename


def main():
    tips = load_tips()
    state = load_state()
    tip, state = pick_next_tip(tips, state)

    quote_id = tip["Quote ID"]
    quote_text = tip["Quote"]
    caption = build_post_text(tip)

    image_filename = generate_image(quote_text, quote_id)
    save_state(state)

    print(f"Selected Quote ID {quote_id}: {quote_text[:60]}...")
    print(f"Image saved to posts/{image_filename}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"quote_id={quote_id}\n")
            f.write(f"image_filename={image_filename}\n")
            # Captions may contain newlines, so use a delimiter-safe block.
            f.write("caption<<CAPTION_EOF\n")
            f.write(f"{caption}\n")
            f.write("CAPTION_EOF\n")


if __name__ == "__main__":
    main()
