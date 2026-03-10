from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from yt_dlp import YoutubeDL

if TYPE_CHECKING:
    from griddy.nfl.models import WeeklyGameDetail

# noinspection PyUnresolvedReferences
from yt_dlp.extractor.nfl import NFLBaseIE

from .constants import MEDIA_BASE_DIR
from .downloaders import BaseDownloader
from .file_namer import NFLGameFileNamer
from .file_operations import get_max_episode_number_in_dir
from .mappings import DEFAULT_REPLAY_TYPES, TEAM_FULL_NAMES
from .utils import generate_episode_metadata_xml

logger = logging.getLogger(__name__)


# Alias for backward compatibility; the implementation now lives in file_namer.py
FileNamer = NFLGameFileNamer


class GameExtractor:
    """Extracts game information from the NFL API for download processing."""

    def __init__(
        self,
        nfl_client: Any,
        replay_base_url: str = "https://www.nfl.com/plus/games/",
    ) -> None:
        self.nfl_client = nfl_client
        self._replay_base_url = replay_base_url

    def should_extract(self, game: WeeklyGameDetail, teams: list[str]) -> bool:
        """
        Determine whether we should proceed with extracting this game.

        :param game: The (parsed) game JSON returned by the NFL API.
        :type game: WeeklyGameDetail

        :param teams: A list of teams that games should be extracted for.
            Values are expected to be abbreviations.
        :type teams: List[str]

        :return: A boolean indicating yes or no.
        :rtype: bool
        """
        if teams == ["all"]:
            return True

        game_participants = [game.home_team.full_name, game.away_team.full_name]

        for team in teams:
            if TEAM_FULL_NAMES[team.upper()] in game_participants:
                return True

        return False

    def extract_game_info(
        self, game: WeeklyGameDetail, replay_types: list | None = None
    ) -> dict:
        """
        Extract only the information relevant to downloading and storing the replays properly.

        :param game: A WeeklyGameDetail containing all the information about a given game.
        :type game: WeeklyGameDetail

        :param replay_types: Which replay type(s) to grab the necessary information for.
        :type replay_types: List[str]

        :returns: A dict containing only the relevant information.
        :rtype: Dict
        """
        fields = ["season", "week", "week_type", "date_"]

        game_info = {attr: getattr(game, attr) for attr in fields}
        game_info["homeTeam"] = game.home_team.full_name
        game_info["awayTeam"] = game.away_team.full_name
        game_info["divider"] = "vs" if game.neutral_site else "at"

        for ex_id in game.external_ids:
            if ex_id.source == "slug":
                game_info["slug"] = ex_id.id

        if not replay_types:
            replay_types = DEFAULT_REPLAY_TYPES.values()

        game_info["replays"] = {}
        for replay in game.replays:
            subType = replay.sub_type

            if subType in replay_types:
                game_info["replays"][subType] = {
                    "mcpPlaybackId": replay.mcp_playback_id,
                    "thumbnailUrl": replay.thumbnail.get("thumbnailUrl"),
                }

                game_info["replays"][subType]["url"] = self._construct_replay_url(
                    game_info, subType
                )

        return game_info

    def _construct_replay_url(self, game: dict, replay_type: str) -> str:
        """
        Construct the URL yt-dlp should use to extract the video file.

        :param game: Data for the game we're working on.
        :type game: Dict

        :param replay_type: The type of replay we want to download.
        :type replay_type: str

        :return: The full URL of the game replay.
        :rtype: str
        """
        return f"{self._replay_base_url}{game['slug']}?mcpid={game['replays'][replay_type]['mcpPlaybackId']}"

    def get_and_extract_games_for_week(
        self,
        season: int,
        week: int,
        teams: list[str] | None = None,
        replay_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Fetch the list of games and extract the info we care about.

        :param season: The season we're downloading replays for.
        :type season: int

        :param week: The week number we're downloading replays for.
        :type week: int

        :param teams: Only extract games involving these teams. If None, download all games.
        :type teams: Optional[List[str]]

        :param replay_types: A list of the replay types we want to download.
        :type replay_types: Optional[List[str]]

        :return: A list of dict objects containing only the information we need.
        :rtype: List[Dict]
        """
        logger.info(f"Downloading {replay_types} for {season} week {week}")
        raw_games_list = self.nfl_client.games.get_weekly_game_details(
            season=season, type_="REG", week=week, include_replays=True
        )
        logger.info(f"Found {len(raw_games_list)} games for week {week}")

        if not teams:
            teams = ["all"]

        extracted_games = []
        for game in raw_games_list:
            if self.should_extract(game=game, teams=teams):
                extracted_games.append(
                    self.extract_game_info(game=game, replay_types=replay_types)
                )

        return extracted_games


class MetadataWriter:
    """Constructs and writes NFO metadata files for game replays."""

    def __init__(self, destination_dir: Path, file_namer: FileNamer) -> None:
        self.destination_dir = destination_dir
        self.file_namer = file_namer

    def construct_metadata_for_game(
        self, game: dict, replay_type: str, ep_num: int
    ) -> str:
        """
        Given information about the game, construct the XML string that
        will be stored in the related nfo file for Plex/Jellyfin parsing.

        :param game: The game's information.
        :type game: Dict

        :param replay_type: Which replay type we're creating the metadata for.
        :type replay_type: str

        :param ep_num: The 'episode number' to assign to the replay.
        :return: A string containing XML information that defines the metadata Jellyfin wants.
        :rtype: str
        """
        title = (
            f"{game['season']} Week {game['week']} - ({replay_type}) "
            f"{game['awayTeam']} {game['divider']} {game['homeTeam']}"
        )

        return generate_episode_metadata_xml(
            title=title,
            season=game["season"],
            episode=ep_num,
            aired=game["date_"],
        )

    def write_metadata_file(self, game: dict, replay_type: str, ep_num: int) -> None:
        """
        Construct metadata for the given game and store it in an nfo file.

        :param game: The game to create metadata for.
        :type game: Dict

        :param replay_type: The replay type of the video we're creating metadata for.
        :type replay_type: str

        :param ep_num: The position of this game in the sequence of all NFL games played in the season.
        :type ep_num: int
        """
        file_stem = self.file_namer.construct_file_name(
            game=game, replay_type=replay_type, ep_num=ep_num
        )
        nfo_file = Path(self.destination_dir, f"{file_stem}.nfo")
        xml_string = self.construct_metadata_for_game(
            game=game, replay_type=replay_type, ep_num=ep_num
        )
        nfo_file.write_text(xml_string)


class NFLShowDownloader:
    """
    A wrapper around YoutubeDL that specializes in downloading TV Series available on NFL Plus.
    TODO: This class requires a lot of work to leverage yt-dlp fully.
    """

    def __init__(
        self,
        episode_list_path: str | Path,
        cookie_file_path: str | Path,
        show_dir: str | Path,
        pause_time: int = 30,
    ) -> None:
        """
        Create the NFLShowDownloader with the given arguments.

        :param episode_list_path: The JSON file containing an array of arrays,
            each containing URL leaves for the season's episodes.
        :type episode_list_path: str | Path

        :param cookie_file_path: The Netscape format cookies file to use for authentication.
        :type cookie_file_path: str | Path

        :param show_dir: The directory to store the show's seasons and episodes in.
        :type show_dir: str | Path

        :param pause_time: Number of seconds to sleep the program between season downloads
            to avoid being banned or throttled.
        """
        self.base_url = "https://www.nfl.com/plus/episodes/"

        with open(str(episode_list_path)) as infile:
            data = json.load(infile)
            self.episodes = data["seasons"]

        if isinstance(cookie_file_path, str):
            cookie_file_path = Path(cookie_file_path)
        self.cookie_file_path = cookie_file_path

        self.show_directory = Path(MEDIA_BASE_DIR, show_dir)
        self.show_directory.mkdir(parents=True, exist_ok=True)

        self.base_yt_opts = {
            "cookiefile": self.cookie_file_path,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "merge_output_format": "mp4",
            # "concurrent_fragment_downloads": 4,
            # "writethumbnail": True,
            # "embedthumbnail": True,
            "addmetadata": True,
            "throttledratelimit": 1000000,
            "postprocessors": [
                {
                    "key": "FFmpegMetadata",
                    "add_chapters": True,
                    "add_metadata": True,
                },
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": True,
                },
            ],
            "embedsubs": True,
            "writesubs": True,
            "subtitleslangs": ["en"],
            "progress_hooks": [
                lambda d: (
                    logger.info(f"Downloading {d['filename']}")
                    if d["status"] == "downloading"
                    else None
                )
            ],
        }
        self.completed = []
        self.errors = []
        self.completed_seasons = []
        self.pause_time = pause_time

    def download_episodes(self) -> None:
        """
        Donwload the show episodes as specified in __init__
        :return:
        """
        logger.info("Downloading episodes")
        for idx, season in enumerate(self.episodes):
            logger.info(f"Working on season {idx + 1}")
            if idx + 1 in self.completed_seasons:
                logger.info(f"Skipping Season {idx + 1}")
                continue
            season_directory = self.show_directory / Path(
                "Season " + str(idx + 1).zfill(2)
            )
            season_directory.mkdir(parents=True, exist_ok=True)

            output_tmpl = str(season_directory / "%(title)s.%(ext)s")
            completed_urls = [
                f"{self.base_url}{ep}"
                for ep in season
                if ((ep not in self.completed) and (ep not in self.errors))
            ]
            full_opts = {**self.base_yt_opts, "outtmpl": output_tmpl}

            with YoutubeDL(full_opts) as ydl:
                ydl.download(completed_urls)
                self.completed_seasons.append(idx + 1)

            logger.info(f"Pausing for {self.pause_time} between seasons")
            time.sleep(self.pause_time)


class NFLWeeklyDownloader(BaseDownloader, NFLBaseIE):
    """
    A YoutubeDL wrapper that leverages the NFL tools included with yt-dlp.

    Uses composition to delegate file naming, game extraction, and metadata
    writing to dedicated collaborator objects that can be injected for testing.
    """

    def __init__(
        self,
        firefox_profile_path: str | Path,
        destination_dir: str | Path,
        nfl_username: str | None = None,
        nfl_password: str | None = None,
        nfl_auth: dict[str, Any] | None = None,
        show_login: bool = False,
        add_yt_opts: dict | None = None,
        file_namer: FileNamer | None = None,
        game_extractor: GameExtractor | None = None,
        metadata_writer: MetadataWriter | None = None,
    ) -> None:
        """
        Create the downloader; set its download and storage parameters.

        :param firefox_profile_path: Path to the user's Firefox profile.
        :type firefox_profile_path: str | Path

        :param destination_dir: The directory to store the replays in.
        :type destination_dir: str | Path

        :param nfl_username: Username or email address associated with your NFL.com account.
        :type nfl_username: str | None

        :param nfl_password: Your NFL.com password.
        :type nfl_password: str | None

        :param nfl_auth: A dict containing accessToken, refreshToken, and expiresIn.
        :type nfl_auth: Dict[str, Any] | None

        :param show_login: If true, display browser window as automated login is happening.
        :type show_login: bool

        :param add_yt_opts: Any yt-dlp options that should override the base options.
        :type add_yt_opts: Dict | None

        :param file_namer: Injectable FileNamer for constructing file names.
        :type file_namer: FileNamer | None

        :param game_extractor: Injectable GameExtractor for fetching and filtering games.
        :type game_extractor: GameExtractor | None

        :param metadata_writer: Injectable MetadataWriter for writing NFO files.
        :type metadata_writer: MetadataWriter | None
        """
        from griddy.nfl import GriddyNFL

        super().__init__(firefox_profile_path, destination_dir, add_yt_opts)

        if nfl_auth:
            self.nfl_client = GriddyNFL(nfl_auth=nfl_auth)
        else:
            self.nfl_client = GriddyNFL(
                login_email=nfl_username,
                login_password=nfl_password,
                headless_login=(not show_login),
            )

        self.file_namer = file_namer or FileNamer(base_directory=self.destination_dir)
        if self.file_namer.base_directory is None:
            self.file_namer.base_directory = self.destination_dir
        self.game_extractor = game_extractor or GameExtractor(
            nfl_client=self.nfl_client
        )
        self.metadata_writer = metadata_writer or MetadataWriter(
            destination_dir=self.destination_dir, file_namer=self.file_namer
        )

    def get_and_extract_games_for_week(
        self,
        season: int,
        week: int,
        teams: list[str] | None = None,
        replay_types: list[str] | None = None,
    ) -> list[dict]:
        """Delegate game fetching and extraction to the GameExtractor."""
        return self.game_extractor.get_and_extract_games_for_week(
            season=season, week=week, teams=teams, replay_types=replay_types
        )

    def download_game(self, game: dict, ep_num: int) -> None:
        """
        Download all the replay types we specified for this game.

        :param game: Data for the game we're downloading.
        :type game: Dict

        :param ep_num: The position of this game in the sequence of all NFL games played in the season.
        :type ep_num: int
        """
        for replay_type, info in game["replays"].items():
            logger.info(f"Replay type: {replay_type}")
            file_name = self.file_namer.construct_file_name(game, replay_type, ep_num)
            output_path = self.file_namer.construct_output_path(
                file_stem=file_name, extension="%(ext)s"
            )
            outtmpl = str(output_path)
            logger.info(f"Output path: {outtmpl}")
            self.base_yt_opts["outtmpl"] = str(outtmpl)

            with YoutubeDL(self.base_yt_opts) as ydl:
                ydl.download(info["url"])

            self.metadata_writer.write_metadata_file(
                game=game, replay_type=replay_type, ep_num=ep_num
            )

    def download_all_for_week(
        self,
        season: int,
        week: int,
        teams: list[str] | None = None,
        replay_types: list[str] | None = None,
        sleep_time: int = 15,
        start_ep: int | None = None,
    ) -> None:
        """
        Fetch games, extract their information, and download the replays.

        :param season: The season we're downloading games for.
        :type season: int

        :param week: The week we're downloading games for.
        :type week: int

        :param teams: A list of teams to extract games for.
        :type teams: Optional[List[str]]

        :param replay_types: The list of replay types we want to download.
        :type replay_types: Optional[List[str]]

        :param sleep_time: The number of seconds to wait between downloads.
        :type sleep_time: int

        :param start_ep: The number to start episode labeling with.
        :type start_ep: int
        """
        extracted_games = self.get_and_extract_games_for_week(
            season=season, week=week, teams=teams, replay_types=replay_types
        )
        if start_ep is None:
            start_ep = get_max_episode_number_in_dir(self.destination_dir)

        for idx, game in enumerate(extracted_games):
            ep_num = start_ep + idx + 1

            self.download_game(game=game, ep_num=ep_num)
            logger.info(f"Downloaded {idx + 1}/{len(extracted_games)}")
            logger.info(f"Pausing for {sleep_time} seconds")
            time.sleep(sleep_time)
