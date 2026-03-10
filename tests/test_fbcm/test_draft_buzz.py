"""Tests for fbcm.draft_buzz — static helpers, ProspectParser orchestration, and DraftBuzzScraper."""

from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from fbcm.draft_buzz import DraftBuzzScraper, PageFetcher, ProspectParser
from fbcm.models import (
    BasicInfo,
    Comparison,
    PassingSkills,
    PassingStats,
    ProspectDataSoup,
    RatingsAndRankings,
    ScoutingReport,
)

# ─── PageFetcher Static Methods ─────────────────────────────────────────────


class TestPageFetcherMakeAbsoluteUrl:
    def test_protocol_relative_url(self):
        result = PageFetcher._make_absolute_url("//cdn.example.com/img.png")
        assert result == "https://cdn.example.com/img.png"

    def test_root_relative_url(self):
        result = PageFetcher._make_absolute_url(
            "/images/player.png", "https://www.nfldraftbuzz.com"
        )
        assert result == "https://www.nfldraftbuzz.com/images/player.png"

    def test_absolute_url_unchanged(self):
        url = "https://example.com/img.png"
        result = PageFetcher._make_absolute_url(url)
        assert result == url

    def test_relative_with_no_base(self):
        result = PageFetcher._make_absolute_url("img.png")
        assert result == "img.png"


class TestPageFetcherGetImageType:
    def test_png(self):
        assert PageFetcher._get_image_type("image/png") == "png"

    def test_gif(self):
        assert PageFetcher._get_image_type("image/gif") == "gif"

    def test_webp(self):
        assert PageFetcher._get_image_type("image/webp") == "webp"

    def test_jpeg_default(self):
        assert PageFetcher._get_image_type("image/jpeg") == "jpeg"

    def test_unknown_defaults_to_jpeg(self):
        assert PageFetcher._get_image_type("application/octet-stream") == "jpeg"

    def test_empty_defaults_to_jpeg(self):
        assert PageFetcher._get_image_type("") == "jpeg"


# ─── ProspectParser ──────────────────────────────────────────────────────────


class TestProspectParserParseComparisons:
    @pytest.fixture
    def parser(self):
        # Minimal soup — the comparisons table is passed directly
        soup = BeautifulSoup("<html></html>", "html.parser")
        return ProspectParser(soup=soup, position="QB")

    def test_parses_comparisons(self, parser):
        html = """
        <table class="starRatingTable">
          <th>Comparisons</th>
          <tbody>
            <tr><td>Patrick Mahomes - Texas 92%</td></tr>
            <tr><td>Josh Allen - Wyoming 85%</td></tr>
          </tbody>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        result = parser.parse_comparisons(table=table)

        assert len(result) == 2
        assert isinstance(result[0], Comparison)
        assert result[0].name == "Patrick Mahomes"
        assert result[0].school == "Texas"
        assert result[0].similarity == 92
        assert result[1].name == "Josh Allen"
        assert result[1].similarity == 85

    def test_single_comparison(self, parser):
        html = """
        <table class="starRatingTable">
          <th>Comparisons</th>
          <tbody>
            <tr><td>Lamar Jackson - Louisville 78%</td></tr>
          </tbody>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        result = parser.parse_comparisons(table=table)

        assert len(result) == 1
        assert result[0].name == "Lamar Jackson"
        assert result[0].school == "Louisville"


class TestProspectParserExtractRatingsCompsTables:
    def test_separates_ratings_and_comparisons(self):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92.5</td></tr>
        </table>
        <table class="starRatingTable">
          <th>Comparisons</th>
          <tbody><tr><td>Test Player - Team 90%</td></tr></tbody>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")
        ratings, comps = parser._extract_ratings_comps_tables()

        assert ratings is not None
        assert comps is not None

    def test_no_comparisons_table(self):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92.5</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")
        ratings, comps = parser._extract_ratings_comps_tables()

        assert ratings is not None
        assert comps is None

    def test_excludes_measurables_table(self):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Measurables</th><td>data</td></tr>
        </table>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92.5</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")
        ratings, comps = parser._extract_ratings_comps_tables()

        assert ratings is not None
        # The measurables table should be filtered out
        assert "Overall Rating" in ratings.get_text()


class TestProspectParserParse:
    """Tests for the full parse() orchestration method."""

    def test_parse_returns_prospect_data_soup(self):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92.5</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")

        with (
            patch.object(parser._basic_info_parser, "parse") as mock_basic,
            patch.object(parser._rating_extractor, "parse") as mock_ratings,
            patch.object(parser._skills_parser, "parse") as mock_skills,
            patch.object(parser._scouting_report_parser, "parse") as mock_scout,
        ):
            mock_basic.return_value = BasicInfo(
                first_name="Cam", last_name="Ward", position="QB"
            )
            mock_ratings.return_value = RatingsAndRankings(overall_rating=92.5)
            mock_skills.return_value = PassingSkills(release_speed=88)
            mock_scout.return_value = ScoutingReport(bio="Test bio")

            result = parser.parse()

        assert isinstance(result, ProspectDataSoup)
        assert result.basic_info.first_name == "Cam"
        assert result.ratings.overall_rating == 92.5
        assert result.skills.release_speed == 88
        assert result.scouting_report.bio == "Test bio"
        assert result.stats is None

    def test_parse_with_comparisons_table(self):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td>92.5</td></tr>
        </table>
        <table class="starRatingTable">
          <th>Comparisons</th>
          <tbody>
            <tr><td>Patrick Mahomes - Texas 92%</td></tr>
          </tbody>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = ProspectParser(soup=soup, position="QB")

        with (
            patch.object(parser._basic_info_parser, "parse") as mock_basic,
            patch.object(parser._rating_extractor, "parse") as mock_ratings,
            patch.object(parser._skills_parser, "parse") as mock_skills,
            patch.object(parser._scouting_report_parser, "parse") as mock_scout,
        ):
            mock_basic.return_value = BasicInfo(position="QB")
            mock_ratings.return_value = RatingsAndRankings()
            mock_skills.return_value = PassingSkills()
            mock_scout.return_value = ScoutingReport()

            result = parser.parse()

        assert result.comparisons is not None
        assert len(result.comparisons) == 1
        assert result.comparisons[0].name == "Patrick Mahomes"


