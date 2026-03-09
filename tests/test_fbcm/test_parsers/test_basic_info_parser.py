from fbcm.parsers import BasicInfoParser

from .conftest import BASIC_INFO_HTML


class TestBasicInfoParser:
    def test_parse_extracts_name(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.first_name == "Cam"
        assert result.last_name == "Ward"
        assert result.full_name == "Cam Ward"

    def test_parse_extracts_physical_attributes(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.height == "6-2"
        assert result.weight == "223"

    def test_parse_extracts_college_and_position(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.college == "miami"
        assert result.position == "QB"

    def test_parse_extracts_class_and_hometown(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.class_ == "senior"
        assert result.hometown == "columbia, sc"

    def test_parse_extracts_jersey_and_play_style(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.jersey == "#1"
        assert result.play_style == "Pocket Passer"

    def test_parse_extracts_draft_year_and_forty(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.draft_year == "2026"
        assert result.forty == "4.65"

    def test_parse_extracts_photo_url(self, make_soup):
        soup = make_soup(BASIC_INFO_HTML)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert (
            result.photo_url
            == "https://www.nfldraftbuzz.com/images/players/cam-ward.png"
        )

    def test_parse_dual_position(self, make_soup):
        html = BASIC_INFO_HTML.replace(
            '<div class="player-info-details__value">QB</div>',
            '<div class="player-info-details__value">DE/OLB</div>',
        )
        soup = make_soup(html)
        parser = BasicInfoParser(soup=soup)
        result = parser.parse()

        assert result.position == "EDGE/LB"
