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

from fbcm.fbcm import _download_player_photo, cli, dump_currently_completed


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


def _invoke_extract(runner, extra_cli_args=None, **kwargs):
    """Helper to build common CLI invocation for extract-draft-profiles."""
    args = [
        "--config",
        "nonexistent.yaml",
        "extract-draft-profiles",
        "--output-directory",
        "output",
        "--position",
        "QB",
        "--input-file",
        "urls.json",
    ]
    if extra_cli_args:
        args.extend(extra_cli_args)
    return runner.invoke(cli, args, **kwargs)


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

                result = _invoke_extract(runner)

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

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            assert mock_sdk.prospects.get_prospect.call_count == 2

    def test_connection_error_continues_to_next_prospect(self, runner, sample_prospect):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/bad", "/players/good"]}
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
                    ConnectionError("Network down"),
                    sample_prospect,
                ]

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            assert mock_sdk.prospects.get_prospect.call_count == 2

    def test_skips_already_completed_profiles(self, runner, sample_prospect):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/already-done", "/players/new-one"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()
            Path("input_files/completed.json").write_text(
                json.dumps(["/players/already-done"])
            )

            with (
                patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls,
                patch("fbcm.fbcm._download_player_photo"),
            ):
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.prospects.get_prospect.return_value = sample_prospect

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            assert "Already completed" in result.output
            mock_sdk.prospects.get_prospect.assert_called_once()

    def test_skips_photo_download_when_no_photo_url(self, runner):
        prospect_no_photo = ProspectProfile(
            basic_info=BasicInfo(
                full_name="No Photo Guy",
                position="QB",
                college="Miami",
                photo_url=None,
            ),
        )
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/no-photo"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()

            with (
                patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls,
                patch("fbcm.fbcm._download_player_photo") as mock_download,
            ):
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.prospects.get_prospect.return_value = prospect_no_photo

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            mock_download.assert_not_called()

    def test_invalid_position_raises_bad_parameter(self, runner):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/someone"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()

            with patch("griddy.draftbuzz.GriddyDraftBuzz"):
                result = runner.invoke(
                    cli,
                    [
                        "--config",
                        "nonexistent.yaml",
                        "extract-draft-profiles",
                        "--output-directory",
                        "output",
                        "--position",
                        "K",
                        "--input-file",
                        "urls.json",
                    ],
                )

            assert result.exit_code != 0
            assert "K is not present" in result.output

    def test_unexpected_exception_dumps_progress_and_reraises(
        self, runner, sample_prospect
    ):
        with runner.isolated_filesystem():
            input_data = {"QB": ["/players/will-crash"]}
            Path("urls.json").write_text(json.dumps(input_data))
            Path("output").mkdir()
            Path("output_data").mkdir()
            Path("input_files").mkdir()

            with (
                patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls,
                patch("fbcm.fbcm.dump_currently_completed") as mock_dump,
            ):
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.prospects.get_prospect.side_effect = RuntimeError("crash")

                result = _invoke_extract(runner)

            assert result.exit_code != 0
            mock_dump.assert_called_once()

    def test_writes_output_json(self, runner, sample_prospect):
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

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            # dump_currently_completed writes output JSON
            output_files = list(Path("output_data").glob("*.json"))
            assert len(output_files) >= 1

    def test_serializes_prospect_with_model_dump(self, runner, sample_prospect):
        """Verify the output JSON uses SDK model_dump format."""
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

                result = _invoke_extract(runner)

            assert result.exit_code == 0
            # Read the output and verify it has the SDK model structure
            output_files = list(Path("output_data").glob("*.json"))
            data = json.loads(output_files[0].read_text())
            assert "Cam Ward" in data
            assert "basic_info" in data["Cam Ward"]


