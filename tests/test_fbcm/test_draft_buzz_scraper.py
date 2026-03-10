"""Tests for DraftBuzzScraper and ProspectParser orchestration in fbcm.draft_buzz."""

from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from fbcm.draft_buzz import DraftBuzzScraper, ProspectParser
from fbcm.models import (
    BasicInfo,
    Comparison,
    PassingSkills,
    PassingStats,
    ProspectDataSoup,
    RatingsAndRankings,
    ScoutingReport,
)


def _make_prospect_data(**overrides):
    """Helper to create a ProspectDataSoup with sensible defaults."""
    defaults = {
        "basic_info": BasicInfo(
            first_name="Cam",
            last_name="Ward",
            full_name="Cam Ward",
            position="QB",
            college="Miami",
            photo_url="https://example.com/photo.png",
        ),
        "ratings": RatingsAndRankings(
            overall_rating=92.5,
            draft_projection="Top 5",
            overall_rank=2,
            position_rank="1",
            avg_overall_rank=3.0,
            avg_position_rank=1.5,
        ),
        "skills": PassingSkills(release_speed=88, short_passing=90),
        "comparisons": [
            Comparison(name="Patrick Mahomes", school="Texas", similarity=92)
        ],
        "stats": PassingStats(cmp=280, att=420, yds=3800),
        "scouting_report": ScoutingReport(
            bio="Elite prospect",
            strengths=["Arm strength", "Accuracy"],
            weaknesses=["Footwork"],
            summary="High upside quarterback",
        ),
    }
    defaults.update(overrides)
    return ProspectDataSoup(**defaults)


class TestDraftBuzzScraperInit:
    def test_uses_provided_fetcher(self):
        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        scraper = DraftBuzzScraper(playwright=mock_pw, fetcher=mock_fetcher)
        assert scraper.fetcher is mock_fetcher

    def test_creates_default_fetcher_when_none_provided(self):
        mock_pw = MagicMock()
        with patch("fbcm.draft_buzz.PageFetcher") as mock_pf_cls:
            mock_pf_cls.return_value = MagicMock()
            scraper = DraftBuzzScraper(playwright=mock_pw)
            mock_pf_cls.assert_called_once()
            assert scraper.fetcher is mock_pf_cls.return_value

    def test_initial_state(self):
        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        scraper = DraftBuzzScraper(playwright=mock_pw, fetcher=mock_fetcher)
        assert scraper.current_prospect_data is None
        assert scraper.parser is None
        assert len(scraper.position_rankings_used) == 0


class TestDraftBuzzScraperScrapeFromUrl:
    @pytest.fixture
    def scraper(self):
        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        return DraftBuzzScraper(playwright=mock_pw, fetcher=mock_fetcher)

    def test_scrape_from_url_returns_prospect_data(self, scraper):
        # Set up the mock fetcher to return a minimal BeautifulSoup
        profile_soup = BeautifulSoup(
            """<html><body>
            <table class="starRatingTable">
              <tr><th>Overall Rating</th><td>92.5</td></tr>
            </table>
            </body></html>""",
            "html.parser",
        )
        stats_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        scraper.fetcher.fetch_soup.side_effect = [profile_soup, stats_soup]

        with (
            patch.object(ProspectParser, "parse") as mock_parse,
            patch.object(ProspectParser, "parse_stats") as mock_parse_stats,
        ):
            mock_data = _make_prospect_data()
            mock_parse.return_value = mock_data
            mock_parse_stats.return_value = PassingStats(cmp=280)

            result = scraper.scrape_from_url("/players/cam-ward", "QB")

            assert result is mock_data
            assert scraper.current_prospect_data is mock_data
            assert result.stats == PassingStats(cmp=280)

    def test_scrape_from_url_builds_correct_urls(self, scraper):
        soup = BeautifulSoup(
            """<html><body>
            <table class="starRatingTable">
              <tr><th>Rating</th><td>90</td></tr>
            </table>
            </body></html>""",
            "html.parser",
        )
        scraper.fetcher.fetch_soup.return_value = soup

        with (
            patch.object(ProspectParser, "parse") as mock_parse,
            patch.object(ProspectParser, "parse_stats") as mock_parse_stats,
        ):
            mock_parse.return_value = _make_prospect_data()
            mock_parse_stats.return_value = None

            scraper.scrape_from_url("/players/cam-ward", "QB")

            calls = scraper.fetcher.fetch_soup.call_args_list
            assert "https://www.nfldraftbuzz.com/players/cam-ward" in str(calls[0])
            assert "https://www.nfldraftbuzz.com/players/stats/cam-ward" in str(
                calls[1]
            )

    def test_scrape_resets_current_prospect_data(self, scraper):
        scraper.current_prospect_data = _make_prospect_data()

        soup = BeautifulSoup(
            """<html><body>
            <table class="starRatingTable">
              <tr><th>Rating</th><td>90</td></tr>
            </table>
            </body></html>""",
            "html.parser",
        )
        scraper.fetcher.fetch_soup.return_value = soup

        with (
            patch.object(ProspectParser, "parse") as mock_parse,
            patch.object(ProspectParser, "parse_stats") as mock_parse_stats,
        ):
            new_data = _make_prospect_data(
                basic_info=BasicInfo(full_name="Shedeur Sanders", position="QB")
            )
            mock_parse.return_value = new_data
            mock_parse_stats.return_value = None

            result = scraper.scrape_from_url("/players/shedeur-sanders", "QB")
            assert scraper.current_prospect_data is result


