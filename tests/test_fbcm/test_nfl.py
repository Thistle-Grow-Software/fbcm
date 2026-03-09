import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fbcm.base import BaseDownloader
from fbcm.nfl import (
    FileNamer,
    GameExtractor,
    MetadataWriter,
    NFLShowDownloader,
    NFLWeeklyDownloader,
)

# --- Fixtures ---


def _make_game_dict(**overrides):
    """Helper to build a game info dict with sensible defaults."""
    game = {
        "season": 2024,
        "week": 1,
        "week_type": "REG",
        "date_": "2024-09-08",
        "homeTeam": "Pittsburgh Steelers",
        "awayTeam": "Atlanta Falcons",
        "divider": "at",
        "slug": "atlanta-falcons-at-pittsburgh-steelers-2024-reg-1",
        "replays": {
            "Full Game": {
                "mcpPlaybackId": "abc123",
                "thumbnailUrl": "https://example.com/thumb.jpg",
                "url": "https://www.nfl.com/plus/games/atlanta-falcons-at-pittsburgh-steelers-2024-reg-1?mcpid=abc123",
            }
        },
    }
    game.update(overrides)
    return game


def _make_weekly_game_detail(
    home_full_name="Pittsburgh Steelers",
    away_full_name="Atlanta Falcons",
    neutral_site=False,
    slug="atlanta-falcons-at-pittsburgh-steelers-2024-reg-1",
    replays=None,
):
    """Build a mock WeeklyGameDetail-like object."""
    home_team = SimpleNamespace(full_name=home_full_name)
    away_team = SimpleNamespace(full_name=away_full_name)
    external_ids = [SimpleNamespace(source="slug", id=slug)]

    if replays is None:
        replays = [
            SimpleNamespace(
                sub_type="Full Game",
                mcp_playback_id="abc123",
                thumbnail={"thumbnailUrl": "https://example.com/thumb.jpg"},
            )
        ]

    return SimpleNamespace(
        season=2024,
        week=1,
        week_type="REG",
        date_="2024-09-08",
        home_team=home_team,
        away_team=away_team,
        neutral_site=neutral_site,
        external_ids=external_ids,
        replays=replays,
    )


# --- FileNamer Tests ---


class TestFileNamer:
    def test_construct_file_name_basic(self):
        namer = FileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=1)

        assert result == "NFL Full Game - s2024e001 - 2024_Wk01_ATL_at_PIT"

    def test_construct_file_name_neutral_site(self):
        namer = FileNamer()
        game = _make_game_dict(
            homeTeam="Kansas City Chiefs",
            awayTeam="San Francisco 49ers",
            divider="vs",
        )
        result = namer.construct_file_name(
            game=game, replay_type="Full Game", ep_num=87
        )

        assert result == "NFL Full Game - s2024e087 - 2024_Wk01_SFO_vs_KC"

    def test_construct_file_name_jets_away(self):
        """Jets should get (A) suffix for city disambiguation."""
        namer = FileNamer()
        game = _make_game_dict(awayTeam="New York Jets", homeTeam="Miami Dolphins")
        result = namer.construct_file_name(
            game=game, replay_type="Condensed Game", ep_num=5
        )

        assert "NYJ" in result
        assert "Condensed Game" in result

    def test_construct_file_name_giants_home(self):
        """Giants should get (N) suffix for city disambiguation."""
        namer = FileNamer()
        game = _make_game_dict(homeTeam="New York Giants", awayTeam="Dallas Cowboys")
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=3)

        assert "NYG" in result

    def test_construct_file_name_chargers_away(self):
        """Chargers should get (A) suffix for city disambiguation."""
        namer = FileNamer()
        game = _make_game_dict(
            awayTeam="Los Angeles Chargers", homeTeam="Denver Broncos"
        )
        result = namer.construct_file_name(game=game, replay_type="All-22", ep_num=10)

        assert "LAC" in result

    def test_construct_file_name_rams_home(self):
        """Rams should get (N) suffix for city disambiguation."""
        namer = FileNamer()
        game = _make_game_dict(homeTeam="Los Angeles Rams", awayTeam="Seattle Seahawks")
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=2)

        assert "LAR" in result

    def test_construct_file_name_episode_padding(self):
        namer = FileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=5)

        assert "e005" in result

    def test_construct_file_name_large_episode_number(self):
        namer = FileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(
            game=game, replay_type="Full Game", ep_num=150
        )

        assert "e150" in result

    def test_construct_file_name_week_padding(self):
        namer = FileNamer()
        game = _make_game_dict(week=8)
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=1)

        assert "Wk08" in result


# --- GameExtractor Tests ---


