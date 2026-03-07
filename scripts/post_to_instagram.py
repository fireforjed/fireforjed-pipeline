"""
post_to_instagram.py — Publishes a local image to Instagram
using the Meta Graph API two-step process.
"""

import os, requests, time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

IG_USER_ID = os.environ['IG_USER_ID']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
BASE_URL = f'https://graph.facebook.com/v19.0/{IG_USER_ID}'

def upload_to_imgbb(image_path: str) -> str:
    """Uploads image to ImgBB and returns a public URL."""
    with open(image_path, 'rb') as f:
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': os.environ.get('IMGBB_API_KEY', '')},
            files={'image': f}
        )
    response.raise_for_status()
    return response.json()['data']['url']

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
def post_to_instagram(image_path: str, caption: str) -> str:
    """Publishes image + caption to Instagram. Returns media ID."""

    # ── Get public URL ────────────────────────────────
    public_url = upload_to_imgbb(image_path)
    logger.info(f'Image hosted at: {public_url}')

    # ── Step A: Create media container ───────────────
    container_resp = requests.post(
        f'{BASE_URL}/media',
        data={
            'image_url': public_url,
            'caption': caption,
            'access_token': ACCESS_TOKEN
        }
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()['id']
    logger.info(f'Container created: {container_id}')

    # ── Wait before publishing ────────────────────────
    time.sleep(5)

    # ── Step B: Publish container ─────────────────────
    publish_resp = requests.post(
        f'{BASE_URL}/media_publish',
        data={
            'creation_id': container_id,
            'access_token': ACCESS_TOKEN
        }
    )
    publish_resp.raise_for_status()
    return publish_resp.json()['id']
