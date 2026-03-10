from __future__ import annotations

import logging
from pathlib import Path

from .mappings import CITY_TO_ABBR

logger = logging.getLogger(__name__)


def is_bowl_game(orig_file: str) -> str:
    """
    Given a (properly named) Path object, determine if it
    represents an NCAA bowl/playoff game and return the game's name.

    :param orig_file: The string representing the file name stem for the video file we're inspecting.
    :type orig_file: str
    :return: Either the empty string or the name of the bowl game.
    :rtype: str
    """
    bowl_str = ""
    logger.debug(orig_file)
    # TODO: This needs to be generalized.
    for named_game in [
        "SEC Championship ",
        "Orange Bowl ",
        "CFP Final ",
        "Peach Bowl CFP Semi-Final",
    ]:
        if named_game in orig_file:
            bowl_str = named_game
            break
    return bowl_str


def transform_file_name(orig_file_stem: str) -> str:
    """
    A specialized function that takes a file which follows the naming convention of a specific YouTube channel,
    and transforms the name to match our convention and play nice with Plex, Jellyfin, etc.
    :param orig_file_stem: String representing the originally downloaded file's stem.
    :type: orig_file: str
    :return: The transformed file _stem_ as a string.
    :rtype: str
    """
    namer = NCAAGameFileNamer()
    return namer.construct_file_name(orig_file_stem)


class FileNamer:
    """Base class for constructing output file names.

    All file naming in fbcm follows the pattern:
        {prefix} - s{season}e{episode} - {details}

    Subclasses implement content-specific logic while delegating
    the common pattern to :meth:`format_stem`.

    :param base_directory: Optional base directory for constructing full output paths.
    :type base_directory: Path | None
    """

    def __init__(self, base_directory: Path | None = None) -> None:
        self.base_directory = base_directory

    def format_stem(
        self,
        prefix: str,
        season: int | str,
        episode: int | str,
        details: str,
        episode_padding: int = 3,
    ) -> str:
        """Format a file stem using the standard naming convention.

        :param prefix: The series/content prefix (e.g. "NFL Full Game", "NCAA").
        :param season: The season number or year.
        :param episode: The episode number.
        :param details: The detail suffix (e.g. "2024_Wk01_ATL_at_PIT").
        :param episode_padding: Number of digits to zero-pad the episode to.
        :return: The formatted file stem.
        """
        ep_str = str(episode).zfill(episode_padding)
        return f"{prefix} - s{season}e{ep_str} - {details}"

    def construct_output_path(self, file_stem: str, extension: str = "mp4") -> Path:
        """Construct the full output path for a file.

        :param file_stem: The file name without extension.
        :param extension: The file extension (without leading dot).
        :return: The full output path.
        :raises ValueError: If base_directory has not been set.
        """
        if self.base_directory is None:
            raise ValueError("base_directory must be set to construct output paths")
        return self.base_directory / f"{file_stem}.{extension}"


class NFLGameFileNamer(FileNamer):
    """Constructs file names for NFL game replay downloads.

    Produces names like: ``NFL Full Game - s2024e001 - 2024_Wk01_ATL_at_PIT``
    """

    def construct_file_name(self, game: dict, replay_type: str, ep_num: int) -> str:
        """Create the video file's name according to the established format.

        :param game: Data for the game we're working on.
        :param replay_type: The replay type we're currently storing.
        :param ep_num: The position of this game in the sequence of all NFL games played in the season.
        :return: The stem to be used in the video file's name.
        """
        logger.debug(f"Constructing file name for {game['slug']}")

        away_city = " ".join(game["awayTeam"].split(" ")[:-1])
        home_city = " ".join(game["homeTeam"].split(" ")[:-1])

        if "Jets" in game["awayTeam"] or "Chargers" in game["awayTeam"]:
            away_city += " (A)"
        elif "Giants" in game["awayTeam"] or "Rams" in game["awayTeam"]:
            away_city += " (N)"

        if "Jets" in game["homeTeam"] or "Chargers" in game["homeTeam"]:
            home_city += " (A)"
        elif "Giants" in game["homeTeam"] or "Rams" in game["homeTeam"]:
            home_city += " (N)"

        away_tm = CITY_TO_ABBR[away_city]
        home_tm = CITY_TO_ABBR[home_city]

        prefix = f"NFL {replay_type}"
        details = (
            f"{game['season']}_Wk{str(game['week']).zfill(2)}_"
            f"{away_tm}_{game['divider']}_{home_tm}"
        )
        return self.format_stem(
            prefix=prefix,
            season=game["season"],
            episode=ep_num,
            details=details,
        )


class NCAAGameFileNamer(FileNamer):
    """Constructs file names for NCAA game downloads.

    Transforms names from a specific YouTube channel format into the
    standard convention. Produces names like:
    ``NCAA - s2024e13 - 2024_Gm13SECChampionship_Georgia_vs_Texas``
    """

    def construct_file_name(self, orig_file_stem: str) -> str:
        """Transform a file stem from the source format into the standard convention.

        :param orig_file_stem: String representing the originally downloaded file's stem.
        :return: The transformed file stem.
        """
        stem = orig_file_stem.replace("UGA", "Georgia").replace("@", "at")

        bowl_str = is_bowl_game(orig_file_stem)
        if bowl_str:
            stem = stem.replace(bowl_str, "")
            bowl_str = bowl_str.strip().replace(" ", "").replace("-Final", "")

        stem_parts = stem.split(" ")

        year = stem_parts[0]
        game_num = stem_parts[3]

        try:
            divider_index = stem_parts.index("at")
        except ValueError:
            divider_index = stem_parts.index("vs")

        divider = stem_parts[divider_index]

        team_one = "_".join(stem_parts[5:divider_index])
        team_two = "_".join(stem_parts[divider_index + 1 :])

        game_str = f"{game_num.zfill(2)}{bowl_str}"
        details = f"{year}_Gm{game_str}_{team_one}_{divider}_{team_two}"

        return self.format_stem(
            prefix="NCAA",
            season=year,
            episode=game_num,
            details=details,
            episode_padding=2,
        )


class SeriesFileNamer(FileNamer):
    """Constructs file names for generic TV series content.

    Produces names like: ``NFL Games - s2024e001 - Episode Name``
    """

    def __init__(
        self,
        series_name: str,
        base_directory: Path | None = None,
    ) -> None:
        super().__init__(base_directory=base_directory)
        self.series_name = series_name

    def construct_file_name(
        self, season: int | str, episode: int | str, episode_name: str
    ) -> str:
        """Create the file stem for a series episode.

        :param season: The season number or year.
        :param episode: The episode number.
        :param episode_name: The episode title or description.
        :return: The formatted file stem.
        """
        return self.format_stem(
            prefix=self.series_name,
            season=season,
            episode=episode,
            details=episode_name,
        )
