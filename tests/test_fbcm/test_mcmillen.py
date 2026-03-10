"""Tests for fbcm.mcmillen — web scraping link extraction."""

from unittest.mock import MagicMock, patch

from fbcm.mcmillen import extract_links_for_year


class TestExtractLinksForYear:
    @patch("fbcm.mcmillen.requests")
    def test_extracts_matching_hrefs(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <a href="2024_Steelers_Game1.mp4">Game 1</a>
        <a href="2024_Steelers_Game2.mp4">Game 2</a>
        <a href="other_link.html">Other</a>
        </body></html>
        """
        mock_requests.get.return_value = mock_response

        result = extract_links_for_year(2024)

        assert len(result) == 2
        assert "2024_Steelers_Game1.mp4" in result
        assert "2024_Steelers_Game2.mp4" in result

    @patch("fbcm.mcmillen.requests")
    def test_ignores_non_matching_hrefs(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <a href="2023_Steelers_Game1.mp4">Wrong Year</a>
        <a href="random_page.html">Random</a>
        </body></html>
        """
        mock_requests.get.return_value = mock_response

        result = extract_links_for_year(2024)

        assert len(result) == 0

    @patch("fbcm.mcmillen.requests")
    def test_returns_set(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <a href="2024_Steelers_Game1.mp4">Game 1</a>
        <a href="2024_Steelers_Game1.mp4">Duplicate</a>
        </body></html>
        """
        mock_requests.get.return_value = mock_response

        result = extract_links_for_year(2024)

        assert isinstance(result, set)
        assert len(result) == 1

    @patch("fbcm.mcmillen.requests")
    def test_skips_empty_hrefs(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <a href="">Empty</a>
        <a href="2024_Steelers_Game1.mp4">Game 1</a>
        </body></html>
        """
        mock_requests.get.return_value = mock_response

        result = extract_links_for_year(2024)

        assert len(result) == 1

    @patch("fbcm.mcmillen.requests")
    def test_strips_whitespace(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <a href="  2024_Steelers_Game1.mp4  ">Game 1</a>
        </body></html>
        """
        mock_requests.get.return_value = mock_response

        result = extract_links_for_year(2024)

        assert len(result) == 1
