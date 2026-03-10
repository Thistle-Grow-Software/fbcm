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
# TODO: Think harder about this name?
PHOTO_BASE_DIR = os.getenv(
    "PHOTO_BASE_DIR", "/mnt/e/FootballGames/automation/output_data/player_photos"
)

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
