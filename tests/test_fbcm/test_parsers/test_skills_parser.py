import pytest
from bs4 import BeautifulSoup

from fbcm.models import (
    DefensiveBackSkills,
    DefensiveLinemanSkills,
    LinebackerSkills,
    OffensiveLinemanSkills,
    PassCatcherSkills,
    PassingSkills,
    RunningBackSkills,
)
from fbcm.parsers import SkillsParser

from .conftest import RATINGS_TABLE_HTML


@pytest.fixture
def qb_ratings_table():
    soup = BeautifulSoup(RATINGS_TABLE_HTML, "html.parser")
    return soup.find("table", class_="starRatingTable")


class TestSkillsParser:
    def test_parse_qb_skills(self, qb_ratings_table):
        parser = SkillsParser(position="QB")
        result = parser.parse(table=qb_ratings_table)

        assert isinstance(result, PassingSkills)
        assert result.release_speed == 88
        assert result.short_passing == 90
        assert result.medium_passing == 85
        assert result.long_passing == 82
        assert result.rush_scramble == 75

    def test_parse_rb_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>Rushing: 90/100</td></tr>
          <tr><td>Break Tackles: 85/100</td></tr>
          <tr><td>Receiving Hands: 78/100</td></tr>
          <tr><td>Pass Blocking: 65/100</td></tr>
          <tr><td>Run Blocking: 70/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="RB")
        result = parser.parse(table=table)

        assert isinstance(result, RunningBackSkills)
        assert result.rushing == 90
        assert result.break_tackles == 85

    def test_parse_wr_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>QB Rating When Targeted: 120.5/158.3</td></tr>
          <tr><td>Hands: 92/100</td></tr>
          <tr><td>Short Receiving: 88/100</td></tr>
          <tr><td>Intermediate Routes: 85/100</td></tr>
          <tr><td>Deep Threat: 90/100</td></tr>
          <tr><td>Blocking: 60/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="WR")
        result = parser.parse(table=table)

        assert isinstance(result, PassCatcherSkills)
        assert result.hands == 92

    def test_parse_ol_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>Pass Blocking: 88/100</td></tr>
          <tr><td>Run Blocking: 90/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="OL")
        result = parser.parse(table=table)

        assert isinstance(result, OffensiveLinemanSkills)
        assert result.pass_blocking == 88
        assert result.run_blocking == 90

    def test_parse_dl_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>QB Rating When Targeted: 75.2/158.3</td></tr>
          <tr><td>Tackling: 85/100</td></tr>
          <tr><td>Pass Rush: 90/100</td></tr>
          <tr><td>Run Defense: 88/100</td></tr>
          <tr><td>Coverage: 60/100</td></tr>
          <tr><td>Zone: 55/100</td></tr>
          <tr><td>Man Press: 50/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="DL")
        result = parser.parse(table=table)

        assert isinstance(result, DefensiveLinemanSkills)
        assert result.pass_rush == 90

    def test_parse_lb_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>QB Rating When Targeted: 80.0/158.3</td></tr>
          <tr><td>Tackling: 90/100</td></tr>
          <tr><td>Pass Rush: 75/100</td></tr>
          <tr><td>Run Defense: 92/100</td></tr>
          <tr><td>Coverage: 70/100</td></tr>
          <tr><td>Zone: 72/100</td></tr>
          <tr><td>Man Press: 65/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="LB")
        result = parser.parse(table=table)

        assert isinstance(result, LinebackerSkills)
        assert result.tackling == 90

    def test_parse_db_skills(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>QB Rating When Targeted: 55.0/158.3</td></tr>
          <tr><td>Tackling: 78/100</td></tr>
          <tr><td>Run Defense: 72/100</td></tr>
          <tr><td>Coverage: 95/100</td></tr>
          <tr><td>Zone: 90/100</td></tr>
          <tr><td>Man Press: 88/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="DB")
        result = parser.parse(table=table)

        assert isinstance(result, DefensiveBackSkills)
        assert result.coverage == 95

    def test_parse_unknown_position_raises(self, make_soup):
        html = """
        <table>
          <tr></tr><tr></tr><tr></tr><tr></tr>
          <tr><td>Some Skill: 80/100</td></tr>
          <tr><td>Draft Projection - stop here</td></tr>
        </table>
        """
        soup = make_soup(html)
        table = soup.find("table")
        parser = SkillsParser(position="K")
        with pytest.raises(ValueError, match="Could not find skill ratings"):
            parser.parse(table=table)
