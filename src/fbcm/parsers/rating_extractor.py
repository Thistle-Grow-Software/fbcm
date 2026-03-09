from bs4 import BeautifulSoup, Tag

from fbcm.models import RatingsAndRankings

from .base import ParserBase


class RatingExtractor(ParserBase):
    """Extracts prospect ratings, rankings, and outlet grades."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self, table: Tag) -> RatingsAndRankings:
        self._perform_rating_checks(table=table)

        table_rows = table.find_all("tr")
        overall = self._extract_ovr_rtg(row=table_rows[0])
        opposition = self._extract_opposition_rtg(row=table_rows[2])

        proj_rank_row = self._get_projection_ranks_row(rows=table_rows)
        proj_ranks = self._extract_proj_and_rankings(row=proj_rank_row)
        avg_ranks = self._extract_average_ranks()

        outlet_ratings = self._extract_outlet_ratings(table=table)

        return RatingsAndRankings(
            overall_rating=overall,
            opposition_rating=opposition,
            **proj_ranks,
            **outlet_ratings,
            **avg_ranks,
        )

    def _perform_rating_checks(self, table: Tag):
        ovr_rtg_label = table.find("th")
        if "overall rating" not in ovr_rtg_label.get_text().lower():
            raise ValueError(
                f"Unexpected label in first <th> element: {ovr_rtg_label.get_text}"
            )

    def _extract_ovr_rtg(self, row: Tag) -> float:
        return float(row.find("span").get_text(strip=True).replace(" / 100", ""))

    def _extract_opposition_rtg(self, row: Tag) -> int:
        meter_div = row.find("div", class_="meter")
        rtg_as_str = meter_div["title"].split(":")[-1].strip().replace("%", "")
        return int(rtg_as_str)

    def _extract_proj_and_rankings(self, row: Tag) -> dict:
        projection_label = self.get_tag_with_text(
            search_space=row, tag_name="span", text="draft projection"
        )
        projection = self.get_text_following_label(label_tag=projection_label)

        ovr_rank_label = self.get_tag_with_text(
            search_space=row, tag_name="span", text="overall rank"
        )
        ovr_rank = self.get_text_following_label(label_tag=ovr_rank_label)

        pos_rank_label = self.get_tag_with_text(
            search_space=row, tag_name="span", text="position rank"
        )
        pos_rank = self.get_text_following_label(label_tag=pos_rank_label)

        return {
            "draft_projection": projection,
            "overall_rank": ovr_rank,
            "position_rank": pos_rank,
        }

    def _get_projection_ranks_row(self, rows: list[Tag]) -> Tag | None:
        for row in rows:
            if "draft projection" in row.get_text().lower():
                return row
        return None

    def _extract_average_ranks(self) -> dict:
        rankings_div = self.soup.find("div", class_="rankingBox")
        avg_ovr, avg_pos = rankings_div.find_all("div", class_="rankVal")
        return {
            "avg_overall_rank": float(avg_ovr.get_text(strip=True)),
            "avg_position_rank": float(avg_pos.get_text(strip=True)),
        }

    def _extract_outlet_ratings(self, table: Tag) -> dict[str, float | None]:
        return {
            "espn": self._extract_espn(table=table),
            "rivals": self._extract_rivals(table=table),
            "rtg_247": self._extract_247(table=table),
        }

    def _extract_rivals(self, table: Tag) -> float | None:
        rivals_row = self.get_tag_with_text(
            search_space=table, tag_name="span", text="rivals"
        )
        if rivals_row:
            return float(rivals_row.get_text(strip=True).split(":")[-1].split()[0])
        return None

    def _extract_247(self, table: Tag) -> float | None:
        sports_247_rtg_row = self.get_tag_with_text(
            search_space=table, tag_name="span", text="247 rating"
        )
        if sports_247_rtg_row:
            return float(
                sports_247_rtg_row.get_text(strip=True).split()[-1].split("/")[0]
            )
        return None

    def _extract_espn(self, table: Tag) -> float | None:
        espn_rtg_row = self.get_tag_with_text(
            search_space=table, tag_name="span", text="espn"
        )
        if espn_rtg_row:
            return float(espn_rtg_row.get_text(strip=True).split()[-1].split("/")[0])
        return None
