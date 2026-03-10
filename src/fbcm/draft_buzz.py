import logging
import time
from collections import defaultdict
from pathlib import Path
from random import uniform
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Browser, Playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from fbcm.browser_retry import BrowserRetryHandler
from fbcm.models import Comparison, ProspectDataSoup
from fbcm.parsers import (
    BasicInfoParser,
    RatingExtractor,
    ScoutingReportParser,
    SkillsParser,
    StatsParser,
)

logger = logging.getLogger(__name__)


class PageFetcher:
    """Handles fetching web pages using Playwright browser automation."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
    CONTENT_WAIT_TIME = 3000

    MAX_RETRIES = 3

    def __init__(
        self,
        playwright: Playwright,
        headless: bool = False,
        base_url: str = "https://www.nfldraftbuzz.com",
    ):
        self.base_url = base_url
        self.playwright = playwright
        self.headless = headless
        self.browser = self._launch_browser()
        self._retry_handler = BrowserRetryHandler(
            playwright=playwright,
            launch_browser=self._launch_browser,
            max_retries=self.MAX_RETRIES,
        )

    def _launch_browser(self) -> Browser:
        """Launch a new browser instance."""
        return self.playwright.firefox.launch(headless=self.headless, slow_mo=150)

    def _ensure_browser_connected(self) -> None:
        """Ensure browser is connected, relaunch if necessary."""
        if not self.browser.is_connected():
            logger.warning("Browser disconnected, relaunching...")
            self.browser = self._launch_browser()

    def fetch(
        self, url: str, attempt_image_fetch: bool = False
    ) -> tuple[str, bytes | None, str]:
        """
        Fetch page content using Playwright browser automation.

        Args:
            url: The URL to fetch.
            attempt_image_fetch: Whether to attempt downloading the player image.

        Returns:
            Tuple of (page_text, image_bytes, image_type).
        """
        result, self.browser = self._retry_handler.execute(
            operation=lambda browser: self._fetch_with_page(url, attempt_image_fetch),
            browser=self.browser,
        )
        return result

    def fetch_soup(self, url) -> BeautifulSoup:
        self._ensure_browser_connected()
        page = self.browser.new_page()
        try:
            logger.info(f"Navigating to: {url}")
            page.goto(url=url)
            return BeautifulSoup(page.content(), "lxml")
        finally:
            page.close()

    def _fetch_with_page(
        self, url: str, attempt_image_fetch: bool
    ) -> tuple[str, bytes | None, str]:
        """Internal method to fetch a page. May raise PlaywrightError."""
        self._ensure_browser_connected()
        logger.debug("Opening new page...")

        page = self.browser.new_page()
        try:
            logger.info(f"Navigating to: {url}")
            try:
                page.goto(url)
            except PlaywrightTimeout:
                logger.warning("Page load timeout, continuing with partial content...")

            text_content = page.evaluate("() => document.body.innerText")
            if attempt_image_fetch:
                image_data, image_type = self._find_and_download_image(page, url)
            else:
                image_data = None
                image_type = None
            # TODO: Returning both text_content and page.content is a temporary kludge
            return text_content, image_data, image_type
        finally:
            page.close()

    def _find_and_download_image(self, page, base_url: str) -> tuple[bytes | None, str]:
        """Find and download the player image from the page."""
        image_url = self._find_image_url(page)

        if not image_url:
            image_url = self._find_any_large_image(page)

        if image_url:
            return self._download_image(page, image_url, base_url)

        return None, "jpeg"

    def _find_image_url(self, page) -> str | None:
        """Try to find image URL using predefined selectors."""
        img = page.locator("figure.player-info__photo img")
        src = img.get_attribute("src")
        return self._make_absolute_url(url=src, base_url=self.base_url)

    def _find_any_large_image(self, page) -> str | None:
        """Fallback: try to find any large player image."""
        try:
            images = page.query_selector_all("img")
            for img in images:
                src = img.get_attribute("src")
                if src and not self._should_skip_image(src):
                    if (
                        "nfldraftbuzz" in src
                        or "imagn" in src.lower()
                        or "player" in src.lower()
                    ):
                        return src
        except PlaywrightError:
            logger.warning("Failed to query images from page, skipping image search")
        return None

    def _should_skip_image(self, src: str) -> bool:
        """Check if an image URL should be skipped."""
        src_lower = src.lower()
        return any(pattern in src_lower for pattern in self.SKIP_IMAGE_PATTERNS)

    def _download_image(
        self, page, image_url: str, base_url: str
    ) -> tuple[bytes | None, str]:
        """Download image from URL."""
        logger.info(f"Found player image: {image_url[:80]}...")
        try:
            image_url = self._make_absolute_url(image_url, base_url)
            response = page.request.get(image_url)
            if response.ok:
                image_data = response.body()
                image_type = self._get_image_type(
                    response.headers.get("content-type", "")
                )
                logger.info(f"Downloaded image: {len(image_data)} bytes ({image_type})")
                return image_data, image_type
        except (PlaywrightError, PlaywrightTimeout) as e:
            logger.error(f"Failed to download image: {e}")
        return None, "jpeg"

    @staticmethod
    def _make_absolute_url(url: str, base_url: str = None) -> str:
        """Convert relative URL to absolute."""
        if url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            return urljoin(base_url, url)
        return url

    @staticmethod
    def _get_image_type(content_type: str) -> str:
        """Determine image type from content-type header."""
        if "png" in content_type:
            return "png"
        elif "gif" in content_type:
            return "gif"
        elif "webp" in content_type:
            return "webp"
        return "jpeg"


class ProspectParser:
    """
    Facade/orchestrator that coordinates focused parser classes to parse
    nfldraftbuzz.com prospect profiles. Maintains the same public API as
    the former ProspectParser class.
    """

    def __init__(self, soup: BeautifulSoup, position: str):
        self.soup = soup
        self.position = position
        self._basic_info_parser = BasicInfoParser(soup=soup)
        self._rating_extractor = RatingExtractor(soup=soup)
        self._skills_parser = SkillsParser(position=position)
        self._scouting_report_parser = ScoutingReportParser(soup=soup)

    def parse(self) -> ProspectDataSoup:
        basic_info = self._basic_info_parser.parse()
        rtgs_table, comps_table = self._extract_ratings_comps_tables()

        ratings = self._rating_extractor.parse(table=rtgs_table)
        skills = self._skills_parser.parse(table=rtgs_table)
        comparisons = self.parse_comparisons(table=comps_table) if comps_table else None
        scouting_report = self._scouting_report_parser.parse()

        return ProspectDataSoup(
            basic_info=basic_info,
            ratings=ratings,
            skills=skills,
            comparisons=comparisons,
            scouting_report=scouting_report,
            stats=None,
        )

    def parse_stats(self, soup: BeautifulSoup):
        stats_parser = StatsParser(soup=soup, position=self.position)
        return stats_parser.parse()

    def parse_comparisons(self, table: Tag) -> list[Comparison]:
        comparisons = []
        comp_rows = table.find("tbody").find_all("tr")

        for row in comp_rows:
            text_parts = row.get_text().split()
            comp_name = f"{text_parts[0]} {text_parts[1]}"
            comp_school = text_parts[3]
            comp_score = int(text_parts[-1].replace("%", ""))

            comparisons.append(
                Comparison(name=comp_name, school=comp_school, similarity=comp_score)
            )

        return comparisons

    def _extract_ratings_comps_tables(self):
        ratings_and_rankings = [
            table
            for table in self.soup.find_all("table", class_="starRatingTable")
            if not table.find("th", string=lambda s: "measurables" in s.lower())
        ]

        ratings = ratings_and_rankings[0]
        if len(ratings_and_rankings) > 1:
            comparisons = ratings_and_rankings[1]
        else:
            comparisons = None
        return ratings, comparisons


class DraftBuzzScraper:
    """Main orchestrator for scraping NFL Draft Buzz prospect pages."""

    def __init__(
        self,
        playwright: Playwright,
        profile_root_dir: Path = None,
        fetcher: PageFetcher = None,
        headless: bool = True,
    ):
        self.profile_root_dir = profile_root_dir
        self.base_url = "https://www.nfldraftbuzz.com"
        self.fetcher = fetcher or PageFetcher(
            playwright=playwright, base_url=self.base_url, headless=headless
        )
        self.parser = None
        self.position_rankings_used = defaultdict(list)

        self.current_prospect_data: ProspectDataSoup | None = None

    def scrape_from_url(self, url: str, position: str) -> ProspectDataSoup:
        """Scrape prospect data from a URL."""
        self.current_prospect_data = None
        logger.info("Parsing prospect data...")
        full_url = f"{self.base_url}{url}"
        base_soup = self.fetcher.fetch_soup(url=full_url)
        self.parser = ProspectParser(soup=base_soup, position=position)
        prospect_data = self.parser.parse()

        logger.info("Fetching stats page")
        slug_parts = url.split("/")
        player_stats_slug = f"/{slug_parts[1]}/stats/{slug_parts[-1]}"
        stats_full_url = f"{self.base_url}{player_stats_slug}"

        stats_soup = self.fetcher.fetch_soup(url=stats_full_url)
        logger.info("Attempting to parse stats")
        stats_data = self.parser.parse_stats(soup=stats_soup)
        prospect_data.stats = stats_data

        self.current_prospect_data = prospect_data
        return prospect_data

    def save_player_photo_to_disk(self):
        logger.info(
            f"Saving photo for {self.current_prospect_data.basic_info.full_name}"
        )
        logger.info(
            f"Fetching image from {self.current_prospect_data.basic_info.photo_url}"
        )

        response = requests.get(self.current_prospect_data.basic_info.photo_url)
        response.raise_for_status()
        file_name = f"{self.current_prospect_data.basic_info.full_name}.png"

        output_path = Path(self.profile_root_dir, "player_photos", file_name)
        output_path.write_bytes(response.content)
        logger.info(f"Wrote image to disk at {output_path}")

    def print_summary(self, data: ProspectDataSoup) -> None:
        """Log summary of extracted data."""
        logger.info("Extracted data summary:")
        logger.info(f"  Name: {data.basic_info.full_name}")
        logger.info(f"  Position: {data.basic_info.position}")
        logger.info(f"  School: {data.basic_info.college}")
        logger.info(f"  Rating: {data.ratings.overall_rating}/100")
        logger.info(f"  Draft Projection: {data.ratings.draft_projection}")
        logger.info(f"  Strengths: {len(data.scouting_report.strengths)} items")
        logger.info(f"  Weaknesses: {len(data.scouting_report.weaknesses)} items")
        logger.info(
            f"  Image: {'Yes' if data.basic_info.photo_path.exists() else 'No'}"
        )


class ProspectProfileListExtractor:
    MAX_RETRIES = 3

    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.browser = self._launch_browser()
        self.base_url = "https://www.nfldraftbuzz.com"
        self._retry_handler = BrowserRetryHandler(
            playwright=playwright,
            launch_browser=self._launch_browser,
            max_retries=self.MAX_RETRIES,
        )

    def _launch_browser(self) -> Browser:
        """Launch a new browser instance."""
        return self.playwright.firefox.launch(headless=False)

    def extract_prospect_hrefs(self, page):
        logger.info(f"Extracting prospect hrefs for {page.url}")
        rows = page.locator("#positionRankTable tbody tr")
        data_hrefs = rows.evaluate_all(
            "rows => rows.map(row => row.getAttribute('data-href'))"
        )
        return data_hrefs

    def extract_prospect_urls_for_position(self, pos: str) -> list[str]:
        all_profiles = []

        path = f"/positions/{pos}/1/2026"
        full_url = f"{self.base_url}{path}"

        page = self._create_page_with_retry(full_url)
        all_profiles.extend(self.extract_prospect_hrefs(page=page))
        links = page.locator("ul.pagination li.page-item a.page-link[href]")
        position_page_hrefs = links.evaluate_all(
            "anchors => anchors.map(a => a.getAttribute('href'))"
        )

        for path in position_page_hrefs:
            page.close()
            full_url = f"{self.base_url}{path}"
            page = self._create_page_with_retry(full_url)
            time.sleep(uniform(4.5, 5.5))

            prospect_hrefs = self.extract_prospect_hrefs(page)
            all_profiles.extend(prospect_hrefs)
        page.close()
        return all_profiles

    def _create_page_with_retry(self, url: str):
        """Create a new page and navigate to URL with retry on browser crash."""

        def _open_page(browser: Browser):
            if not browser.is_connected():
                raise PlaywrightError("browser has been closed")
            page = browser.new_page()
            page.goto(url, timeout=0)
            return page

        result, self.browser = self._retry_handler.execute(
            operation=_open_page,
            browser=self.browser,
        )
        return result
