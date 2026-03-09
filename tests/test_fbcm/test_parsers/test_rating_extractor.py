import pytest
from bs4 import BeautifulSoup

from fbcm.parsers import RatingExtractor

from .conftest import RANKING_BOX_HTML, RATINGS_TABLE_HTML


def _build_full_html():
    return f"<html><body>{RATINGS_TABLE_HTML}{RANKING_BOX_HTML}</body></html>"


@pytest.fixture
def rating_extractor():
    soup = BeautifulSoup(_build_full_html(), "html.parser")
    return RatingExtractor(soup=soup)


@pytest.fixture
def ratings_table():
    soup = BeautifulSoup(_build_full_html(), "html.parser")
    return soup.find("table", class_="starRatingTable")


class TestRatingExtractor:
    def test_parse_overall_rating(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.overall_rating == 92.5

    def test_parse_opposition_rating(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.opposition_rating == 78

    def test_parse_draft_projection(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.draft_projection == "1st Round"

    def test_parse_overall_rank(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.overall_rank == "3"

    def test_parse_position_rank(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.position_rank == "1"

    def test_parse_average_ranks(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.avg_overall_rank == 5.2
        assert result.avg_position_rank == 2.1

    def test_parse_espn_rating(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.espn == 95.0

    def test_parse_rivals_rating(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.rivals == 5.8

    def test_parse_247_rating(self, rating_extractor, ratings_table):
        result = rating_extractor.parse(table=ratings_table)
        assert result.rtg_247 == 0.99

    def test_rating_checks_raises_on_bad_label(self, make_soup):
        html = """
        <html><body>
        <table class="starRatingTable">
          <tr><th>Bad Label</th></tr>
        </table>
        <div class="rankingBox">
          <div class="rankVal">1</div>
          <div class="rankVal">2</div>
        </div>
        </body></html>
        """
        soup = make_soup(html)
        extractor = RatingExtractor(soup=soup)
        table = soup.find("table")
        with pytest.raises(ValueError, match="Unexpected label"):
            extractor.parse(table=table)

    def test_missing_outlet_ratings_returns_none(self, make_soup):
        html = f"""
        <html><body>
        <table class="starRatingTable">
          <tr><th>Overall Rating</th><td><span>80 / 100</span></td></tr>
          <tr><td>filler</td></tr>
          <tr><td><div class="meter" title="Opposition Rating: 50%"></div></td></tr>
          <tr>
            <td>
              <span>Draft Projection</span><span>2nd Round</span>
              <span>Overall Rank</span><span>15</span>
              <span>Position Rank</span><span>5</span>
            </td>
          </tr>
        </table>
        {RANKING_BOX_HTML}
        </body></html>
        """
        soup = make_soup(html)
        extractor = RatingExtractor(soup=soup)
        table = soup.find("table")
        result = extractor.parse(table=table)
        assert result.espn is None
        assert result.rivals is None
        assert result.rtg_247 is None
