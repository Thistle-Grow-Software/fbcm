# Usage

## Installation

Clone the repository and sync dependencies:

```bash
git clone <repo-url>
cd fbcm
uv sync
```

Building the docs (optional):

```bash
uv sync --extra docs
zensical serve
```

## Quick start

Once installed, the `fbcm` command is available:

```bash
fbcm --help
```

Common commands include:

- `fbcm download-list <INPUT_FILE> <OUTPUT_DIRECTORY> [--cookie-file cookies.txt]`
- `fbcm update-metadata <DIRECTORY_PATH> [--pretend] [--verbose]`
- `fbcm nfl-games <SEASON> <WEEK> [--team PIT] [--replay-type full_game] [--start-ep 0]`
- `fbcm rename-series <SERIES_NAME> [--release-year 2020] [--pretend] [--replace]`
- `fbcm convert-format <DIRECTORY> [--pretend] [--delete]`

## Environment variables

The following environment variables are used by various commands:

- `PROFILE_LOCATION`: Path to a Netscape-formatted cookie file for authenticated downloads (used by nfl_games).
- `DEST_DIR`: Default destination directory for downloaded game replays (used by nfl_games).
- `MEDIA_BASE_DIR`: Base media library directory for organizing shows and episodes (used by NFL show downloads and renaming utilities).
- `THROTTLED_RATE_LIMIT`: Optional rate limit passed to yt-dlp when throttled downloads are detected.

## Cookies

Some endpoints (e.g., NFL Plus) require authentication. Provide cookies exported in Netscape format either via:

- CLI options that accept a cookie file, or
- Setting `PROFILE_LOCATION` to point to your cookies file.

See the CLI reference for details on per-command options.
