import pytest

from fbcm.file_namer import (
    FileNamer,
    NCAAGameFileNamer,
    NFLGameFileNamer,
    SeriesFileNamer,
)


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
        "replays": {},
    }
    game.update(overrides)
    return game


# --- FileNamer (base class) Tests ---


class TestFileNamer:
    def test_format_stem_default_padding(self):
        namer = FileNamer()
        result = namer.format_stem(
            prefix="NFL Full Game",
            season=2024,
            episode=1,
            details="2024_Wk01_ATL_at_PIT",
        )
        assert result == "NFL Full Game - s2024e001 - 2024_Wk01_ATL_at_PIT"

    def test_format_stem_custom_padding(self):
        namer = FileNamer()
        result = namer.format_stem(
            prefix="NCAA", season=2024, episode=5, details="details", episode_padding=2
        )
        assert result == "NCAA - s2024e05 - details"

    def test_format_stem_string_season_and_episode(self):
        namer = FileNamer()
        result = namer.format_stem(
            prefix="Test", season="2024", episode="042", details="stuff"
        )
        assert result == "Test - s2024e042 - stuff"

    def test_construct_output_path(self, tmp_path):
        namer = FileNamer(base_directory=tmp_path)
        result = namer.construct_output_path("my_file", extension="mp4")
        assert result == tmp_path / "my_file.mp4"

    def test_construct_output_path_custom_extension(self, tmp_path):
        namer = FileNamer(base_directory=tmp_path)
        result = namer.construct_output_path("my_file", extension="nfo")
        assert result == tmp_path / "my_file.nfo"

    def test_construct_output_path_raises_without_base_directory(self):
        namer = FileNamer()
        with pytest.raises(ValueError, match="base_directory must be set"):
            namer.construct_output_path("my_file")

    def test_construct_output_path_with_yt_dlp_extension(self, tmp_path):
        namer = FileNamer(base_directory=tmp_path)
        result = namer.construct_output_path("my_file", extension="%(ext)s")
        assert result == tmp_path / "my_file.%(ext)s"


# --- NFLGameFileNamer Tests ---


class TestNFLGameFileNamer:
    def test_construct_file_name_basic(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=1)

        assert result == "NFL Full Game - s2024e001 - 2024_Wk01_ATL_at_PIT"

    def test_construct_file_name_neutral_site(self):
        namer = NFLGameFileNamer()
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
        namer = NFLGameFileNamer()
        game = _make_game_dict(awayTeam="New York Jets", homeTeam="Miami Dolphins")
        result = namer.construct_file_name(
            game=game, replay_type="Condensed Game", ep_num=5
        )

        assert "NYJ" in result
        assert "Condensed Game" in result

    def test_construct_file_name_giants_home(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict(homeTeam="New York Giants", awayTeam="Dallas Cowboys")
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=3)

        assert "NYG" in result

    def test_construct_file_name_chargers_away(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict(
            awayTeam="Los Angeles Chargers", homeTeam="Denver Broncos"
        )
        result = namer.construct_file_name(game=game, replay_type="All-22", ep_num=10)

        assert "LAC" in result

    def test_construct_file_name_rams_home(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict(homeTeam="Los Angeles Rams", awayTeam="Seattle Seahawks")
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=2)

        assert "LAR" in result

    def test_construct_file_name_episode_padding(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=5)

        assert "e005" in result

    def test_construct_file_name_large_episode_number(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(
            game=game, replay_type="Full Game", ep_num=150
        )

        assert "e150" in result

    def test_construct_file_name_week_padding(self):
        namer = NFLGameFileNamer()
        game = _make_game_dict(week=8)
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=1)

        assert "Wk08" in result

    def test_inherits_from_file_namer(self):
        namer = NFLGameFileNamer()
        assert isinstance(namer, FileNamer)

    def test_uses_format_stem(self):
        """Verify construct_file_name delegates to the base format_stem method."""
        namer = NFLGameFileNamer()
        game = _make_game_dict()
        result = namer.construct_file_name(game=game, replay_type="Full Game", ep_num=1)

        # The result should match the format_stem pattern
        assert " - s2024e001 - " in result

    def test_construct_output_path_inherited(self, tmp_path):
        namer = NFLGameFileNamer(base_directory=tmp_path)
        game = _make_game_dict()
        file_name = namer.construct_file_name(
            game=game, replay_type="Full Game", ep_num=1
        )
        output_path = namer.construct_output_path(file_name, extension="mp4")

        assert output_path.parent == tmp_path
        assert output_path.name.endswith(".mp4")


# --- NCAAGameFileNamer Tests ---


class TestNCAAGameFileNamer:
    def test_construct_file_name_with_bowl(self):
        namer = NCAAGameFileNamer()
        fake_file = "2024 - Game 13 2024-12-07 SEC Championship UGA vs Texas"
        result = namer.construct_file_name(orig_file_stem=fake_file)

        assert result == "NCAA - s2024e13 - 2024_Gm13SECChampionship_Georgia_vs_Texas"

    def test_construct_file_name_regular_game(self):
        namer = NCAAGameFileNamer()
        fake_file = "2024 - Game 01 2024-09-01 Random Info Team_A at Team_B"
        result = namer.construct_file_name(orig_file_stem=fake_file)

        assert result.startswith("NCAA - s2024e01")
        assert "at" in result

    def test_inherits_from_file_namer(self):
        namer = NCAAGameFileNamer()
        assert isinstance(namer, FileNamer)


# --- SeriesFileNamer Tests ---


class TestSeriesFileNamer:
    def test_construct_file_name_basic(self):
        namer = SeriesFileNamer(series_name="NFL Games")
        result = namer.construct_file_name(
            season=2024, episode=5, episode_name="Some Episode"
        )

        assert result == "NFL Games - s2024e005 - Some Episode"

    def test_construct_file_name_with_file_stem(self):
        namer = SeriesFileNamer(series_name="NFL Games")
        result = namer.construct_file_name(
            season=2024, episode=1, episode_name="2024_Wk01_PIT_at_ATL"
        )

        assert result == "NFL Games - s2024e001 - 2024_Wk01_PIT_at_ATL"

    def test_construct_file_name_string_episode(self):
        namer = SeriesFileNamer(series_name="NFL Games")
        result = namer.construct_file_name(
            season=2024, episode="05", episode_name="Week 5 Game"
        )

        assert "e005" in result

    def test_inherits_from_file_namer(self):
        namer = SeriesFileNamer(series_name="Test")
        assert isinstance(namer, FileNamer)

    def test_has_series_name(self):
        namer = SeriesFileNamer(series_name="NFL Games")
        assert namer.series_name == "NFL Games"

    def test_with_base_directory(self, tmp_path):
        namer = SeriesFileNamer(series_name="NFL Games", base_directory=tmp_path)
        file_stem = namer.construct_file_name(
            season=2024, episode=1, episode_name="test"
        )
        output_path = namer.construct_output_path(file_stem)

        assert output_path.parent == tmp_path