class TestUpdateDraftProspectUrls:
    def _single_page(self, **kwargs):
        """PositionRankings with total_pages=1 (no further pages)."""
        defaults = dict(position="QB", year=2026, page=1, total_pages=1, entries=[])
        defaults.update(kwargs)
        return PositionRankings(**defaults)

    def test_paginates_through_rankings(self, runner):
        page1 = PositionRankings(
            position="QB",
            year=2026,
            page=1,
            total_pages=2,
            entries=[
                RankedProspect(name="Player 1", href="/players/player-1-qb-2026"),
            ],
        )
        page2 = PositionRankings(
            position="QB",
            year=2026,
            page=2,
            total_pages=2,
            entries=[
                RankedProspect(name="Player 2", href="/players/player-2-qb-2026"),
            ],
        )
        empty = self._single_page()

        with runner.isolated_filesystem():
            with patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls:
                mock_sdk = mock_sdk_cls.return_value
                # QB: page1 then page2; remaining 8 positions: single empty page each
                mock_sdk.rankings.get_position_rankings.side_effect = [
                    page1,
                    page2,
                ] + [empty] * 8

                result = runner.invoke(
                    cli,
                    ["--config", "nonexistent.yaml", "update-draft-prospect-urls"],
                )

            assert result.exit_code == 0
            urls = json.loads(Path("prospect_urls.json").read_text())
            assert len(urls["QB"]) == 2
            assert urls["QB"][0] == "/players/player-1-qb-2026"
            assert urls["QB"][1] == "/players/player-2-qb-2026"

    def test_handles_exception_on_first_page(self, runner):
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

    def test_skips_entries_with_none_href(self, runner):
        page = PositionRankings(
            position="QB",
            year=2026,
            page=1,
            total_pages=1,
            entries=[
                RankedProspect(name="Player 1", href="/players/p1"),
                RankedProspect(name="Player 2", href=None),
                RankedProspect(name="Player 3", href="/players/p3"),
            ],
        )
        empty = self._single_page()

        with runner.isolated_filesystem():
            with patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls:
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.rankings.get_position_rankings.side_effect = [page] + [
                    empty
                ] * 8

                result = runner.invoke(
                    cli,
                    ["--config", "nonexistent.yaml", "update-draft-prospect-urls"],
                )

            assert result.exit_code == 0
            urls = json.loads(Path("prospect_urls.json").read_text())
            assert len(urls["QB"]) == 2
            assert "/players/p1" in urls["QB"]
            assert "/players/p3" in urls["QB"]

    def test_custom_year_argument(self, runner):
        page_empty = self._single_page()

        with runner.isolated_filesystem():
            with patch("griddy.draftbuzz.GriddyDraftBuzz") as mock_sdk_cls:
                mock_sdk = mock_sdk_cls.return_value
                mock_sdk.rankings.get_position_rankings.return_value = page_empty

                result = runner.invoke(
                    cli,
                    [
                        "--config",
                        "nonexistent.yaml",
                        "update-draft-prospect-urls",
                        "--year",
                        "2027",
                    ],
                )

            assert result.exit_code == 0
            call_kwargs = mock_sdk.rankings.get_position_rankings.call_args_list[
                0
            ].kwargs
            assert call_kwargs["year"] == 2027


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

    def test_creates_player_photos_directory(self, tmp_path):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"data"
            mock_get.return_value = mock_response

            _download_player_photo(
                photo_url="https://example.com/photo.png",
                full_name="Test Player",
                output_dir=tmp_path,
            )

        assert (tmp_path / "player_photos").is_dir()

    def test_raises_on_http_error(self, tmp_path):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("404")
            mock_get.return_value = mock_response

            with pytest.raises(Exception, match="404"):
                _download_player_photo(
                    photo_url="https://example.com/missing.png",
                    full_name="Missing",
                    output_dir=tmp_path,
                )


class TestDumpCurrentlyCompleted:
    def test_writes_position_data_and_completed_list(self, tmp_path):
        import os

        output_data = tmp_path / "output_data"
        output_data.mkdir()
        input_files = tmp_path / "input_files"
        input_files.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            dump_currently_completed(
                position="QB",
                data={"Cam Ward": {"basic_info": {"position": "QB"}}},
                completed_list=["/players/cam-ward"],
            )
        finally:
            os.chdir(original_cwd)

        output_files = list(output_data.glob("QB_redo_*.json"))
        assert len(output_files) == 1
        data = json.loads(output_files[0].read_text())
        assert "Cam Ward" in data

        completed = json.loads((input_files / "completed.json").read_text())
        assert "/players/cam-ward" in completed
