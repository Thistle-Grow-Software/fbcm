# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`fbcm` is a CLI tool for archiving football content (primarily NFL, also CFL and UFL). It wraps `yt-dlp` with specialized functionality for NFL Plus downloads, metadata generation, and media file management for Plex/Jellyfin compatibility.

## Build and Development Commands

```bash
# Sync dependencies (install project + dev deps)
uv sync --extra dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_fbcm/test_base.py

# Run a specific test
uv run pytest tests/test_fbcm/test_base.py::test_function_name -v

# Format code
uv run ruff format src/

# Lint (and auto-fix)
uv run ruff check --fix src/

# Type check
uv run mypy src/

# Format code
tgf-format
```

## Architecture

### CLI Entry Point
- `src/fbcm/fbcm.py` - Click-based CLI with commands: `download-list`, `update-metadata`, `nfl-show`, `nfl-games`, `rename-series`, `convert-format`, `generate-nfo-files`

### Core Modules
- `src/fbcm/base.py` - Contains `BaseDownloader` (yt-dlp wrapper), `FileOperationsUtil` (file renaming, format conversion, metadata updates), `MetaDataCreator` (NFO file generation), and league-specific helper functions for week/playoff calculations
- `src/fbcm/nfl.py` - `NFLShowDownloader` for NFL Plus TV series, `NFLWeeklyDownloader` (inherits BaseDownloader + NFLBaseIE) for game replays using the griddy NFL client

### Key Data Structures
- `base.py` contains team abbreviation mappings (`abbreviation_map`, `TEAM_FULL_NAMES`, `CITY_TO_ABBR`) used throughout for NFL/CFL/UFL team lookups
- `DEFAULT_REPLAY_TYPES` maps CLI options to NFL API replay type names

### File Naming Convention
Games are named: `{League} {replay_type} - s{season}e{episode} - {year}_Wk{week}_{away_abbr}_{at|vs}_{home_abbr}`

NFO metadata files (XML format) are generated alongside videos for Jellyfin/Plex parsing.

## Environment Variables

- `MEDIA_BASE_DIR` - Base directory for media storage (used by rename-series, nfl-show)
- `FIREFOX_PROFILE` - Firefox profile path for yt-dlp cookie extraction
- `DESTINATION_DIR` - Default output directory for nfl-games
- `CONCURRENT_FRAGMENTS` - yt-dlp concurrent fragment downloads (default: 1)
- `THROTTLED_RATE_LIMIT` - yt-dlp rate limit (default: 1000000)
- `AWS_CODEARTIFACT_TOKEN` - Authentication token used for interacting with AWS CodeArtifact PyPi repository
- `UV_INDEX_PRIVATE_REGISTRY_USERNAME` - Username used by `uv` when interacting with CodeArtifact
- `UV_INDEX_PRIVATE_REGISTRY_PASSWORD` - Same value as `AWS_CODEARTIFACT_TOKEN`, used by `uv` to interact with CodeArtifact
- `ISSUE_PREFIX` - Used by the `tgf-commit` function (described in the next section) to create commit messages that will be linked to Jira issues properly.

## Configuration File

The CLI supports YAML config files (`fbcm.yaml`) with auto-discovery:
1. Current working directory
2. `~/.config/fbcm.yaml`
3. Explicit `--config /path/to/config.yaml`

Precedence: CLI args > Config file > Defaults

See `fbcm.yaml.example` for the config file structure. Common options (`cookies_file`, `output_directory`, `pretend`, `verbose`) are mapped to command-specific parameter names via `src/fbcm/utils.py:COMMON_OPTION_MAPPINGS`.

## Dependencies

- `yt-dlp` - Core video downloading
- `griddy` - NFL API client for game data
- `ffmpeg-python` - Video format conversion (requires ffmpeg on PATH)
- `mutagen` - MP4 metadata manipulation
- `click` - CLI framework
- `pyyaml` - Config file parsing


## Custom Shell Functions and Aliases (from ~/.bashrc and ~/.bash_functions)
- `artifact-token` - Initializes necessary authentication info for interacting with AWS CodeArtifact. Usage: `artifact-token`
- `griddy` - Navigates to the project directory, sets project specific env vars, and invokes `artifact-token`. Usage: `griddy`
- `tgf-format` - Runs `isort` and `black` _in the current directory_. Usage: `tgf-format`
- `tgf-commit` - Stages, commits (signed), and pushes changes in one step. Enforces Conventional Commit formatting derived from the current branch name. Usage: `tgf-commit [-a] [-p|--pull-request] <message>` See `tgf-commit --help` for more.

## Git Conventions

- **Always run `tgf-format` before committing.**
- **Always use `tgf-commit` to commit changes.** It will automatically handle commit message formatting, and can create pull requests for you automatically. 

### Branch Naming Conventions
- All branches should be prefixed with the `<type>` of issue it addresses. Valid types are `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `style`, `perf`, and `build`.
- `<type>` should be followed by `/<$ISSUE_PREFIX>-<ISSUE NUMBER>`, and finally end with `-<short-description>`

### Examples

- `feat/TGS-31-player-stats`
- `docs/TGS-50-update-usage-docs`

It is crucial to follow this branch naming convention, as the `tgf-commit` command uses the branch name to form commit messages.

## Working Conventions
- When context usage exceeds 60%, proactively summarize current task state under "## Current Task" in this file
- Run /compact proactively rather than waiting for the context limit
- Always use `tgf-format` before commiting changes and `tgf-commit` to commit changes.
- Run `uv lock` before committing any time `pyproject.toml` has been modified.