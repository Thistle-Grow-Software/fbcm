"""Tests for draft CLI commands that consume the GriddyDraftBuzz SDK."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from griddy.draftbuzz.errors import ParsingError
from griddy.draftbuzz.models import (
    BasicInfo,
    PositionRankings,
    ProspectProfile,
    RankedProspect,
)

from fbcm.fbcm import _download_player_photo, cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_prospect():
    return ProspectProfile(
        basic_info=BasicInfo(
            first_name="Cam",
            last_name="Ward",
            full_name="Cam Ward",
            position="QB",
            college="Miami",
            photo_url="https://example.com/photo.png",
        ),
    )


class TestExtractDraftProfiles:
    def test_fetches_prospect_via_sdk(self, runner, sample_prospect):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/cam-ward-qb-2025"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()

            with (
                patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls,
                patch("fbcm.fbcm._download_player_photo"),
            ):
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.prospects.get_prospect.return_value = sample_prospect

                result = runner.invoke(
                    cli,
                    [
                        "--config",
                        "nonexistent.yaml",
                        "extract-draft-profiles",
                        "--output-directory",
                        "output",
                        "--position",
                        "QB",
                        "--input-file",
                        "urls.json",
                    ],
                )

            assert result.exit_code == 0
            mock_sdk.prospects.get_prospect.assert_called_once_with(
                slug="players/cam-ward-qb-2025", position="QB"
            )

    def test_parsing_error_continues_to_next_prospect(self, runner, sample_prospect):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/bad-prospect", "/players/cam-ward-qb-2025"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()

            with (
                patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls,
                patch("fbcm.fbcm._download_player_photo"),
            ):
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.prospects.get_prospect.side_effect = [
                    ParsingError(message="Parse failed"),
                    sample_prospect,
                ]

                result = runner.invoke(
                    cli,
                    [
                        "--config",
                        "nonexistent.yaml",
                        "extract-draft-profiles",
                        "--output-directory",
                        "output",
                        "--position",
                        "QB",
                        "--input-file",
                        "urls.json",
                    ],
                )

            assert result.exit_code == 0
            assert mock_sdk.prospects.get_prospect.call_count == 2


class TestUpdateDraftProspectUrls:
    def test_paginates_through_rankings(self, runner):
        page1 = PositionRankings(
            position="QB",
            year=2026,
            page=1,
            entries=[
                RankedProspect(name="Player 1", href="/players/player-1-qb-2026"),
                RankedProspect(name="Player 2", href="/players/player-2-qb-2026"),
            ],
        )
        page_empty = PositionRankings(entries=[])

        with runner.isolated_filesystem():
            with patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls:
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.rankings.get_position_rankings.side_effect = [
                    page1,
                    page_empty,
                ] + [page_empty] * 8

                result = runner.invoke(
                    cli,
                    ["--config", "nonexistent.yaml", "update-draft-prospect-urls"],
                )

            assert result.exit_code == 0
            urls = json.loads(Path("prospect_urls.json").read_text())
            assert len(urls["QB"]) == 2
            assert urls["QB"][0] == "/players/player-1-qb-2026"

    def test_handles_exception_per_position(self, runner):
        with runner.isolated_filesystem():
            with patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls:
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.rankings.get_position_rankings.side_effect = ConnectionError(
                    "Network error"
                )

                result = runner.invoke(
                    cli,
                    ["--config", "nonexistent.yaml", "update-draft-prospect-urls"],
                )

            assert result.exit_code == 0


class TestDownloadPlayerPhoto:
    def test_downloads_and_saves_photo(self, tmp_path):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake image data"
            mock_get.return_value = mock_response

            _download_player_photo(
                photo_url="https://example.com/photo.png",
                full_name="Cam Ward",
                output_dir=tmp_path,
            )

        photo_path = tmp_path / "player_photos" / "Cam Ward.png"
        assert photo_path.exists()
        assert photo_path.read_bytes() == b"fake image data"
