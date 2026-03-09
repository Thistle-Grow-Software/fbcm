import pytest

from fbcm.models import (
    DefenseStats,
    OffenseSkillPlayerStats,
    PassingStats,
)
from fbcm.parsers import StatsParser

from .conftest import DEFENSE_STATS_HTML, QB_STATS_HTML, RB_STATS_HTML


class TestStatsParserQB:
    def test_parse_qb_stats(self, make_soup):
        soup = make_soup(QB_STATS_HTML)
        parser = StatsParser(soup=soup, position="QB")
        result = parser.parse()

        assert isinstance(result, PassingStats)
        assert result.cmp == 280
        assert result.att == 420
        assert result.cmp_pct == 66.7
        assert result.yds == 3800
        assert result.td == 32
        assert result.ints == 8
        assert result.sack == 15
        assert result.qb_rtg == 155.2

    def test_parse_qb_games_and_snaps(self, make_soup):
        soup = make_soup(QB_STATS_HTML)
        parser = StatsParser(soup=soup, position="QB")
        result = parser.parse()

        assert result.games_played == 40
        assert result.snap_count == 2100


class TestStatsParserDefense:
    def test_parse_defense_stats(self, make_soup):
        soup = make_soup(DEFENSE_STATS_HTML)
        parser = StatsParser(soup=soup, position="DL")
        result = parser.parse()

        assert isinstance(result, DefenseStats)
        assert result.tackle.total == 65
        assert result.tackle.solo == 42
        assert result.tackle.ff == 3
        assert result.tackle.sacks == 8.5
        assert result.interception.ints == 2
        assert result.interception.yds == 35
        assert result.interception.td == 1
        assert result.interception.pds == 10

    def test_parse_defense_games_and_snaps_not_on_top_level(self, make_soup):
        """games_played/snap_count are extracted but not passed to DefenseStats constructor."""
        soup = make_soup(DEFENSE_STATS_HTML)
        parser = StatsParser(soup=soup, position="LB")
        result = parser.parse()

        # DefenseStats doesn't receive gp_and_snaps directly (pre-existing behavior)
        assert result.games_played is None
        assert result.snap_count is None

    @pytest.mark.parametrize("position", ["DL", "EDGE", "LB", "DB"])
    def test_defense_positions_all_parse(self, make_soup, position):
        soup = make_soup(DEFENSE_STATS_HTML)
        parser = StatsParser(soup=soup, position=position)
        result = parser.parse()
        assert isinstance(result, DefenseStats)


class TestStatsParserRB:
    def test_parse_rb_stats(self, make_soup):
        soup = make_soup(RB_STATS_HTML)
        parser = StatsParser(soup=soup, position="RB")
        result = parser.parse()

        assert isinstance(result, OffenseSkillPlayerStats)
        assert result.rushing.att == 200
        assert result.rushing.yds == 1200
        assert result.rushing.avg == 6.0
        assert result.rushing.td == 14
        assert result.receiving.rec == 30
        assert result.receiving.yds == 250
        assert result.receiving.td == 2


class TestStatsParserOL:
    def test_parse_ol_returns_none(self, make_soup):
        soup = make_soup("<html><body></body></html>")
        parser = StatsParser(soup=soup, position="OL")
        result = parser.parse()
        assert result is None


class TestStatsParserUnknown:
    def test_parse_unknown_position_returns_none(self, make_soup):
        soup = make_soup("<html><body></body></html>")
        parser = StatsParser(soup=soup, position="K")
        result = parser.parse()
        assert result is None