class TestDraftBuzzScraperSavePlayerPhoto:
    def test_save_player_photo_to_disk(self, tmp_path):
        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        scraper = DraftBuzzScraper(
            playwright=mock_pw,
            fetcher=mock_fetcher,
            profile_root_dir=tmp_path,
        )

        photos_dir = tmp_path / "player_photos"
        photos_dir.mkdir()

        scraper.current_prospect_data = _make_prospect_data()

        with patch("fbcm.draft_buzz.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_bytes"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            scraper.save_player_photo_to_disk()

            mock_get.assert_called_once_with("https://example.com/photo.png")
            expected_file = photos_dir / "Cam Ward.png"
            assert expected_file.exists()
            assert expected_file.read_bytes() == b"fake_image_bytes"

    def test_save_player_photo_raises_on_http_error(self, tmp_path):
        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        scraper = DraftBuzzScraper(
            playwright=mock_pw,
            fetcher=mock_fetcher,
            profile_root_dir=tmp_path,
        )
        scraper.current_prospect_data = _make_prospect_data()

        with patch("fbcm.draft_buzz.requests.get") as mock_get:
            from requests.exceptions import HTTPError

            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                scraper.save_player_photo_to_disk()


class TestDraftBuzzScraperPrintSummary:
    def test_print_summary_logs_prospect_info(self, caplog):
        import logging

        mock_pw = MagicMock()
        mock_fetcher = MagicMock()
        scraper = DraftBuzzScraper(playwright=mock_pw, fetcher=mock_fetcher)

        data = _make_prospect_data()

        with caplog.at_level(logging.INFO, logger="fbcm.draft_buzz"):
            scraper.print_summary(data)

        assert "Cam Ward" in caplog.text
        assert "QB" in caplog.text
        assert "Miami" in caplog.text
        assert "92.5" in caplog.text
        assert "Top 5" in caplog.text
        assert "2 items" in caplog.text  # strengths count
        assert "1 items" in caplog.text  # weaknesses count


class TestProspectParserParseOrchestration:
    def test_parse_delegates_to_sub_parsers(self):
        html = """<html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92</td></tr>
        </table>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")

        with (
            patch.object(parser._basic_info_parser, "parse") as mock_bi,
            patch.object(parser._rating_extractor, "parse") as mock_re,
            patch.object(parser._skills_parser, "parse") as mock_sp,
            patch.object(parser._scouting_report_parser, "parse") as mock_sr,
        ):
            mock_bi.return_value = BasicInfo(full_name="Test Player", position="QB")
            mock_re.return_value = RatingsAndRankings(overall_rating=92)
            mock_sp.return_value = PassingSkills(release_speed=88)
            mock_sr.return_value = ScoutingReport(bio="Bio text")

            result = parser.parse()

            mock_bi.assert_called_once()
            mock_re.assert_called_once()
            mock_sp.assert_called_once()
            mock_sr.assert_called_once()

            assert isinstance(result, ProspectDataSoup)
            assert result.basic_info.full_name == "Test Player"
            assert result.ratings.overall_rating == 92
            assert result.stats is None  # parse() doesn't fetch stats

    def test_parse_stats_delegates_to_stats_parser(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        parser = ProspectParser(soup=soup, position="QB")

        stats_soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        with patch("fbcm.draft_buzz.StatsParser") as mock_sp_cls:
            mock_instance = MagicMock()
            mock_instance.parse.return_value = PassingStats(cmp=300)
            mock_sp_cls.return_value = mock_instance

            result = parser.parse_stats(stats_soup)

            mock_sp_cls.assert_called_once_with(soup=stats_soup, position="QB")
            assert result == PassingStats(cmp=300)
