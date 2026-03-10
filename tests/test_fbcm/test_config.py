import os

import pytest
from click import UsageError

from fbcm.config import (
    ConvertFormatConfig,
    DownloadListConfig,
    GenerateNfoConfig,
    NFLGamesConfig,
    NFLShowConfig,
)


class TestDownloadListConfig:
    def test_cli_values_take_precedence(self):
        config = {"download_list": {"output_directory": "/config/dir"}}
        cfg = DownloadListConfig.from_cli_and_config(
            config=config,
            output_directory="/cli/dir",
            cookies_file="/cli/cookies.txt",
        )
        assert cfg.output_directory == "/cli/dir"
        assert cfg.cookies_file == "/cli/cookies.txt"

    def test_falls_back_to_command_config(self):
        config = {
            "download_list": {
                "output_directory": "/config/dir",
                "cookies_file": "/config/cookies.txt",
            }
        }
        cfg = DownloadListConfig.from_cli_and_config(
            config=config, output_directory=None, cookies_file=None
        )
        assert cfg.output_directory == "/config/dir"
        assert cfg.cookies_file == "/config/cookies.txt"

    def test_falls_back_to_common_config(self):
        config = {
            "output_directory": "/common/dir",
            "cookies_file": "/common/cookies.txt",
        }
        cfg = DownloadListConfig.from_cli_and_config(
            config=config, output_directory=None, cookies_file=None
        )
        assert cfg.output_directory == "/common/dir"
        assert cfg.cookies_file == "/common/cookies.txt"

    def test_raises_when_output_directory_missing(self):
        with pytest.raises(UsageError, match="--output-directory is required"):
            DownloadListConfig.from_cli_and_config(
                config={}, output_directory=None, cookies_file=None
            )

    def test_command_config_overrides_common_config(self):
        config = {
            "output_directory": "/common/dir",
            "download_list": {"output_directory": "/cmd/dir"},
        }
        cfg = DownloadListConfig.from_cli_and_config(
            config=config, output_directory=None, cookies_file=None
        )
        assert cfg.output_directory == "/cmd/dir"


class TestNFLShowConfig:
    def test_cli_values_take_precedence(self):
        config = {"nfl_show": {"output_directory": "/config/dir"}}
        cfg = NFLShowConfig.from_cli_and_config(
            config=config,
            output_directory="/cli/dir",
            cookies_file="/cli/cookies.txt",
        )
        assert cfg.output_directory == "/cli/dir"
        assert cfg.cookies_file == "/cli/cookies.txt"

    def test_falls_back_to_config(self):
        config = {
            "nfl_show": {
                "output_directory": "/config/dir",
                "cookies_file": "/config/cookies.txt",
            }
        }
        cfg = NFLShowConfig.from_cli_and_config(
            config=config, output_directory=None, cookies_file=None
        )
        assert cfg.output_directory == "/config/dir"
        assert cfg.cookies_file == "/config/cookies.txt"

    def test_defaults_to_none(self):
        cfg = NFLShowConfig.from_cli_and_config(
            config={}, output_directory=None, cookies_file=None
        )
        assert cfg.output_directory is None
        assert cfg.cookies_file is None


