"""
generate_image.py — Composes a 1080x1080 Instagram image
using a random forge background from assets/backgrounds/,
with a light dark overlay and centered white text.
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap, os, uuid, random

from config.settings import IMG_SIZE, FONT_SIZE, FONT_COLOR, BACKGROUND_COLOR

OUTPUT_DIR = 'output'
FONT_PATH = 'assets/fonts/Oswald-Bold.ttf'
BACKGROUNDS_DIR = 'assets/backgrounds'
OVERLAY_ALPHA = 120  # 0=fully transparent, 255=solid black. 120 = light darkening
MAIN_FONT_SIZE = 90   # large and bold
BRAND_FONT_SIZE = 44  # "Forjed" tag at bottom


def get_random_background() -> Image.Image:
    """Pick a random image from assets/backgrounds/ and return resized RGBA."""
    valid_ext = ('.jpg', '.jpeg', '.png')
    images = [
        f for f in os.listdir(BACKGROUNDS_DIR)
        if f.lower().endswith(valid_ext)
    ]
    if not images:
        # Fallback to solid black if no backgrounds found
        return Image.new('RGBA', IMG_SIZE, (0, 0, 0, 255))

    chosen = random.choice(images)
    path = os.path.join(BACKGROUNDS_DIR, chosen)
    bg = Image.open(path).convert('RGBA')

    # Crop to square from center, then resize to 1080x1080
    w, h = bg.size
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    bg = bg.crop((left, top, left + min_side, top + min_side))
    bg = bg.resize(IMG_SIZE, Image.LANCZOS)
    return bg


def auto_wrap(text: str, font, draw, max_width: int) -> str:
    """Find the widest wrap width that keeps text within max_width pixels."""
    for w in range(40, 8, -1):
        wrapped = textwrap.fill(text, width=w)
        bbox = draw.textbbox((0, 0), wrapped, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return wrapped
    return textwrap.fill(text, width=10)


def generate_image(caption_text: str) -> str:
    """
    Composites caption_text over a random forge background.
    Returns the path to the saved image file.
    """
    # ── Background ────────────────────────────────────
    img = get_random_background()

    # ── Dark overlay for text legibility ──────────────
    overlay = Image.new('RGBA', IMG_SIZE, (0, 0, 0, OVERLAY_ALPHA))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    MAX_WIDTH = IMG_SIZE[0] - 200  # 100px padding each side

    # ── Load font ─────────────────────────────────────
    try:
        font = ImageFont.truetype(FONT_PATH, size=MAIN_FONT_SIZE)
        small_font = ImageFont.truetype(FONT_PATH, size=BRAND_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    # ── Word-wrap text ────────────────────────────────
    wrapped = auto_wrap(caption_text, font, draw, MAX_WIDTH)

    # ── Center multiline text on canvas ──────────────
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, align="center")
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (IMG_SIZE[0] - text_w) // 2
    y = (IMG_SIZE[1] - text_h) // 2

    # ── Draw shadow ───────────────────────────────────
    for offset in [(5, 5), (4, 4), (3, 3)]:
        draw.multiline_text(
            (x + offset[0], y + offset[1]), wrapped,
            font=font, fill=(0, 0, 0, 220), align="center"
        )

    # ── Draw main white text ──────────────────────────
    draw.multiline_text((x, y), wrapped, font=font, fill=FONT_COLOR, align="center")

    # ── Brand tag at bottom ───────────────────────────
    draw.line([(80, 985), (1000, 985)], fill=(200, 110, 20, 180), width=1)
    draw.text((80, 994), "Forjed", font=small_font, fill=(200, 110, 20, 220))

    # ── Save to output/ ───────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f'post_{uuid.uuid4().hex[:8]}.png')
    img.convert('RGB').save(out_path, 'PNG')
    return out_path
