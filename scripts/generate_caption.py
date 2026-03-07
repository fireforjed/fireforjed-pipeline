"""
generate_caption.py — Calls Claude API to produce a post caption
and hashtags tailored to the Fire Forjed brand voice.
"""

import os
import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import BRAND_VOICE, HASHTAG_COUNT, MAX_CAPTION_CHARS, TOPICS
import random

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_caption(topic: str = None) -> tuple[str, str]:
    """
    Generates a caption and hashtags for a given topic.
    If no topic is provided, picks one randomly from settings.
    Returns: (caption_text, hashtag_string)
    """

    if not topic:
        topic = random.choice(TOPICS)

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=BRAND_VOICE,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write an Instagram post about: {topic}. "
                    f"Respond only in JSON with two keys: "
                    f"'caption' (max {MAX_CAPTION_CHARS} characters, no hashtags) "
                    f"and 'hashtags' (exactly {HASHTAG_COUNT} relevant tags "
                    f"as a single space-separated string starting with #). "
                    f"No preamble. JSON only."
                )
            }
        ]
    )

    data = json.loads(message.content[0].text)
    return data['caption'], data['hashtags']
