"""Typed configuration dataclasses for fbcm CLI commands.

Each dataclass encapsulates the configuration for a specific CLI command,
handling the merge of CLI arguments with YAML config file values.
Precedence: CLI args > command-specific config > common config > defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any


def _resolve(
    param_name: str,
    cli_value: Any,
    command_config: dict[str, Any],
    common_config: dict[str, Any],
    common_key: str | None = None,
) -> Any:
    """Return the first non-None value from CLI, command config, or common config."""
    if cli_value is not None:
        return cli_value
    if param_name in command_config:
        return command_config[param_name]
    if common_key and common_key in common_config:
        return common_config[common_key]
    return None


def _resolve_list(
    param_name: str,
    cli_value: tuple | list | None,
    command_config: dict[str, Any],
    common_config: dict[str, Any],
    common_key: str | None = None,
) -> list | None:
    """Resolve a list/tuple parameter, converting empty tuples to None."""
    # Click passes empty tuples for unset `multiple=True` options
    if cli_value and len(cli_value) > 0:
        return list(cli_value)
    if param_name in command_config:
        val = command_config[param_name]
        return list(val) if val else None
    if common_key and common_key in common_config:
        val = common_config[common_key]
        return list(val) if val else None
    return None


@dataclass
class DownloadListConfig:
    """Configuration for the download-list command."""

    output_directory: str
    cookies_file: str | None = None

    @classmethod
    def from_cli_and_config(
        cls,
        config: dict[str, Any],
        output_directory: str | None,
        cookies_file: str | None,
    ) -> DownloadListConfig:
        cmd_cfg = config.get("download_list", {}) or {}

        resolved_output = _resolve(
            "output_directory", output_directory, cmd_cfg, config, "output_directory"
        )
        resolved_cookies = _resolve(
            "cookies_file", cookies_file, cmd_cfg, config, "cookies_file"
        )

        if not resolved_output:
            from click import UsageError

            raise UsageError("--output-directory is required (via option or config)")

        return cls(
            output_directory=resolved_output,
            cookies_file=resolved_cookies,
        )


@dataclass
class NFLShowConfig:
    """Configuration for the nfl-show command."""

    output_directory: str | None = None
    cookies_file: str | None = None

    @classmethod
    def from_cli_and_config(
        cls,
        config: dict[str, Any],
        output_directory: str | None,
        cookies_file: str | None,
    ) -> NFLShowConfig:
        cmd_cfg = config.get("nfl_show", {}) or {}

        return cls(
            output_directory=_resolve(
                "output_directory",
                output_directory,
                cmd_cfg,
                config,
                "output_directory",
            ),
            cookies_file=_resolve(
                "cookies_file", cookies_file, cmd_cfg, config, "cookies_file"
            ),
        )


@dataclass
class NFLGamesConfig:
    """Configuration for the nfl-games command."""

    output_directory: str = ""
    cookies_file: str = "cookies.txt"
    credentials_file: str | None = None
    nfl_username: str | None = None
    nfl_password: str | None = None
    show_login: bool = False
    season: int = 0
    week: list[int] = field(default_factory=lambda: list(range(1, 19)))
    team: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    replay_type: list[str] = field(default_factory=lambda: ["full_game"])
    start_ep: int | None = None
    list_only: bool = False

    def __post_init__(self) -> None:
        if not self.output_directory:
            self.output_directory = os.getcwd()
        if self.season == 0:
            self.season = date.today().year

    @classmethod
    def from_cli_and_config(
        cls,
        config: dict[str, Any],
        output_directory: str | None,
        cookies_file: str | None,
        credentials_file: str | None,
        nfl_username: str | None,
        nfl_password: str | None,
        show_login: bool,
        season: int | None,
        week: tuple[int, ...],
        team: tuple[str, ...],
        exclude: tuple[str, ...],
        replay_type: tuple[str, ...],
        start_ep: int | None,
        list_only: bool | None,
    ) -> NFLGamesConfig:
        cmd_cfg = config.get("nfl_games", {}) or {}

        return cls(
            output_directory=_resolve(
                "output_directory",
                output_directory,
                cmd_cfg,
                config,
                "output_directory",
            )
            or "",
            cookies_file=_resolve(
                "cookies_file", cookies_file, cmd_cfg, config, "cookies_file"
            )
            or "cookies.txt",
            credentials_file=_resolve(
                "credentials_file",
                credentials_file,
                cmd_cfg,
                config,
                "credentials_file",
            ),
            nfl_username=_resolve(
                "nfl_username",
                nfl_username if nfl_username else None,
                cmd_cfg,
                config,
                "nfl_username",
            ),
            nfl_password=_resolve(
                "nfl_password",
                nfl_password if nfl_password else None,
                cmd_cfg,
                config,
                "nfl_password",
            ),
            show_login=_resolve(
                "show_login", show_login if show_login else None, cmd_cfg, config
            )
            or False,
            season=_resolve("season", season if season else None, cmd_cfg, config) or 0,
            week=_resolve_list("week", week, cmd_cfg, config) or list(range(1, 19)),
            team=_resolve_list("team", team, cmd_cfg, config) or [],
            exclude=_resolve_list("exclude", exclude, cmd_cfg, config) or [],
            replay_type=_resolve_list("replay_type", replay_type, cmd_cfg, config)
            or ["full_game"],
            start_ep=_resolve("start_ep", start_ep, cmd_cfg, config),
            list_only=_resolve(
                "list_only", list_only if list_only else None, cmd_cfg, config
            )
            or False,
        )


@dataclass
class ConvertFormatConfig:
    """Configuration for the convert-format command."""

    orig_format: str = "mkv"
    new_format: str = "mp4"
    pretend: bool = False
    delete: bool = False

    @classmethod
    def from_cli_and_config(
        cls,
        config: dict[str, Any],
        orig_format: str | None,
        new_format: str | None,
        pretend: bool | None,
        delete: bool | None,
    ) -> ConvertFormatConfig:
        cmd_cfg = config.get("convert_format", {}) or {}

        return cls(
            orig_format=_resolve("orig_format", orig_format, cmd_cfg, config) or "mkv",
            new_format=_resolve("new_format", new_format, cmd_cfg, config) or "mp4",
            pretend=_resolve(
                "pretend", pretend if pretend else None, cmd_cfg, config, "pretend"
            )
            or False,
            delete=_resolve("delete", delete if delete else None, cmd_cfg, config)
            or False,
        )


@dataclass
class GenerateNfoConfig:
    """Configuration for the generate-nfo-files command."""

    league: str = "nfl"
    overwrite: bool = False

    @classmethod
    def from_cli_and_config(
        cls,
        config: dict[str, Any],
        league: str | None,
        overwrite: bool | None,
    ) -> GenerateNfoConfig:
        cmd_cfg = config.get("generate_nfo_files", {}) or {}

        return cls(
            league=_resolve("league", league, cmd_cfg, config) or "nfl",
            overwrite=_resolve(
                "overwrite", overwrite if overwrite else None, cmd_cfg, config
            )
            or False,
        )
