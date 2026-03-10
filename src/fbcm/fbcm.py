import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from random import uniform

import click

from .config import (
    ConvertFormatConfig,
    DownloadListConfig,
    GenerateNfoConfig,
    NFLGamesConfig,
    NFLShowConfig,
)
from .mappings import DEFAULT_REPLAY_TYPES, POSITIONS, TEAM_FULL_NAMES
from .utils import find_config, load_config

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=False),
    help="Path to config file. Auto-discovers fbcm.yaml in CWD or ~/.config/ if not specified.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG level) logging.",
)
@click.option(
    "--log-file",
    type=click.Path(),
    default=None,
    help="Path to a file where logs should be written in addition to the console.",
)
@click.pass_context
def cli(ctx, config, verbose, log_file):
    """fbcm - Football content manager and archiving tools."""
    from .logging_config import setup_logging

    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level, log_file=log_file)

    ctx.ensure_object(dict)
    config_path = find_config(config)
    ctx.obj["config"] = load_config(config_path)
    if config_path:
        click.echo(f"Using config: {config_path}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-directory",
    type=click.Path(exists=True),
    help="The path to store the downloaded videos in.",
)
@click.option(
    "--cookies-file",
    type=click.Path(exists=True),
    help="If authentication is required, you can provide a cookies file via this flag. The file must follow the Netscape format.",
)
@click.pass_context
def download_list(ctx, input_file, output_directory, cookies_file: Path = None):
    """
    Download a list of URLS provided via INPUT_FILE.

    INPUT_FILE is the path to a text file where video URLs are listed, one per line.
    """
    from .downloaders import BaseDownloader

    config = ctx.obj.get("config", {})
    cfg = DownloadListConfig.from_cli_and_config(
        config=config,
        output_directory=output_directory,
        cookies_file=cookies_file,
    )

    bd = BaseDownloader(
        cookie_file_path=cfg.cookies_file,
        destination_dir=cfg.output_directory,
    )
    bd.download_from_file(Path(input_file))


@cli.command()
@click.argument("input_file")
@click.option(
    "--output-directory",
    type=click.Path(exists=True),
    help="The path to store the downloaded videos in.",
)
@click.option(
    "--cookies-file",
    type=click.Path(exists=True),
    help="A .txt file containing NFL authentication cookies following the Netscape format.",
)
@click.pass_context
def nfl_show(ctx, input_file, output_directory, cookies_file):
    """
    Download episodes from shows available on NFL Plus.

    INPUT_FILE is a JSON file containing the URL leaf nfl.com uses for each episode.
    """
    from .nfl import NFLShowDownloader

    config = ctx.obj.get("config", {})
    cfg = NFLShowConfig.from_cli_and_config(
        config=config,
        output_directory=output_directory,
        cookies_file=cookies_file,
    )

    click.echo("Downloading NFL show")
    nfl = NFLShowDownloader(input_file, cfg.cookies_file, cfg.output_directory)
    nfl.download_episodes()