class TestGameExtractor:
    def test_should_extract_all_teams(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail()

        assert extractor.should_extract(game, teams=["all"]) is True

    def test_should_extract_matching_team(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail()

        assert extractor.should_extract(game, teams=["PIT"]) is True

    def test_should_extract_no_match(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail()

        assert extractor.should_extract(game, teams=["DAL"]) is False

    def test_should_extract_away_team_match(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail()

        assert extractor.should_extract(game, teams=["ATL"]) is True

    def test_extract_game_info_basic(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail()
        result = extractor.extract_game_info(game, replay_types=["Full Game"])

        assert result["season"] == 2024
        assert result["week"] == 1
        assert result["homeTeam"] == "Pittsburgh Steelers"
        assert result["awayTeam"] == "Atlanta Falcons"
        assert result["divider"] == "at"
        assert result["slug"] == "atlanta-falcons-at-pittsburgh-steelers-2024-reg-1"
        assert "Full Game" in result["replays"]

    def test_extract_game_info_neutral_site(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_weekly_game_detail(neutral_site=True)
        result = extractor.extract_game_info(game, replay_types=["Full Game"])

        assert result["divider"] == "vs"

    def test_extract_game_info_filters_replay_types(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        replays = [
            SimpleNamespace(
                sub_type="Full Game",
                mcp_playback_id="abc123",
                thumbnail={"thumbnailUrl": "https://example.com/thumb.jpg"},
            ),
            SimpleNamespace(
                sub_type="Condensed Game",
                mcp_playback_id="def456",
                thumbnail={"thumbnailUrl": "https://example.com/thumb2.jpg"},
            ),
        ]
        game = _make_weekly_game_detail(replays=replays)

        result = extractor.extract_game_info(game, replay_types=["Condensed Game"])

        assert "Condensed Game" in result["replays"]
        assert "Full Game" not in result["replays"]

    def test_extract_game_info_default_replay_types(self):
        """When replay_types is None, all DEFAULT_REPLAY_TYPES should be included."""
        extractor = GameExtractor(nfl_client=MagicMock())
        replays = [
            SimpleNamespace(
                sub_type="Full Game",
                mcp_playback_id="abc123",
                thumbnail={"thumbnailUrl": "https://example.com/thumb.jpg"},
            ),
        ]
        game = _make_weekly_game_detail(replays=replays)
        result = extractor.extract_game_info(game, replay_types=None)

        assert "Full Game" in result["replays"]

    def test_construct_replay_url(self):
        extractor = GameExtractor(nfl_client=MagicMock())
        game = _make_game_dict()
        url = extractor._construct_replay_url(game, "Full Game")

        assert url == (
            "https://www.nfl.com/plus/games/"
            "atlanta-falcons-at-pittsburgh-steelers-2024-reg-1"
            "?mcpid=abc123"
        )

    def test_construct_replay_url_custom_base(self):
        extractor = GameExtractor(
            nfl_client=MagicMock(),
            replay_base_url="https://custom.nfl.com/games/",
        )
        game = _make_game_dict()
        url = extractor._construct_replay_url(game, "Full Game")

        assert url.startswith("https://custom.nfl.com/games/")

    def test_get_and_extract_games_for_week(self):
        mock_client = MagicMock()
        mock_client.games.get_weekly_game_details.return_value = [
            _make_weekly_game_detail(),
            _make_weekly_game_detail(
                home_full_name="Dallas Cowboys",
                away_full_name="Cleveland Browns",
                slug="cle-at-dal-2024-reg-1",
            ),
        ]
        extractor = GameExtractor(nfl_client=mock_client)

        result = extractor.get_and_extract_games_for_week(
            season=2024, week=1, teams=["PIT"], replay_types=["Full Game"]
        )

        assert len(result) == 1
        assert result[0]["homeTeam"] == "Pittsburgh Steelers"

    def test_get_and_extract_games_for_week_all_teams(self):
        mock_client = MagicMock()
        mock_client.games.get_weekly_game_details.return_value = [
            _make_weekly_game_detail(),
            _make_weekly_game_detail(
                home_full_name="Dallas Cowboys",
                away_full_name="Cleveland Browns",
                slug="cle-at-dal-2024-reg-1",
            ),
        ]
        extractor = GameExtractor(nfl_client=mock_client)

        result = extractor.get_and_extract_games_for_week(
            season=2024, week=1, teams=None, replay_types=["Full Game"]
        )

        assert len(result) == 2

    def test_get_and_extract_games_for_week_calls_api(self):
        mock_client = MagicMock()
        mock_client.games.get_weekly_game_details.return_value = []
        extractor = GameExtractor(nfl_client=mock_client)

        extractor.get_and_extract_games_for_week(season=2024, week=5)

        mock_client.games.get_weekly_game_details.assert_called_once_with(
            season=2024, type_="REG", week=5, include_replays=True
        )


# --- MetadataWriter Tests ---


class TestMetadataWriter:
    def test_construct_metadata_for_game(self):
        namer = FileNamer()
        writer = MetadataWriter(destination_dir=Path("/tmp"), file_namer=namer)
        game = _make_game_dict()

        xml = writer.construct_metadata_for_game(
            game=game, replay_type="Full Game", ep_num=1
        )

        assert "<title>" in xml
        assert "2024 Week 1 - (Full Game) Atlanta Falcons at Pittsburgh Steelers" in xml
        assert "<season>2024</season>" in xml
        assert "<episode>1</episode>" in xml
        assert "<aired>2024-09-08</aired>" in xml

    def test_write_metadata_file(self, tmp_path):
        namer = FileNamer()
        writer = MetadataWriter(destination_dir=tmp_path, file_namer=namer)
        game = _make_game_dict()

        writer.write_metadata_file(game=game, replay_type="Full Game", ep_num=1)

        expected_stem = namer.construct_file_name(
            game=game, replay_type="Full Game", ep_num=1
        )
        nfo_file = tmp_path / f"{expected_stem}.nfo"
        assert nfo_file.exists()

        content = nfo_file.read_text()
        assert "<episodedetails>" in content
        assert "Atlanta Falcons" in content

    def test_write_metadata_file_uses_file_namer(self, tmp_path):
        """Verify MetadataWriter delegates to the injected FileNamer."""
        mock_namer = MagicMock()
        mock_namer.construct_file_name.return_value = "test_file_name"

        writer = MetadataWriter(destination_dir=tmp_path, file_namer=mock_namer)
        game = _make_game_dict()

        writer.write_metadata_file(game=game, replay_type="Full Game", ep_num=1)

        mock_namer.construct_file_name.assert_called_once_with(
            game=game, replay_type="Full Game", ep_num=1
        )
        assert (tmp_path / "test_file_name.nfo").exists()


# --- NFLWeeklyDownloader Composition Tests ---


class TestNFLWeeklyDownloaderComposition:
    @patch("griddy.nfl.GriddyNFL")
    def test_accepts_injected_file_namer(self, mock_griddy_cls, tmp_path):
        custom_namer = FileNamer()
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
            file_namer=custom_namer,
        )

        assert nwd.file_namer is custom_namer

    @patch("griddy.nfl.GriddyNFL")
    def test_accepts_injected_game_extractor(self, mock_griddy_cls, tmp_path):
        custom_extractor = GameExtractor(nfl_client=MagicMock())
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
            game_extractor=custom_extractor,
        )

        assert nwd.game_extractor is custom_extractor

    @patch("griddy.nfl.GriddyNFL")
    def test_accepts_injected_metadata_writer(self, mock_griddy_cls, tmp_path):
        custom_writer = MetadataWriter(destination_dir=tmp_path, file_namer=FileNamer())
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
            metadata_writer=custom_writer,
        )

        assert nwd.metadata_writer is custom_writer

    @patch("griddy.nfl.GriddyNFL")
    def test_creates_default_collaborators(self, mock_griddy_cls, tmp_path):
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
        )

        assert isinstance(nwd.file_namer, FileNamer)
        assert isinstance(nwd.game_extractor, GameExtractor)
        assert isinstance(nwd.metadata_writer, MetadataWriter)

    @patch("griddy.nfl.GriddyNFL")
    def test_default_game_extractor_uses_nfl_client(self, mock_griddy_cls, tmp_path):
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
        )

        assert nwd.game_extractor.nfl_client is nwd.nfl_client

    @patch("griddy.nfl.GriddyNFL")
    def test_default_metadata_writer_uses_file_namer(self, mock_griddy_cls, tmp_path):
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
        )

        assert nwd.metadata_writer.file_namer is nwd.file_namer

    @patch("griddy.nfl.GriddyNFL")
    def test_delegates_get_and_extract_to_game_extractor(
        self, mock_griddy_cls, tmp_path
    ):
        mock_extractor = MagicMock()
        mock_extractor.get_and_extract_games_for_week.return_value = []

        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
            game_extractor=mock_extractor,
        )

        nwd.get_and_extract_games_for_week(season=2024, week=1, teams=["PIT"])

        mock_extractor.get_and_extract_games_for_week.assert_called_once_with(
            season=2024, week=1, teams=["PIT"], replay_types=None
        )

    @patch("griddy.nfl.GriddyNFL")
    def test_no_longer_inherits_from_nfl_base_ie(self, mock_griddy_cls, tmp_path):
        """Verify NFLBaseIE is no longer in the MRO."""
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
        )

        class_names = [cls.__name__ for cls in type(nwd).__mro__]
        assert "NFLBaseIE" not in class_names

    @patch("griddy.nfl.GriddyNFL")
    def test_still_inherits_from_base_downloader(self, mock_griddy_cls, tmp_path):
        nwd = NFLWeeklyDownloader(
            firefox_profile_path="/fake/profile",
            destination_dir=tmp_path,
            nfl_auth={"accessToken": "t", "refreshToken": "r", "expiresIn": 3600},
        )

        assert isinstance(nwd, BaseDownloader)


# --- NFLShowDownloader Tests (preserved from original) ---


class TestNFLShowDownloader:
    def test_errors_initialized_once_as_empty_list(self, tmp_path):
        episode_file = tmp_path / "episodes.json"
        episode_file.write_text(json.dumps({"seasons": [["ep1", "ep2"]]}))

        cookie_file = tmp_path / "cookies.txt"
        cookie_file.touch()

        with patch("fbcm.nfl.MEDIA_BASE_DIR", str(tmp_path)):
            downloader = NFLShowDownloader(
                episode_list_path=episode_file,
                cookie_file_path=cookie_file,
                show_dir="test_show",
            )

        assert downloader.errors == []
        assert downloader.completed == []
        assert downloader.completed_seasons == []
