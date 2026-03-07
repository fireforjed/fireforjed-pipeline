import os, json, random
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import BRAND_VOICE, HASHTAG_COUNT, MAX_CAPTION_CHARS, TOPICS

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_caption(topic: str = None) -> tuple[str, str]:
    if not topic:
        topic = random.choice(TOPICS)

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=BRAND_VOICE,
            messages=[{
                "role": "user",
                "content": (
                    f"Write an Instagram post about: {topic}. "
                    f"Respond only in JSON with two keys: "
                    f"'caption' (max {MAX_CAPTION_CHARS} characters, no hashtags) "
                    f"and 'hashtags' (exactly {HASHTAG_COUNT} relevant tags "
                    f"as a single space-separated string starting with #). "
                    f"No preamble. JSON only."
                )
            }]
        )
        data = json.loads(message.content[0].text)
        return data['caption'], data['hashtags']
    except Exception as e:
        print(f"DETAILED ERROR: {type(e).__name__}: {e}")
        raise
