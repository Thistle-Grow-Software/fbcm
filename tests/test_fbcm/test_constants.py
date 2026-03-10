from fbcm.constants import (
    DEFAULT_CONTENT_WAIT_TIME_MS,
    DEFAULT_MAX_BROWSER_RETRIES,
    DEFAULT_SLOW_MO_MS,
    DEFAULT_VIEWPORT,
    NFL_DRAFT_BUZZ_BASE_URL,
    NFL_EPISODES_BASE_URL,
    NFL_REPLAY_BASE_URL,
    PAGE_NAVIGATION_SLEEP_RANGE,
    POSITION_GROUP_SLEEP_RANGE,
    PROFILE_SCRAPE_SLEEP_RANGE,
)


class TestURLConstants:
    def test_nfl_replay_base_url(self):
        assert NFL_REPLAY_BASE_URL == "https://www.nfl.com/plus/games/"

    def test_nfl_episodes_base_url(self):
        assert NFL_EPISODES_BASE_URL == "https://www.nfl.com/plus/episodes/"

    def test_nfl_draft_buzz_base_url(self):
        assert NFL_DRAFT_BUZZ_BASE_URL == "https://www.nfldraftbuzz.com"

    def test_url_constants_are_strings(self):
        for url in [
            NFL_REPLAY_BASE_URL,
            NFL_EPISODES_BASE_URL,
            NFL_DRAFT_BUZZ_BASE_URL,
        ]:
            assert isinstance(url, str)

    def test_url_constants_start_with_https(self):
        for url in [
            NFL_REPLAY_BASE_URL,
            NFL_EPISODES_BASE_URL,
            NFL_DRAFT_BUZZ_BASE_URL,
        ]:
            assert url.startswith("https://")


class TestBrowserAutomationConstants:
    def test_default_viewport_dimensions(self):
        assert DEFAULT_VIEWPORT == {"width": 1920, "height": 1080}

    def test_default_slow_mo(self):
        assert DEFAULT_SLOW_MO_MS == 150

    def test_default_content_wait_time(self):
        assert DEFAULT_CONTENT_WAIT_TIME_MS == 3000

    def test_default_max_browser_retries(self):
        assert DEFAULT_MAX_BROWSER_RETRIES == 3


class TestSleepRangeConstants:
    def test_profile_scrape_sleep_range(self):
        assert PROFILE_SCRAPE_SLEEP_RANGE == (3.5, 4.5)

    def test_page_navigation_sleep_range(self):
        assert PAGE_NAVIGATION_SLEEP_RANGE == (4.5, 5.5)

    def test_position_group_sleep_range(self):
        assert POSITION_GROUP_SLEEP_RANGE == (10, 15)

    def test_sleep_ranges_are_two_element_tuples(self):
        for sleep_range in [
            PROFILE_SCRAPE_SLEEP_RANGE,
            PAGE_NAVIGATION_SLEEP_RANGE,
            POSITION_GROUP_SLEEP_RANGE,
        ]:
            assert isinstance(sleep_range, tuple)
            assert len(sleep_range) == 2

    def test_sleep_range_min_less_than_max(self):
        for sleep_range in [
            PROFILE_SCRAPE_SLEEP_RANGE,
            PAGE_NAVIGATION_SLEEP_RANGE,
            POSITION_GROUP_SLEEP_RANGE,
        ]:
            assert sleep_range[0] < sleep_range[1]