class TestNFLGamesConfig:
    def test_cli_values_take_precedence(self):
        cfg = NFLGamesConfig.from_cli_and_config(
            config={"nfl_games": {"season": 2020}},
            output_directory="/cli/dir",
            cookies_file="/cli/cookies.txt",
            credentials_file=None,
            nfl_username="user@test.com",
            nfl_password="pass123",
            show_login=False,
            season=2025,
            week=(1, 2),
            team=("PIT",),
            exclude=("BAL",),
            replay_type=("condensed",),
            start_ep=10,
            list_only=True,
        )
        assert cfg.output_directory == "/cli/dir"
        assert cfg.cookies_file == "/cli/cookies.txt"
        assert cfg.nfl_username == "user@test.com"
        assert cfg.nfl_password == "pass123"
        assert cfg.season == 2025
        assert cfg.week == [1, 2]
        assert cfg.team == ["PIT"]
        assert cfg.exclude == ["BAL"]
        assert cfg.replay_type == ["condensed"]
        assert cfg.start_ep == 10
        assert cfg.list_only is True

    def test_falls_back_to_command_config(self):
        config = {
            "nfl_games": {
                "season": 2023,
                "week": [5, 6],
                "team": ["DAL"],
                "replay_type": ["condensed"],
            }
        }
        cfg = NFLGamesConfig.from_cli_and_config(
            config=config,
            output_directory=None,
            cookies_file=None,
            credentials_file=None,
            nfl_username=None,
            nfl_password=None,
            show_login=False,
            season=None,
            week=(),
            team=(),
            exclude=(),
            replay_type=(),
            start_ep=None,
            list_only=None,
        )
        assert cfg.season == 2023
        assert cfg.week == [5, 6]
        assert cfg.team == ["DAL"]
        assert cfg.replay_type == ["condensed"]

    def test_defaults_applied(self):
        cfg = NFLGamesConfig.from_cli_and_config(
            config={},
            output_directory=None,
            cookies_file=None,
            credentials_file=None,
            nfl_username=None,
            nfl_password=None,
            show_login=False,
            season=None,
            week=(),
            team=(),
            exclude=(),
            replay_type=(),
            start_ep=None,
            list_only=None,
        )
        assert cfg.output_directory == os.getcwd()
        assert cfg.cookies_file == "cookies.txt"
        assert cfg.show_login is False
        assert cfg.week == list(range(1, 19))
        assert cfg.team == []
        assert cfg.exclude == []
        assert cfg.replay_type == ["full_game"]
        assert cfg.start_ep is None
        assert cfg.list_only is False

    def test_common_config_fallback(self):
        config = {
            "output_directory": "/common/dir",
            "cookies_file": "/common/cookies.txt",
            "credentials_file": "/common/creds.json",
        }
        cfg = NFLGamesConfig.from_cli_and_config(
            config=config,
            output_directory=None,
            cookies_file=None,
            credentials_file=None,
            nfl_username=None,
            nfl_password=None,
            show_login=False,
            season=None,
            week=(),
            team=(),
            exclude=(),
            replay_type=(),
            start_ep=None,
            list_only=None,
        )
        assert cfg.output_directory == "/common/dir"
        assert cfg.cookies_file == "/common/cookies.txt"
        assert cfg.credentials_file == "/common/creds.json"

    def test_empty_tuples_treated_as_unset(self):
        cfg = NFLGamesConfig.from_cli_and_config(
            config={"nfl_games": {"week": [3]}},
            output_directory=None,
            cookies_file=None,
            credentials_file=None,
            nfl_username=None,
            nfl_password=None,
            show_login=False,
            season=None,
            week=(),
            team=(),
            exclude=(),
            replay_type=(),
            start_ep=None,
            list_only=None,
        )
        assert cfg.week == [3]


class TestConvertFormatConfig:
    def test_cli_values_take_precedence(self):
        config = {"convert_format": {"orig_format": "avi"}}
        cfg = ConvertFormatConfig.from_cli_and_config(
            config=config,
            orig_format="webm",
            new_format="mkv",
            pretend=True,
            delete=True,
        )
        assert cfg.orig_format == "webm"
        assert cfg.new_format == "mkv"
        assert cfg.pretend is True
        assert cfg.delete is True

    def test_falls_back_to_command_config(self):
        config = {
            "convert_format": {
                "orig_format": "avi",
                "new_format": "mp4",
                "pretend": True,
                "delete": True,
            }
        }
        cfg = ConvertFormatConfig.from_cli_and_config(
            config=config,
            orig_format=None,
            new_format=None,
            pretend=None,
            delete=None,
        )
        assert cfg.orig_format == "avi"
        assert cfg.new_format == "mp4"
        assert cfg.pretend is True
        assert cfg.delete is True

    def test_defaults_applied(self):
        cfg = ConvertFormatConfig.from_cli_and_config(
            config={},
            orig_format=None,
            new_format=None,
            pretend=None,
            delete=None,
        )
        assert cfg.orig_format == "mkv"
        assert cfg.new_format == "mp4"
        assert cfg.pretend is False
        assert cfg.delete is False


class TestGenerateNfoConfig:
    def test_cli_values_take_precedence(self):
        config = {"generate_nfo_files": {"league": "cfl"}}
        cfg = GenerateNfoConfig.from_cli_and_config(
            config=config, league="ufl", overwrite=True
        )
        assert cfg.league == "ufl"
        assert cfg.overwrite is True

    def test_falls_back_to_command_config(self):
        config = {"generate_nfo_files": {"league": "cfl", "overwrite": True}}
        cfg = GenerateNfoConfig.from_cli_and_config(
            config=config, league=None, overwrite=None
        )
        assert cfg.league == "cfl"
        assert cfg.overwrite is True

    def test_defaults_applied(self):
        cfg = GenerateNfoConfig.from_cli_and_config(
            config={}, league=None, overwrite=None
        )
        assert cfg.league == "nfl"
        assert cfg.overwrite is False
