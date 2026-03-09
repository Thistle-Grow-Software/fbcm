from bs4 import BeautifulSoup

from fbcm.models import ScoutingReport


class ScoutingReportParser:
    """Parses scouting report text (bio, strengths, weaknesses, summary)."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self) -> ScoutingReport:
        intro_div = self.soup.find("div", class_="playerDescIntro")
        if not intro_div:
            return ScoutingReport()

        strengths_div = self.soup.find("div", class_="playerDescPro")
        weak_summary_divs = self.soup.find_all("div", class_="playerDescNeg")
        weaknesses_div = weak_summary_divs[0]

        summary = None
        if len(weak_summary_divs) > 1:
            summary = weak_summary_divs[1].get_text(strip=True)

        strengths = [
            line
            for line in strengths_div.get_text().splitlines()
            if line and "scouting report" not in line.lower()
        ]
        weaknesses = [
            line
            for line in weaknesses_div.get_text().splitlines()
            if line and "scouting report" not in line.lower()
        ]

        return ScoutingReport(
            bio=intro_div.get_text(strip=True),
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary,
        )
