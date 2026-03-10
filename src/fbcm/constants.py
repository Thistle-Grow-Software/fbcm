import os

# Application related
OUTPUT_FORMATS = {
    "json": "JSON",
    "yaml": "YAML",
    "csv": "CSV",
    "docx": "Microsoft Word",
}
MEDIA_BASE_DIR = os.getenv("MEDIA_BASE_DIR")
CONCURRENT_FRAGMENTS = os.getenv("CONCURRENT_FRAGMENTS", 1)
THROTTLED_RATE_LIMIT = os.getenv("THROTTLED_RATE_LIMIT", 1000000)
PHOTO_BASE_DIR = os.getenv(
    "PHOTO_BASE_DIR", "/mnt/e/FootballGames/automation/output_data/player_photos"
)

# --- Font defaults ---
RATING_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# --- URLs ---
NFL_REPLAY_BASE_URL = "https://www.nfl.com/plus/games/"
NFL_EPISODES_BASE_URL = "https://www.nfl.com/plus/episodes/"
NFL_DRAFT_BUZZ_BASE_URL = "https://www.nfldraftbuzz.com"

# --- Browser automation defaults ---
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_SLOW_MO_MS = 150
DEFAULT_CONTENT_WAIT_TIME_MS = 3000
DEFAULT_MAX_BROWSER_RETRIES = 3

# --- Sleep ranges (seconds) for anti-scraping delays ---
PROFILE_SCRAPE_SLEEP_RANGE = (3.5, 4.5)
PAGE_NAVIGATION_SLEEP_RANGE = (4.5, 5.5)
POSITION_GROUP_SLEEP_RANGE = (10, 15)

# Re-export mappings for backward compatibility
from .mappings import (  # noqa: E402, F401
    ABBREVIATION_MAP,
    CITY_TO_ABBR,
    DEFAULT_REPLAY_TYPES,
    POSITION_STATS,
    POSITION_TO_GROUP_MAP,
    POSITIONS,
    TEAM_FULL_NAMES,
)