@cli.command()
@click.option(
    "--output-directory",
    envvar="DESTINATION_DIR",
    type=click.Path(exists=True),
    help="Directory the downloaded games should be saved to.",
)
@click.option(
    "--cookies-file",
    type=click.Path(exists=True),
    help="A txt file containing cookies needed for NFL API authentication.",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True),
    help="A JSON file containing NFL auth tokens (accessToken, refreshToken, expiresIn). "
    "Cannot be used with --nfl-username/--nfl-password.",
)
@click.option(
    "--nfl-username",
    type=str,
    help="The username/email associated with your NFL.com account. "
    "Cannot be used with --credentials-file.",
)
@click.option(
    "--nfl-password",
    type=str,
    help="The password associated with your NFL.com account. "
    "Cannot be used with --credentials-file.",
)
@click.option(
    "--show-login",
    type=bool,
    is_flag=True,
    help="When passed, show the browser window while performing automated login.",
)
@click.option("--season", type=int, help="Season games were played in")
@click.option("--week", type=int, multiple=True, help="Week the games were played in")
@click.option(
    "--team",
    multiple=True,
    type=str,
    help="Restrict downloads to a single team by providing the team's three letter abbreviation here. "
    "If blank, all are fetched.",
)
@click.option("--exclude", multiple=True, type=str, help="Teams to exclude")
@click.option(
    "--replay-type",
    multiple=True,
    type=click.Choice(DEFAULT_REPLAY_TYPES.keys(), case_sensitive=False),
    help="Specify which replay types to download. If blank, the full game is downloaded.",
)
@click.option("--start-ep", type=int, help="Where to pick up episode numbering from.")
@click.option(
    "--list-only",
    type=bool,
    default=None,
    is_flag=True,
    flag_value=True,
    help="Don't download the games, only list them to stdout.",
)
@click.pass_context
def nfl_games(
    ctx,
    output_directory: str,
    cookies_file: str,
    credentials_file: str,
    nfl_username: str,
    nfl_password: str,
    show_login: bool,
    season: int,
    week: tuple[int],
    team: tuple[str],
    exclude: tuple[str],
    replay_type: tuple[str],
    start_ep: int,
    list_only: bool,
):
    # TODO: Ensure jellyfin isn't running..it borks the post processing
    """
    Download NFL game replays of the specified SEASON and WEEK

    SEASON Is the year (2009 or later) for which to download replays.
    WEEK The season week number to download replays for.
    """
    from .nfl import NFLWeeklyDownloader

    config = ctx.obj.get("config", {})
    cfg = NFLGamesConfig.from_cli_and_config(
        config=config,
        output_directory=output_directory,
        cookies_file=cookies_file,
        credentials_file=credentials_file,
        nfl_username=nfl_username,
        nfl_password=nfl_password,
        show_login=show_login,
        season=season,
        week=week,
        team=team,
        exclude=exclude,
        replay_type=replay_type,
        start_ep=start_ep,
        list_only=list_only,
    )

    # Validate mutual exclusivity: credentials_file vs username/password
    has_credentials_file = cfg.credentials_file is not None
    has_username_password = cfg.nfl_username is not None or cfg.nfl_password is not None

    if has_credentials_file and has_username_password:
        raise click.UsageError(
            "--credentials-file cannot be used with --nfl-username/--nfl-password. "
            "Use one authentication method or the other."
        )

    # Load credentials from file if provided
    nfl_auth = None
    if cfg.credentials_file:
        with open(cfg.credentials_file) as f:
            nfl_auth = json.load(f)
        click.echo(f"Using credentials file: {cfg.credentials_file}")
    else:
        click.echo(f"NFL Username: {cfg.nfl_username}")

    click.echo(f"Output directory: {cfg.output_directory}")
    click.echo(f"Cookies file: {cfg.cookies_file}")
    click.echo(f"Show Login: {cfg.show_login}")
    click.echo(f"Season: {cfg.season}")
    click.echo(f"Week: {cfg.week}")
    click.echo(f"Team: {cfg.team}")
    click.echo(f"Exclude: {cfg.exclude}")
    click.echo(f"Replay Type: {cfg.replay_type}")
    click.echo(f"Start episode: {cfg.start_ep}")

    profile_dir = os.getenv("FIREFOX_PROFILE")
    allowed_extractors = ["nfl.com:plus:replay"]
    extractor_args = {"nflplusreplay": {"type": [cfg.replay_type[0]]}}

    add_opts = {
        "allowed_extractors": allowed_extractors,
        "extractor_args": extractor_args,
    }

    nwd = NFLWeeklyDownloader(
        firefox_profile_path=profile_dir,
        destination_dir=cfg.output_directory,
        nfl_username=cfg.nfl_username,
        nfl_password=cfg.nfl_password,
        nfl_auth=nfl_auth,
        show_login=cfg.show_login,
        add_yt_opts=add_opts,
    )

    if cfg.team:
        teams_to_fetch = [tm for tm in cfg.team if tm not in cfg.exclude]
    else:
        teams_to_fetch = [tm for tm in TEAM_FULL_NAMES if tm not in cfg.exclude]

    resolved_replay_types = [DEFAULT_REPLAY_TYPES[r] for r in cfg.replay_type]

    if cfg.list_only:
        games = []
        for wk in cfg.week:
            click.echo(f"Working on games for Week {wk}")
            wk_games = nwd.get_and_extract_games_for_week(
                season=cfg.season,
                week=wk,
                teams=teams_to_fetch,
                replay_types=resolved_replay_types,
            )
            games.extend(wk_games)

        for game in games:
            logger.info(f"{game}")

    else:
        for wk in cfg.week:
            click.echo(f"Working on games for Week {wk}")
            nwd.download_all_for_week(
                season=cfg.season,
                week=wk,
                teams=teams_to_fetch,
                replay_types=resolved_replay_types,
                start_ep=cfg.start_ep,
            )


