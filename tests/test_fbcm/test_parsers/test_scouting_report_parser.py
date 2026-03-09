from fbcm.parsers import ScoutingReportParser

from .conftest import SCOUTING_REPORT_HTML


class TestScoutingReportParser:
    def test_parse_bio(self, make_soup):
        soup = make_soup(SCOUTING_REPORT_HTML)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert result.bio == "Top quarterback prospect with elite arm talent."

    def test_parse_strengths(self, make_soup):
        soup = make_soup(SCOUTING_REPORT_HTML)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert "Strong arm" in result.strengths
        assert "Quick release" in result.strengths
        assert "Good pocket presence" in result.strengths

    def test_parse_filters_scouting_report_header(self, make_soup):
        soup = make_soup(SCOUTING_REPORT_HTML)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        for item in result.strengths:
            assert "scouting report" not in item.lower()
        for item in result.weaknesses:
            assert "scouting report" not in item.lower()

    def test_parse_weaknesses(self, make_soup):
        soup = make_soup(SCOUTING_REPORT_HTML)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert "Footwork needs improvement" in result.weaknesses
        assert "Tends to hold ball too long" in result.weaknesses

    def test_parse_summary(self, make_soup):
        soup = make_soup(SCOUTING_REPORT_HTML)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert result.summary == "Overall a very talented prospect with high upside."

    def test_parse_returns_empty_when_no_intro(self, make_soup):
        soup = make_soup("<html><body></body></html>")
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert result.bio == ""
        assert result.strengths == []
        assert result.weaknesses == []
        assert result.summary is None

    def test_parse_no_summary_when_single_neg_div(self, make_soup):
        html = """
        <div class="playerDescIntro">Bio text here.</div>
        <div class="playerDescPro">Strengths here</div>
        <div class="playerDescNeg">Weaknesses here</div>
        """
        soup = make_soup(html)
        parser = ScoutingReportParser(soup=soup)
        result = parser.parse()

        assert result.summary is None
        assert result.bio == "Bio text here."