class TestProspectParserParseStats:
    def test_parse_stats_delegates_to_stats_parser(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        parser = ProspectParser(soup=soup, position="QB")

        stats_soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        with patch("fbcm.draft_buzz.StatsParser") as mock_stats_parser_cls:
            mock_instance = MagicMock()
            mock_instance.parse.return_value = PassingStats(cmp=280, att=420)
            mock_stats_parser_cls.return_value = mock_instance

            result = parser.parse_stats(stats_soup)

        mock_stats_parser_cls.assert_called_once_with(soup=stats_soup, position="QB")
        assert isinstance(result, PassingStats)
        assert result.cmp == 280

    def test_parse_stats_returns_none_when_no_stats(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        parser = ProspectParser(soup=soup, position="OL")
        stats_soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        with patch("fbcm.draft_buzz.StatsParser") as mock_cls:
            mock_cls.return_value.parse.return_value = None
            result = parser.parse_stats(stats_soup)

        assert result is None


# ─── DraftBuzzScraper ────────────────────────────────────────────────────────


class TestDraftBuzzScraper:
    @pytest.fixture
    def mock_playwright(self):
        return MagicMock()

    @pytest.fixture
    def mock_fetcher(self):
        return MagicMock(spec=PageFetcher)

    @pytest.fixture
    def scraper(self, mock_playwright, mock_fetcher):
        return DraftBuzzScraper(
            playwright=mock_playwright,
            fetcher=mock_fetcher,
            headless=True,
        )

    def test_init_sets_defaults(self, scraper, mock_fetcher):
        assert scraper.fetcher is mock_fetcher
        assert scraper.parser is None
        assert scraper.current_prospect_data is None
        assert isinstance(scraper.position_rankings_used, defaultdict)

    def test_scrape_from_url_builds_correct_urls(self, scraper, mock_fetcher):
        base_soup = BeautifulSoup(
            """<html><body>
            <table class="starRatingTable">
              <tr><th>Rating</th><td>90</td></tr>
            </table>
            </body></html>""",
            "html.parser",
        )
        stats_soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        mock_fetcher.fetch_soup.side_effect = [base_soup, stats_soup]

        with (
            patch.object(ProspectParser, "parse") as mock_parse,
            patch.object(ProspectParser, "parse_stats") as mock_parse_stats,
        ):
            mock_data = ProspectDataSoup(
                basic_info=BasicInfo(position="QB"),
                ratings=RatingsAndRankings(overall_rating=90),
            )
            mock_parse.return_value = mock_data
            mock_parse_stats.return_value = PassingStats(cmp=280)

            scraper.scrape_from_url("/players/cam-ward", "QB")

        # Verify the correct URLs were constructed
        calls = mock_fetcher.fetch_soup.call_args_list
        assert calls[0].kwargs["url"] == "https://www.nfldraftbuzz.com/players/cam-ward"
        assert (
            calls[1].kwargs["url"]
            == "https://www.nfldraftbuzz.com/players/stats/cam-ward"
        )
        assert scraper.current_prospect_data is not None

    def test_save_player_photo_to_disk(self, scraper, tmp_path):
        scraper.profile_root_dir = tmp_path
        scraper.current_prospect_data = ProspectDataSoup(
            basic_info=BasicInfo(
                full_name="Cam Ward",
                photo_url="https://example.com/cam.png",
            )
        )

        (tmp_path / "player_photos").mkdir()

        with patch("fbcm.draft_buzz.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_bytes"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            scraper.save_player_photo_to_disk()

        expected_path = tmp_path / "player_photos" / "Cam Ward.png"
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"fake_image_bytes"

    def test_save_player_photo_raises_on_http_error(self, scraper, tmp_path):
        scraper.profile_root_dir = tmp_path
        scraper.current_prospect_data = ProspectDataSoup(
            basic_info=BasicInfo(
                full_name="Test Player",
                photo_url="https://example.com/missing.png",
            )
        )

        with patch("fbcm.draft_buzz.requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = Exception("404")
            with pytest.raises(Exception, match="404"):
                scraper.save_player_photo_to_disk()

    def test_print_summary_logs_info(self, scraper, caplog):
        """print_summary should log key prospect details."""
        data = ProspectDataSoup(
            basic_info=BasicInfo(
                full_name="Cam Ward",
                position="QB",
                college="Miami",
            ),
            ratings=RatingsAndRankings(
                overall_rating=92.5,
                draft_projection="Top 5",
            ),
            scouting_report=ScoutingReport(
                strengths=["Arm strength", "Accuracy"],
                weaknesses=["Footwork"],
            ),
        )

        import logging

        with caplog.at_level(logging.INFO):
            scraper.print_summary(data)

        log_text = caplog.text
        assert "Cam Ward" in log_text
        assert "QB" in log_text
        assert "Miami" in log_text
        assert "92.5" in log_text
        assert "Top 5" in log_text
        assert "2 items" in log_text  # strengths count
        assert "1 items" in log_text  # weaknesses count
