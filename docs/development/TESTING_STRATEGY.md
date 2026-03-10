# FBCM Testing Strategy

## Current State

### Modules With Tests (8/18 source modules)

| Module | Test File | Coverage Level |
|--------|-----------|---------------|
| `metadata.py` (functions) | `test_base.py` | High — playoff conversion, week parsing |
| `config.py` | `test_config.py` | High — all `from_cli_and_config` paths |
| `browser_retry.py` | `test_browser_retry.py` | High — retry logic, error recovery |
| `file_namer.py` | `test_file_namer.py` | High — NFL/NCAA/Series naming |
| `constants.py` | `test_constants.py` | Basic validation |
| `utils.py` | `test_utils.py` | `generate_episode_metadata_xml` |
| `logging_config.py` | `test_logging_config.py` | `setup_logging` |
| `parsers/*` | `test_parsers/*` | High — all 5 parsers with HTML fixtures |

### Modules Without Tests

| Module | LOC | Risk | Testability |
|--------|-----|------|-------------|
| `models.py` | 393 | HIGH | Excellent — pure dataclasses, no I/O |
| `draft_buzz.py` | 409 | HIGH | Mixed — static methods testable, browser logic needs mocks |
| `docx/word_gen.py` | 920 | HIGH | Mixed — helpers testable, DOCX generation needs fixtures |
| `file_operations.py` | 234 | HIGH | Good — filesystem ops mockable with tmp_path |
| `nfl.py` | 499 | HIGH | Good — injectable deps, mockable API client |
| `metadata.py` (MetaDataCreator) | 137 | MEDIUM | Good — filesystem + string logic |
| `mcmillen.py` | 30 | MEDIUM | Good — mock requests |
| `downloaders/base_downloader.py` | 100 | MEDIUM | Low — yt-dlp wrapper |
| `fbcm.py` (CLI) | 626 | LOW | Can use Click's CliRunner |

## Testing Strategy

### Framework & Tools

- **pytest** (already in use) — test runner and fixtures
- **pytest-cov** — coverage reporting (added as dev dependency)
- **unittest.mock** — mocking external dependencies (Playwright, requests, ffmpeg, yt-dlp)
- **tmp_path** — pytest built-in fixture for filesystem tests
- **HTML fixtures** — already established pattern in `tests/test_fbcm/test_parsers/conftest.py`

### Testing Approach by Module Category

#### 1. Pure Logic (Unit Tests — No Mocking Required)

These modules have no external dependencies and can be tested directly:

- **`models.py`** — `from_dict()`, `to_dict()`, `_convert_value()`, position-aware type resolution
- **`docx/word_gen.py`** helpers — `blend_colors()`, `darken_color()`, `hex_to_rgb()`, `skill_bar()`, `get_primary_position()`
- **`metadata.py`** `MetaDataCreator._create_title_string()`

#### 2. I/O-Dependent (Mock External Dependencies)

- **`file_operations.py`** — Use `tmp_path` for filesystem, mock `mutagen.mp4.MP4` and `ffmpeg`
- **`nfl.py`** — Mock `GriddyNFL` client, use injectable collaborators
- **`draft_buzz.py`** — Mock Playwright browser/page objects, test parsing orchestration with HTML fixtures
- **`mcmillen.py`** — Mock `requests.get`, test HTML parsing with fixture strings

#### 3. Integration-Heavy (Defer or Mark as `@pytest.mark.integration`)

- **`fbcm.py`** CLI commands — Click's `CliRunner` for smoke tests
- **`downloaders/base_downloader.py`** — yt-dlp wrapper, low value to unit test
- **`docx/word_gen.py`** DOCX generation — complex document rendering, consider golden-file approach later

### Fixture Strategy

- **HTML fixtures**: Continue the established pattern in `conftest.py` for parser and scraper tests
- **Factory fixtures**: Use `@pytest.fixture` factories (like existing `make_soup`) for creating test data
- **Model fixtures**: Create reusable prospect data fixtures for `word_gen.py` and `draft_buzz.py` tests
- **tmp_path**: Use pytest's built-in `tmp_path` for all filesystem operations

### Coverage Target

Given the I/O-heavy nature of the codebase:

- **Target: 70% line coverage** as initial goal
- **Pure logic modules**: Target 90%+ (models, helpers, metadata functions)
- **I/O modules**: Target 60%+ (mock boundaries, test business logic)
- **CLI/integration**: Defer to future tickets, mark with `@pytest.mark.integration`

### Snapshot/Golden-File Testing

Not recommended at this stage. The parsers already use HTML fixture strings effectively.
Golden-file testing could be considered later for DOCX output validation if visual regression
becomes a concern.

### Browser-Dependent Tests

- Mock Playwright objects (`Browser`, `Page`, `Locator`) for unit tests
- Static methods in `PageFetcher` (`_make_absolute_url`, `_get_image_type`, `_should_skip_image`) are testable without mocks
- Full browser integration tests should be marked `@pytest.mark.integration` and `@pytest.mark.slow`

## Pytest Configuration

The following additions were made to `pyproject.toml`:

- `pytest-cov` added to dev dependencies
- Coverage configuration updated with `--cov` flags in `addopts`
- Coverage report configured with `fail_under` threshold

## Priority Order for Test Implementation

1. `models.py` — Used everywhere, pure logic, highest ROI
2. `docx/word_gen.py` helpers — Pure functions, easy wins
3. `file_operations.py` — Safety-critical filesystem operations
4. `nfl.py` (`GameExtractor`, `MetadataWriter`) — Core business logic
5. `metadata.py` (`MetaDataCreator`) — String construction + filesystem
6. `draft_buzz.py` (static methods + `ProspectParser`) — Scraping orchestration
7. `mcmillen.py` — Small module, quick to cover
