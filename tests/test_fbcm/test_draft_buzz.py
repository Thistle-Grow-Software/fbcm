"""Tests for fbcm.draft_buzz — static helpers and ProspectParser orchestration."""

import pytest
from bs4 import BeautifulSoup

from fbcm.draft_buzz import PageFetcher, ProspectParser
from fbcm.models import Comparison


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
            <tr><td>Patrick Mahomes - Kansas City 92%</td></tr>
            <tr><td>Josh Allen - Buffalo 85%</td></tr>
          </tbody>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        result = parser.parse_comparisons(table=table)

        assert len(result) == 2
        assert isinstance(result[0], Comparison)
        assert result[0].name == "Patrick Mahomes"
        assert result[0].school == "Kansas City"
        assert result[0].similarity == 92
        assert result[1].name == "Josh Allen"
        assert result[1].similarity == 85

    def test_single_comparison(self, parser):
        html = """
        <table class="starRatingTable">
          <th>Comparisons</th>
          <tbody>
            <tr><td>Lamar Jackson - Baltimore 78%</td></tr>
          </tbody>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        result = parser.parse_comparisons(table=table)

        assert len(result) == 1
        assert result[0].name == "Lamar Jackson"


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
