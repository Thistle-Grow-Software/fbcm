from fbcm.constants import (
    NFL_EPISODES_BASE_URL,
    NFL_REPLAY_BASE_URL,
)


class TestURLConstants:
    def test_nfl_replay_base_url(self):
        assert NFL_REPLAY_BASE_URL == "https://www.nfl.com/plus/games/"

    def test_nfl_episodes_base_url(self):
        assert NFL_EPISODES_BASE_URL == "https://www.nfl.com/plus/episodes/"

    def test_url_constants_are_strings(self):
        for url in [
            NFL_REPLAY_BASE_URL,
            NFL_EPISODES_BASE_URL,
        ]:
            assert isinstance(url, str)

    def test_url_constants_start_with_https(self):
        for url in [
            NFL_REPLAY_BASE_URL,
            NFL_EPISODES_BASE_URL,
        ]:
            assert url.startswith("https://")