@cli.command()
@click.option(
    "--output-directory",
    envvar="DESTINATION_DIR",
    type=click.Path(exists=True),
    help="Directory the downloaded games should be saved to.",
)
@click.option(
    "--position",
    type=str,
    multiple=True,
    help="Extract draft profiles for the specified position",
)
@click.option(
    "--input-file",
    type=click.Path(exists=True),
    help="A text file containing multiple player slugs "
    "(one per line) to extract profiles for.",
)
@click.pass_context
def extract_draft_profiles(
    ctx,
    output_directory: str,
    position: str,
    input_file: str,
):
    from playwright._impl._errors import TimeoutError
    from playwright.sync_api import sync_playwright

    from .draft_buzz import DraftBuzzScraper

    selected_positions = list(position)
    if not selected_positions:
        logger.info("No positions selected. Defaulting to all.")
        selected_positions = POSITIONS
    logger.info(f"Position: {selected_positions}")

    with open(input_file) as infile:
        profile_urls = json.load(infile)

    with sync_playwright() as playwright:
        scraper = DraftBuzzScraper(
            playwright=playwright, profile_root_dir=Path(output_directory)
        )

        completed_profiles = []
        with open("input_files/completed.json") as infile:
            completed_profiles = json.load(infile)

        click.echo(f"Loaded {len(completed_profiles)} completed profiles.")

        for pos in selected_positions:
            if pos not in profile_urls:
                raise click.BadParameter(f"{pos} is not present in the input file.")

            position_profiles = profile_urls[pos]
            click.echo(f"Found {len(position_profiles)} {pos} profile URLs to extract.")

            position_player_data = {}

            for prof_slug in position_profiles:
                if prof_slug in completed_profiles:
                    click.echo(f"Already completed {prof_slug}. Skipping.")
                    continue

                click.echo(f"Processing player profile: {prof_slug}")
                time.sleep(uniform(3.5, 4.5))

                try:
                    player_data = scraper.scrape_from_url(url=prof_slug, position=pos)
                    position_player_data[player_data.basic_info.full_name] = (
                        player_data.to_dict()
                    )
                    scraper.save_player_photo_to_disk()

                    completed_profiles.append(prof_slug)

                except TimeoutError:
                    dump_currently_completed(
                        position=pos,
                        data=position_player_data,
                        completed_list=completed_profiles,
                    )
                    raise
            dump_currently_completed(
                position=pos,
                data=position_player_data,
                completed_list=completed_profiles,
            )

            time.sleep(random.uniform(10, 15))


@cli.command()
@click.option(
    "--output-directory",
    envvar="DESTINATION_DIR",
    type=click.Path(exists=True),
    help="Directory the downloaded games should be saved to.",
)
@click.option(
    "--position",
    type=str,
    multiple=True,
    help="Extract draft profiles for the specified position",
)
@click.pass_context
def gen_prospect_word_docs(
    ctx,
    output_directory: str,
    position: str,
):
    from .docx.word_gen import WordDocGenerator
    from .models import ProspectDataSoup

    selected_positions = list(position)
    if not selected_positions:
        click.echo("No positions selected. Defaulting to all.")
        selected_positions = POSITIONS
    click.echo(f"Position: {selected_positions}")

    wdg = WordDocGenerator(
        output_path=output_directory,
        ring_image_base_dir=output_directory,
        colors_path="input_files/school_colors.json",
    )

    click.echo(f"Provided output directory: {output_directory}")
    for position in selected_positions:
        click.echo(f"Generating docs for {position} position.")
        input_file = f"output_data/{position}.json"

        with open(input_file) as infile:
            position_data = json.load(infile)

        click.echo(f"Processing {len(position_data)} profiles.")

        cur_count = 1
        for prospect_name, data in position_data.items():
            click.echo(
                f"Generating profile for {prospect_name}, #{cur_count} of {len(position_data)}"
            )

            prospect = ProspectDataSoup.from_dict(data=data)
            wdg.add_prospect(prospect=prospect)

            wdg.generate_complete_document()
            cur_count += 1
    wdg.generate_complete_document(filename="2026_All_Prospects_COMPLETE.docx")


@cli.command()
@click.pass_context
def update_draft_prospect_urls(ctx):
    from playwright._impl._errors import TimeoutError
    from playwright.sync_api import sync_playwright

    from .draft_buzz import ProspectProfileListExtractor

    profile_lists = {}
    with sync_playwright() as playwright:
        pple = ProspectProfileListExtractor(playwright=playwright)

        for position in POSITIONS:
            try:
                profile_lists[position] = pple.extract_prospect_urls_for_position(
                    pos=position
                )
            except TimeoutError:
                logger.warning(
                    f"Position {position} timed out. Sleeping, then moving on to next position."
                )
                time.sleep(5)

    with open("prospect_urls.json", "w") as outfile:
        json.dump(profile_lists, outfile, indent=4)


