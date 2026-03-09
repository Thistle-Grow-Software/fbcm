from bs4 import Tag

from fbcm.models import (
    DefensiveBackSkills,
    DefensiveLinemanSkills,
    LinebackerSkills,
    OffensiveLinemanSkills,
    PassCatcherSkills,
    PassingSkills,
    RunningBackSkills,
    SkillRatings,
)


class SkillsParser:
    """Parses prospect skill ratings from the ratings table."""

    def __init__(self, position: str):
        self.position = position

    def parse(self, table: Tag) -> SkillRatings:
        rows = table.find_all("tr")[4:]
        skill_rtgs_rows = self._gather_skill_rtg_rows(rows=rows)
        skill_ratings_dict = self._extract_skill_ratings(rows=skill_rtgs_rows)
        return self._construct_skill_ratings_obj(ratings=skill_ratings_dict)

    def _gather_skill_rtg_rows(
        self, rows: list[Tag], sentinel_val: str = "draft projection"
    ) -> list[Tag]:
        skill_rows = []
        for row in rows:
            if sentinel_val in row.get_text().lower():
                break
            skill_rows.append(row)
        return skill_rows

    def _extract_skill_ratings(self, rows: list[Tag]) -> dict:
        skills = {}
        for row in rows:
            skill_name, rating = (
                row.get_text(strip=True)
                .lower()
                .replace(" ", "_")
                .replace("%", "")
                .split(":")
            )

            if "/" in rating:
                rating = rating.split("/")[0]
            rating = float(rating.replace("_", ""))

            skills[skill_name.replace("/", "_")] = int(rating)

        return skills

    def _construct_skill_ratings_obj(self, ratings: dict) -> SkillRatings:
        match self.position:
            case "QB":
                return PassingSkills(**ratings)
            case "RB":
                return RunningBackSkills(**ratings)
            case "WR" | "TE":
                return PassCatcherSkills(**ratings)
            case "OL":
                return OffensiveLinemanSkills(**ratings)
            case "DL" | "EDGE":
                return DefensiveLinemanSkills(**ratings)
            case "LB":
                return LinebackerSkills(**ratings)
            case "DB":
                return DefensiveBackSkills(**ratings)
            case _:
                raise ValueError(
                    f"Could not find skill ratings for position: {self.position}"
                )
