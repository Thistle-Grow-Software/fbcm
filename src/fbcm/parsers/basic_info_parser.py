import re

from bs4 import BeautifulSoup, Tag

from fbcm.constants import POSITION_TO_GROUP_MAP
from fbcm.models import BasicInfo

from .base import ParserBase


class BasicInfoParser(ParserBase):
    """Parses basic prospect information from a BeautifulSoup-parsed page."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self) -> BasicInfo:
        basic_info_dict = {}

        first_name, last_name = self._parse_name()

        info_details_div = self.soup.find("div", class_="player-info-details")
        basic_info_dict.update(
            self._parse_player_info_details_div(div=info_details_div)
        )

        basic_info_table_tag = self.soup.find("table", class_="basicInfoTable")
        basic_info_dict.update(self._parse_basic_info_table(basic_info_table_tag))

        basic_info_dict["class_"] = basic_info_dict.pop("class")
        basic_info_dict["hometown"] = basic_info_dict.pop("home town")
        basic_info_dict["photo_url"] = self._extract_image_url()

        return BasicInfo(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            **basic_info_dict,
        )

    def _parse_name(self) -> tuple[str, str]:
        first_name = self.soup.find("span", class_="player-info__first-name").get_text(
            strip=True
        )
        last_name = self.soup.find("span", class_="player-info__last-name").get_text(
            strip=True
        )
        return first_name, last_name

    def _parse_position(self, value: str) -> str:
        position_group_str = ""
        if "/" in value:
            p1, p2 = value.split("/")
            p1_group = POSITION_TO_GROUP_MAP.get(p1.upper())
            p2_group = POSITION_TO_GROUP_MAP.get(p2.upper())

            if not (p1_group or p2_group):
                raise ValueError(
                    f"Could not find a valid position group for position: {value}"
                )

            if p1_group and p2_group:
                position_group_str = f"{p1_group}/{p2_group}"
            elif p1_group:
                position_group_str = p1_group
            elif p2:
                position_group_str = p2_group

        else:
            position_group_str = POSITION_TO_GROUP_MAP[value.upper()]

        return position_group_str

    def _parse_player_info_details_div(self, div: Tag) -> dict:
        basic_info_dict = {}

        for attr_div in div.find_all("div", class_="player-info-details__item"):
            field_tag = attr_div.find("h6", class_="player-info-details__title")
            value_tag = attr_div.find("div", class_="player-info-details__value")

            field = field_tag.get_text(strip=True).lower()
            value = value_tag.get_text(strip=True).lower()

            if field == "position":
                value = self._parse_position(value=value)
            basic_info_dict[field] = value

        return basic_info_dict

    def _parse_basic_info_table(self, tag: Tag) -> dict:
        jersey_num_tag = tag.find(text=re.compile(r"#\d+"))
        if jersey_num_tag:
            jersey_num = jersey_num_tag.get_text(strip=True)
        else:
            jersey_num = ""

        sub_position_label = self.get_tag_with_title_containing(tag, "Sub-Position")
        sub_position_value = self.get_text_following_label(sub_position_label)

        last_updated_label = self.get_tag_with_title_containing(tag, "Last Updated")
        last_updated_value = self.get_text_following_label(last_updated_label)

        draft_yr_label = self.get_tag_with_title_containing(tag, "Draft Year")
        draft_yr_value = self.get_text_following_label(draft_yr_label)

        forty_label = self.get_tag_with_title_containing(tag, "40 yard dash time")
        forty_value = self.get_text_following_label(forty_label)

        return {
            "jersey": jersey_num,
            "play_style": sub_position_value,
            "last_updated": last_updated_value,
            "draft_year": draft_yr_value,
            "forty": forty_value.split()[0],
        }

    def _extract_image_url(self) -> str:
        figure_tag = self.soup.find("figure", class_="player-info__photo")
        image_path = figure_tag.find("img")["src"]
        return f"https://www.nfldraftbuzz.com{image_path}"
