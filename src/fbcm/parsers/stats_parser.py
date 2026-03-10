import logging

from bs4 import BeautifulSoup, Tag

from fbcm.models import (
    DefenseStats,
    InterceptionStats,
    OffenseSkillPlayerStats,
    PassingStats,
    ReceivingStats,
    RushingStats,
    Stats,
    TackleStats,
)

from .base import ParserBase

logger = logging.getLogger(__name__)


class StatsParser(ParserBase):
    """Parses prospect statistical data from stats page tables."""

    def __init__(self, soup: BeautifulSoup, position: str):
        self.soup = soup
        self.position = position

    def parse(self) -> Stats | None:
        table_div = None
        match self.position:
            case "QB":
                table_div = self.soup.find(id="QBstats")
            case "RB" | "WR" | "TE":
                table_div = self.soup.find(id="RB-Rush-stats")
            case "OL":
                pass
            case "DL" | "EDGE" | "LB" | "DB":
                table_div = self.soup.find(id="DBLBDL-stats")
            case _:
                logger.warning(
                    f"Could not match position {self.position} to any known group."
                )

        if table_div is not None:
            extracted_stats = self._extract_stats_object(div=table_div)
            if extracted_stats:
                return extracted_stats[0]

        return None

    def _extract_games_and_snaps(self) -> dict:
        gp_label = self.get_tag_with_title_containing(
            tag=self.soup, search_str="College Games Played"
        )
        games_played = int(self.get_text_following_label(label_tag=gp_label) or "0")
        snaps_label = self.get_tag_with_title_containing(
            tag=self.soup, search_str="College Snap Count"
        )
        snap_count = int(self.get_text_following_label(label_tag=snaps_label) or "0")

        return {"games_played": games_played, "snap_count": snap_count}

    def _transform_passing_stats(self, season_stats: dict) -> dict:
        season_stats["cmp_pct"] = season_stats.pop("cmp%")
        season_stats["ints"] = season_stats.pop("int")
        season_stats["qb_rtg"] = season_stats.pop("pro rat")
        season_stats.pop("rat")
        season_stats.pop("avg")

        season_stats["year"] = season_stats.pop("year").split()[0]

        for fld in ["cmp", "att", "yds", "td", "ints", "sack", "year"]:
            try:
                season_stats[fld] = int(season_stats[fld] or 0)
            except ValueError:
                logger.error(f"Invalid value for field {fld}: {season_stats[fld]}")
                logger.error(f"Full season_stats_dict: {season_stats}")
                raise

        for fld in ["cmp_pct", "qb_rtg"]:
            try:
                season_stats[fld] = float(season_stats[fld] or 0.0)
            except ValueError:
                logger.error(f"Invalid value for field {fld}: {season_stats[fld]}")
                logger.error(f"Full season_stats_dict: {season_stats}")
                raise

        return season_stats

    def _transform_stats(self, season_stats: dict) -> dict:
        match self.position:
            case "QB":
                return self._transform_passing_stats(season_stats=season_stats)
        return season_stats

    def _extract_stats_object(self, div: Tag) -> list:
        stats_table = div.find("table")
        header_values = [
            th.get_text(strip=True).lower()
            for th in stats_table.thead.find_all("th", class_="player-season-avg__stat")
            if th.get_text(strip=True)
        ]
        seasons = []

        gp_and_snaps = self._extract_games_and_snaps()

        for row in stats_table.tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]

            if self.position == "QB":
                season_stats = dict(zip(header_values, cells))
                season_stats = self._transform_stats(season_stats=season_stats)
                stats_obj = PassingStats(**season_stats, **gp_and_snaps)
            elif self.position in ["RB"]:
                season_stats = {
                    "year": cells[0],
                    **gp_and_snaps,
                    "rushing": {
                        "att": int(cells[1] or "0"),
                        "yds": int(cells[2] or "0"),
                        "avg": float(cells[3] or "0"),
                        "td": int(cells[4] or "0"),
                    },
                    "receiving": {
                        "rec": int(cells[5] or "0"),
                        "yds": int(cells[6] or "0"),
                        "avg": float(cells[7] or "0"),
                        "td": int(cells[8] or "0"),
                    },
                }
                rushing_stats = RushingStats(
                    year=season_stats["year"], **season_stats["rushing"]
                )
                receiving_stats = ReceivingStats(
                    year=season_stats["year"], **season_stats["receiving"]
                )
                stats_obj = OffenseSkillPlayerStats(
                    year=season_stats["year"],
                    rushing=rushing_stats,
                    receiving=receiving_stats,
                )
            elif self.position in ["WR", "TE"]:
                season_stats = {
                    "year": cells[0],
                    **gp_and_snaps,
                    "receiving": {
                        "rec": int(cells[1] or "0"),
                        "yds": int(cells[2] or "0"),
                        "avg": float(cells[3] or "0"),
                        "td": int(cells[4] or "0"),
                    },
                    "rushing": {
                        "att": int(cells[5] or "0"),
                        "yds": int(cells[6] or "0"),
                        "avg": float(cells[7] or "0"),
                        "td": int(cells[8] or "0"),
                    },
                }
                rushing_stats = RushingStats(
                    year=season_stats["year"], **season_stats["rushing"]
                )
                receiving_stats = ReceivingStats(
                    year=season_stats["year"], **season_stats["receiving"]
                )
                stats_obj = OffenseSkillPlayerStats(
                    year=season_stats["year"],
                    rushing=rushing_stats,
                    receiving=receiving_stats,
                )
            elif self.position == "OL":
                stats_obj = gp_and_snaps
            elif self.position in ["DL", "EDGE", "LB", "DB"]:
                season_stats = {
                    "year": int(cells[0].split()[0]),
                    **gp_and_snaps,
                    "tackle": {
                        "total": int(cells[1] or "0"),
                        "solo": int(cells[2] or "0"),
                        "ff": int(cells[3] or "0"),
                        "sacks": float(cells[4] or "0"),
                    },
                    "interception": {
                        "ints": int(cells[5] or "0"),
                        "yds": int(cells[6] or "0"),
                        "td": int(cells[7] or "0"),
                        "pds": int(cells[8] or "0"),
                    },
                }
                tackle_stats = TackleStats(
                    year=season_stats["year"], **season_stats["tackle"]
                )
                interception_stats = InterceptionStats(
                    year=season_stats["year"], **season_stats["interception"]
                )
                stats_obj = DefenseStats(
                    year=season_stats["year"],
                    tackle=tackle_stats,
                    interception=interception_stats,
                )
            else:
                raise ValueError(
                    f"Could not match position {self.position} to "
                    f"a position with a defined stats mapping."
                )

            seasons.append(stats_obj)

        seasons.sort(key=lambda stats: stats.year, reverse=True)

        return seasons
