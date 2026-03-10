import logging
from dataclasses import dataclass
from pathlib import Path

from .mappings import ABBREVIATION_MAP
from .utils import generate_episode_metadata_xml

logger = logging.getLogger(__name__)


def convert_nfl_playoff_name_to_int(year: int, week_name: str) -> int | None:
    """
    Given a season and week name, determine the week number of the game.

    :param year: The year during which the regular season associated with the postseason game was played.
    :type year: int
    :param week_name: The game's name. One of 'Wild Card', 'Divisional', 'Conference Championship', or 'Super Bowl'
    :type week_name: str
    :return: The week number that the named game was played during the provided season.
    """
    num = None

    if year < 1978:
        # Through 1997: 14 week schedule, no bye week, no wildcard
        if week_name == "Divisional":
            num = 15
        elif week_name == "Conference Championship":
            num = 16
        elif "Super Bowl" in week_name:
            num = 17
    elif year < 1990:
        # 1978 - 1989: 16 week schedule, no bye week, wildcard round
        if week_name == "Wild Card":
            num = 17
        elif week_name == "Divisional":
            num = 18
        elif week_name == "Conference Championship":
            num = 19
        elif "Super Bowl" in week_name:
            num = 20
    elif year == 1993 or year > 2020:
        # 1993: 18 week schedule, two bye weeks (16 games), wildcard round
        # 2021 - Current: 18 week schedule (17 games), wildcard round, results in
        # Same numbering as 1993
        if week_name == "Wild Card":
            num = 19
        elif week_name == "Divisional":
            num = 20
        elif week_name == "Conference Championship":
            num = 21
        elif "Super Bowl" in week_name:
            num = 22
    elif year < 2021:
        # 1990 - 2020 (except 1993): 17 week schedule, one bye week, wildcard round
        if week_name == "Wild Card":
            num = 18
        elif week_name == "Divisional":
            num = 19
        elif week_name == "Conference Championship":
            num = 20
        elif "Super Bowl" in week_name:
            num = 21

    return num


def convert_ufl_playoff_name_to_int(year: int, week_name: str) -> int | None:
    """
    Given a UFL season and a week name, determine the week number of the game.

    :param year: The year the game was played. Included for potential future schedule changes.
    :param week_name: The game's name. One of 'Conference Championship' or 'UFL Championship'
    :return:
    """
    num = None
    if week_name == "Conference Championship":
        num = 11
    elif week_name == "UFL Championship":
        num = 12
    return num


def convert_cfl_playoff_name_to_int(year: int, week_name: str) -> int | None:
    """
    Given a CFL season and a week name, determine the week number of the game.

    :param year: The year the game was played. Included for potential future schedule changes.
    :param week_name: The game's name. One of 'Conference Championship' or 'UFL Championship'
    :return:
    """
    num = None
    if "Semi-Final" in week_name:
        num = 22
    elif "Final" in week_name or "Grey Cup" in week_name:
        num = 23
    return num


def get_week_int_as_string(
    week: str, year: int | None = None, league: str = "nfl"
) -> str:
    """
    Given a week's name and a season, determine the week number of the game.

    :param week: The week name (e.g. 'Wild Card', 'Divisional', etc.)
    :type week: int
    :param year: The season that the game was played.
    :type year: int
    :param league: String indicating which league we are working with. Currently nfl, ufl, and cfl are supported.
    :type league: str
    :return: A string, left padded to a length of 2, representing the week number of the game.
    :rtype: str
    """
    if num := is_playoff_week(week):
        match league:
            case "ufl":
                num = convert_ufl_playoff_name_to_int(year, week_name=num)
            case "cfl":
                num = convert_cfl_playoff_name_to_int(year, week_name=num)
            case "nfl":
                num = convert_nfl_playoff_name_to_int(year, week_name=num)

        return str(num).zfill(2)
    num = ""
    for c in week.lower().replace("wk", ""):
        if not c.isdigit():
            break
        num += c

    # If we're given an invalid week, return the empty string.
    # Without this ternary, "00" would be returned
    return num.zfill(2) if num else ""


def is_playoff_week(week_str: str) -> str:
    """
    Given a short string that was stored alongside a week number in a file name,
    determine the corresponding pretty representation.
    :param week_str: The short string that was stored in the file name. One of 'wc', 'div', 'conf', 'uflchamp', or 'sb'
    :return: The title cased, full version of the week's name.
    :rtype: str
    """
    for week_type in ["wc", "div", "conf", "sb", "esf", "wsf", "wf", "ef", "gc"]:
        if week_type in week_str.lower():
            match week_type:
                case "wc":
                    return "Wild Card"
                case "div":
                    return "Divisional"
                case "conf":
                    return "Conference Championship"
                case "uflchamp":
                    return "UFL Championship"
                case "sb":
                    sb_num = week_str.lower().split("sb")[-1]
                    return f"Super Bowl {sb_num.upper()}"
                case "wsf":
                    return "Western Semi-Final"
                case "esf":
                    return "Eastern Semi-Final"
                case "wf":
                    return "Western Final"
                case "ef":
                    return "Eastern Final"
                case "gc":
                    return "Grey Cup"
                case _:
                    return ""
    return ""


