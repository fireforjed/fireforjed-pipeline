"""
generate_image.py — Composes a 1080x1080 black Instagram image
with white text centered. No external API needed — uses Pillow only.
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, uuid
from config.settings import IMG_SIZE, FONT_SIZE, FONT_COLOR, BACKGROUND_COLOR

OUTPUT_DIR = 'output'
FONT_PATH = 'assets/fonts/Montserrat-Bold.ttf'

def generate_image(caption_text: str) -> str:
    """
    Draws caption_text centered on a black 1080x1080 canvas.
    Returns the path to the saved image file.
    """

    # ── Create pure black canvas ──────────────────────
    img = Image.new('RGBA', IMG_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Load font ─────────────────────────────────────
    try:
        font = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)
    except:
        # Fallback if font file missing
        font = ImageFont.load_default()

    # ── Word-wrap text ────────────────────────────────
    wrapped = textwrap.fill(caption_text, width=20)

    # ── Center text on canvas ─────────────────────────
    bbox = draw.textbbox((0, 0), wrapped, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (IMG_SIZE[0] - text_w) // 2
    y = (IMG_SIZE[1] - text_h) // 2

    # ── Draw subtle shadow ────────────────────────────
    draw.text((x + 3, y + 3), wrapped, font=font, fill=(30, 30, 30, 255))

    # ── Draw main white text ──────────────────────────
    draw.text((x, y), wrapped, font=font, fill=FONT_COLOR)

    # ── Save to output/ ───────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f'post_{uuid.uuid4().hex[:8]}.png')
    img.convert('RGB').save(out_path, 'PNG')

    return out_path