def dump_currently_completed(position, data, completed_list):
    rn = datetime.now()
    suffix = f"{rn.hour}_{rn.minute}_{rn.second}"
    fname = f"{position}_redo_{suffix}.json"

    with open(f"output_data/{fname}", "w") as outfile:
        json.dump(data, outfile, indent=4)

    with open("input_files/completed.json", "w") as outfile:
        json.dump(completed_list, outfile, indent=4)


@cli.command()
@click.pass_context
def draft_sandbox(ctx):
    from .docx.word_gen import WordDocGenerator
    from .models import ProspectDataSoup

    click.echo("Draft profile sandbox...")

    with open("output_data/QB.json") as infile:
        qb_data = json.load(infile)

    fm_data = qb_data["Fernando Mendoza"]
    mendoza_obj = ProspectDataSoup.from_dict(fm_data)
    wdg = WordDocGenerator(
        prospect=mendoza_obj,
        output_path="output_data",
        ring_image_base_dir="output_data",
        colors_path="input_files/school_colors.json",
    )
    wdg.generate_complete_document()


@cli.command()
@click.argument("directory")
@click.option(
    "--pretend",
    default=None,
    is_flag=True,
    flag_value=True,
    help="If passed, don't perform actual updates. Preview only.",
)
@click.option(
    "--orig-format",
    type=str,
    default=None,
    help="fbcm will attempt to convert all videos with the file extension provided here.",
)
@click.option(
    "--new-format", type=str, default=None, help="The desired output file type."
)
@click.option(
    "--delete",
    default=None,
    is_flag=True,
    flag_value=True,
    help="If passed, remove the mkv files after conversion.",
)
@click.pass_context
def convert_format(
    ctx,
    directory: str,
    pretend: bool,
    orig_format: str,
    new_format: str,
    delete: bool,
):
    """
    Convert mkv files stored in DIRECTORY to mp4 files. Other formats will be added eventually.

    DIRECTORY is the directory fbcm will search for mkv files to convert.
    """
    from .file_operations import FileOperationsUtil

    config = ctx.obj.get("config", {})
    cfg = ConvertFormatConfig.from_cli_and_config(
        config=config,
        orig_format=orig_format,
        new_format=new_format,
        pretend=pretend,
        delete=delete,
    )

    conv_dir = Path(directory)
    if not conv_dir.is_dir():
        raise FileNotFoundError(f"Directory {conv_dir} does not exist.")

    fops_util = FileOperationsUtil(conv_dir, cfg.pretend)
    fops_util.convert_formats(
        orig_format=cfg.orig_format, new_format=cfg.new_format, delete=cfg.delete
    )


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.argument("season", type=int)
@click.argument("dates", type=click.Path(exists=True))
@click.option("--league", type=str, default=None, help="One of nfl, ufl, cfl")
@click.option(
    "--overwrite",
    type=bool,
    default=None,
    is_flag=True,
    flag_value=True,
    help="Passing this flag tells fbcm to overwrite any existing .nfo files it may encounter for a given video.",
)
@click.pass_context
def generate_nfo_files(
    ctx,
    directory: str,
    season: int,
    dates: str,
    league: str,
    overwrite: bool,
):
    """
    Construct .nfo files for games of the given league + season combo.

    DIRECTORY is the league's base directory, i.e. the one containing all season directories.
    SEASON is the year we should generate .nfo files for, e.g. 2025
    DATES is a JSON file mapping game numbers to the date they were played.

    """
    from .metadata import MetaDataCreator

    config = ctx.obj.get("config", {})
    cfg = GenerateNfoConfig.from_cli_and_config(
        config=config,
        league=league,
        overwrite=overwrite,
    )

    click.echo(f"Generating .nfo files for {cfg.league.upper()} season {season}.")
    click.echo(f"Looking for relevant video files in {directory}")
    with open(dates) as infile:
        game_dates = json.load(infile)

    mdc = MetaDataCreator(base_dir=directory, game_dates=game_dates, league=cfg.league)

    mdc.create_nfo_for_season(year=season, overwrite=cfg.overwrite)
    click.echo("Done")
