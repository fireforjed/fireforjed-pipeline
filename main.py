"""
main.py — Entry point for the Fire Forjed Instagram automation pipeline.
"""

import os, sys
from loguru import logger
from scripts.generate_caption import generate_caption
from scripts.generate_image import generate_image
from scripts.post_to_instagram import post_to_instagram

def main():
    # ── Get topic (manual override or auto from settings) ──
    topic = os.getenv('TOPIC_OVERRIDE', '').strip() or None
    logger.info(f'Starting Fire Forjed pipeline. Topic: {topic or "auto"}')

    # ── Step 1: Generate caption + hashtags ───────────────
    caption, hashtags = generate_caption(topic)
    logger.info(f'Caption: {caption[:60]}...')

    # ── Step 2: Generate image ────────────────────────────
    image_path = generate_image(caption_text=caption)
    logger.info(f'Image saved to: {image_path}')

    # ── Step 3: Post to Instagram ─────────────────────────
    post_id = post_to_instagram(
        image_path=image_path,
        caption=f'{caption}\n\n{hashtags}'
    )
    logger.success(f'Posted successfully! Media ID: {post_id}')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f'Pipeline failed: {e}')
        sys.exit(1)
