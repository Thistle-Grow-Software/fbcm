from pathlib import Path
from typing import Any

import yaml

CONFIG_FILE_NAME = "fbcm.yaml"


def generate_episode_metadata_xml(
    title: str, season: str | int, episode: str | int, aired: str
) -> str:
    """
    Generate XML metadata for an episode in the format expected by Jellyfin/Plex.

    :param title: The episode title to display.
    :param season: The season number/year.
    :param episode: The episode number.
    :param aired: The air date string (e.g. "2025-09-14").
    :return: An XML string containing episodedetails.
    """
    return (
        f"<episodedetails>\n"
        f"\t<title>{title}</title>\n"
        f"\t<season>{season}</season>\n"
        f"\t<episode>{episode}</episode>\n"
        f"\t<aired>{aired}</aired>\n"
        f"</episodedetails>"
    )


def find_config(explicit_path: str | None = None) -> Path | None:
    """
    Find the config file using auto-discovery or explicit path.

    Search order:
    1. Explicit path (if provided)
    2. Current working directory (fbdl.yaml)
    3. ~/.config/fbdl.yaml

    :param explicit_path: User-provided path to config file
    :return: Path to config file or None if not found
    """
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        return None

    # Check current working directory
    cwd_config = Path.cwd() / CONFIG_FILE_NAME
    if cwd_config.exists():
        return cwd_config

    # Check ~/.config/fbdl.yaml
    home_config = Path.home() / ".config" / CONFIG_FILE_NAME
    if home_config.exists():
        return home_config

    return None


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load configuration from a YAML file.

    :param config_path: Path to the config file
    :return: Dict containing the configuration, or empty dict if no config
    """
    if config_path is None:
        return {}

    with open(config_path) as f:
        config = yaml.safe_load(f)

    return config if config else {}
