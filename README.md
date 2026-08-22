# Fire Forjed Pipeline

Automatically posts a daily Forjed quote image to Facebook and Instagram.

## How it works

1. `scripts/generate_post.py` picks a random not-yet-used row from `tips.csv`,
   overlays the `Quote` text onto the single Forjed background image
   (`assets/backgrounds/background.jpg`) using the Oswald-Bold font, and
   saves it to `posts/{Quote ID}.jpg`. It also updates `quote_state.json`
   so that quote won't repeat until every quote in the sheet has been used
   at least once.
2. The GitHub Actions workflow commits and pushes that generated image
   (and the updated state file) back to the repo, so it has a public
   `raw.githubusercontent.com` URL.
3. `scripts/publish_post.py` posts that image URL, along with the row's
   `Caption` text, to both the Forjed Facebook Page and the Forjed
   Instagram account via the Meta Graph API.

## One-time setup

- **`tips.csv`** must live at the repo root with (at least) these columns:
  `Quote ID`, `Quote`, `Caption`. Extra columns (Theme, Secondary Theme,
  Source Insight, Instagram Potential) are fine to keep -- they're just
  ignored by the script.
- **`assets/backgrounds/background.jpg`** -- the single background image
  used for every post. Replace this file (keep the exact filename) if you
  ever want to change it.
- **`assets/fonts/Oswald-Bold.ttf`** -- already in place, used for the
  on-image quote text.
- **This repo must be public** (or otherwise publicly readable), since
  Instagram's servers need to fetch the generated image via its raw
  GitHub URL before it can publish it.
- **GitHub repo secrets** (Settings > Secrets and variables > Actions):
  `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.

## Posting schedule

Currently set to run once daily via the cron schedule in
`.github/workflows/daily-post.yml`. You can also trigger a run manually
from the Actions tab (`workflow_dispatch`) to test it any time.

To move to twice a day later, just add a second `cron:` line under the
`schedule:` section of the workflow file with a different time.

## Local testing

1. `pip install -r requirements.txt`
2. Copy `env.example.txt` to `.env` and fill in your four Meta credentials.
3. Run `python scripts/generate_post.py` to generate an image locally
   without posting anything.
4. To test actual posting, you'd need the generated image to already be
   at a public URL (e.g. push it to the repo first, or host it
   elsewhere temporarily), then set `IMAGE_URL` and `CAPTION` in `.env`
   and run `python scripts/publish_post.py`.

## Text styling

- White fill, black outline, centered horizontally and vertically.
- Automatically wraps to multiple lines and shrinks the font size (down
  to a minimum) if a quote is too long to fit comfortably.