@dataclass
class MetaDataCreator:
    """
    Create and store metadata based on information stored in file name.
    Used for replays downloaded before NFLWeeklyDownloader was implemented.
    """

    # season_premieres: Dict

    def __init__(
        self, base_dir: str | Path, game_dates: dict, league: str = "nfl"
    ) -> None:
        """
        Initialize the utility, set basic config.

        :param base_dir: The directory containing the videos to generate metadata for.
        :type base_dir: str | Path

        :param game_dates: A dict mapping seasons to a dict of week numbers -> date the game was played on.
        :type game_dates: Dict

        :param league: nfl, ufl, or cfl
        :type league: str
        """
        self.base_dir = base_dir
        self.game_dates = game_dates
        self.league = league

    def _create_title_string(self, file_stem: str) -> str:
        """
        Given the file name, create the title that should be displayed in viewing clients.

        :param file_stem: The file's base name.
        :type file_stem: str

        :return: The name to be stored in metadata.
        :rtype: str
        """
        # file_stem will be something like "2024_Wk01_PIT_at_ATL"
        base_name = file_stem.split(" - ")[-1]
        parts = base_name.split("_")

        year = parts[0]
        week = parts[1]

        week_repr = get_week_int_as_string(week, int(year), league=self.league)
        if suffix := is_playoff_week(week):
            week_repr += f" {suffix}"

        week_repr = week_repr.lstrip("0")

        team_one_abbr = parts[2]
        team_two_abbr = parts[4]

        team_one_city = ABBREVIATION_MAP.get(team_one_abbr)
        if team_one_city is None:
            raise ValueError(
                f"Could not find team {team_one_abbr} in abbreviation map."
            )

        team_two_city = ABBREVIATION_MAP.get(team_two_abbr)
        if team_two_city is None:
            raise ValueError(
                f"Could not find team {team_two_city} in abbreviation map."
            )

        # parts[3] is either "at" (for any game _not_ at a neutral site)
        # or "vs" (for neutral site games, i.e. the Super Bowl)
        return f"{year} Week {week_repr} - {team_one_city} {parts[3]} {team_two_city}"

    def construct_metadata_xml_for_game(self, game_stem: str) -> str:
        title = self._create_title_string(game_stem)

        year, episode_num = [
            x.replace("s", "").strip() for x in game_stem.split("-")[1].split("e")
        ]
        aired = self.game_dates[str(year)][episode_num.lstrip("0")]

        return generate_episode_metadata_xml(
            title=title,
            season=year,
            episode=episode_num.lstrip("0"),
            aired=aired,
        )

    def create_nfo_for_season(self, year: int, overwrite: bool = False) -> None:
        """
        Create metadata files for all games in the provided year

        :param year: The year to create metadata for.
        :type year: int

        :param overwrite: When True, overwrite any existing .nfo files of the same name as one we're generating
        :type overwrite: bool

        """
        season_dir = Path(self.base_dir, f"Season {year}")
        if not season_dir.exists():
            raise FileNotFoundError(f"{season_dir} does not exist.")

        for game in season_dir.rglob("*.mp4"):
            nfo_file = Path(season_dir, f"{game.stem}.nfo")
            if (not overwrite) and nfo_file.exists():
                logger.info(f"{nfo_file} already exists and overwrite=False. Skipping")
                continue

            logger.info(f"Creating {nfo_file}")
            nfo_file.touch()
            xml_str = self.construct_metadata_xml_for_game(game_stem=game.stem)
            nfo_file.write_text(xml_str)

    def rename_files_for_season(
        self, year: int, series_name: str = "NFL Games"
    ) -> None:
        """
        Add the necessary prefix to file names so that Jellyfin will parse
        the game replays as TV seasons.

        :param year: The season to rename video files for.
        :type year: int
        :param series_name: The name with which the games we're handling are prefixed.
        :type series_name: str
        """
        from .file_namer import SeriesFileNamer

        namer = SeriesFileNamer(series_name=series_name)
        season_dir = Path(self.base_dir, f"Season {year}")
        for f in season_dir.rglob(f"{year}*"):
            old_name = f.name
            week_substring = f.stem.split("_")[1]
            episode_number = "".join([c for c in week_substring if c.isdigit()])
            file_stem = namer.construct_file_name(
                season=year, episode=episode_number, episode_name=f.stem
            )
            new_path = f.with_name(f"{file_stem}{f.suffix}")
            f.replace(new_path)
            logger.info(f"Moved {old_name} -> {f.name}")
