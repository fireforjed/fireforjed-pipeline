"""
publish_post.py -- Step 2 of the Forjed daily posting pipeline.

Takes the already-committed-and-pushed image URL and caption (passed in
as environment variables by the GitHub Actions workflow) and posts them
to both the Forjed Facebook Page and Instagram account.

For local testing, create a .env file (see env.example.txt) and set
IMAGE_URL / CAPTION manually to test against an image that's already
publicly reachable.
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()  # no-op if there's no .env file (e.g. in GitHub Actions)

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _post(url, data):
    resp = requests.post(url, data=data, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"{resp.status_code} error for {url}\nResponse body: {resp.text}")
    return resp.json()


def _get(url, params):
    resp = requests.get(url, params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"{resp.status_code} error for {url}\nResponse body: {resp.text}")
    return resp.json()


def post_to_facebook(image_url, caption, page_id, page_access_token):
    url = f"{GRAPH_API_BASE}/{page_id}/photos"
    result = _post(
        url,
        data={"url": image_url, "caption": caption, "access_token": page_access_token},
    )
    print(f"Facebook post successful. Post ID: {result.get('post_id') or result.get('id')}")
    return result


def post_to_instagram(image_url, caption, ig_user_id, ig_access_token):
    # Step 1: create a media container
    create_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    result = _post(
        create_url,
        data={"image_url": image_url, "caption": caption, "access_token": ig_access_token},
    )
    creation_id = result["id"]

    # Step 2: poll until the container has finished processing
    status_url = f"{GRAPH_API_BASE}/{creation_id}"
    for _ in range(10):
        status = _get(status_url, params={"fields": "status_code", "access_token": ig_access_token})
        if status.get("status_code") == "FINISHED":
            break
        time.sleep(3)
    else:
        raise RuntimeError("Instagram media container never finished processing.")

    # Step 3: publish it
    publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    result = _post(publish_url, data={"creation_id": creation_id, "access_token": ig_access_token})
    print(f"Instagram post successful. Media ID: {result.get('id')}")
    return result


def main():
    image_url = os.environ["IMAGE_URL"]
    caption = os.environ["CAPTION"]

    fb_page_id = os.environ["FB_PAGE_ID"]
    fb_page_access_token = os.environ["FB_PAGE_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_USER_ID"]
    ig_access_token = os.environ["IG_ACCESS_TOKEN"]

    errors = []

    try:
        post_to_facebook(image_url, caption, fb_page_id, fb_page_access_token)
    except Exception as e:
        errors.append(f"Facebook posting failed: {e}")
        print(f"ERROR: Facebook posting failed: {e}", file=sys.stderr)

    try:
        post_to_instagram(image_url, caption, ig_user_id, ig_access_token)
    except Exception as e:
        errors.append(f"Instagram posting failed: {e}")
        print(f"ERROR: Instagram posting failed: {e}", file=sys.stderr)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
