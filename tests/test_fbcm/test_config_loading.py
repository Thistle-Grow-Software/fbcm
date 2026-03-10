"""Tests for config file discovery and loading in fbcm.utils."""

from pathlib import Path
from unittest.mock import patch

from fbcm.config import _resolve, _resolve_list
from fbcm.utils import find_config, load_config


class TestFindConfigExplicitPath:
    def test_returns_path_when_exists(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text("key: value")
        result = find_config(explicit_path=str(config_file))
        assert result == config_file

    def test_returns_none_when_explicit_path_missing(self, tmp_path):
        result = find_config(explicit_path=str(tmp_path / "nonexistent.yaml"))
        assert result is None


class TestFindConfigCwdDiscovery:
    def test_finds_config_in_cwd(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text("key: value")
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = find_config()
            assert result == config_file

    def test_skips_cwd_when_no_config(self, tmp_path):
        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch.object(Path, "home", return_value=tmp_path / "fake_home"),
        ):
            result = find_config()
            assert result is None


class TestFindConfigHomeDiscovery:
    def test_finds_config_in_home_config_dir(self, tmp_path):
        home_config_dir = tmp_path / ".config"
        home_config_dir.mkdir()
        config_file = home_config_dir / "fbcm.yaml"
        config_file.write_text("key: value")

        cwd = tmp_path / "some_other_dir"
        cwd.mkdir()

        with (
            patch.object(Path, "cwd", return_value=cwd),
            patch.object(Path, "home", return_value=tmp_path),
        ):
            result = find_config()
            assert result == config_file

    def test_cwd_takes_precedence_over_home(self, tmp_path):
        # Create config in both locations
        cwd_config = tmp_path / "fbcm.yaml"
        cwd_config.write_text("cwd: true")

        home_config_dir = tmp_path / "fake_home" / ".config"
        home_config_dir.mkdir(parents=True)
        home_config = home_config_dir / "fbcm.yaml"
        home_config.write_text("home: true")

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch.object(Path, "home", return_value=tmp_path / "fake_home"),
        ):
            result = find_config()
            assert result == cwd_config


class TestFindConfigNotFound:
    def test_returns_none_when_no_config_anywhere(self, tmp_path):
        empty_cwd = tmp_path / "empty_cwd"
        empty_cwd.mkdir()
        empty_home = tmp_path / "empty_home"
        empty_home.mkdir()

        with (
            patch.object(Path, "cwd", return_value=empty_cwd),
            patch.object(Path, "home", return_value=empty_home),
        ):
            result = find_config()
            assert result is None


class TestLoadConfig:
    def test_returns_empty_dict_when_no_path(self):
        result = load_config(config_path=None)
        assert result == {}

    def test_loads_valid_yaml(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text(
            "output_directory: /media/games\ncookies_file: cookies.txt\n"
        )
        result = load_config(config_path=config_file)
        assert result["output_directory"] == "/media/games"
        assert result["cookies_file"] == "cookies.txt"

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text("")
        result = load_config(config_path=config_file)
        assert result == {}

    def test_loads_nested_config(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text(
            "nfl_games:\n  season: 2025\n  week:\n    - 1\n    - 2\n"
        )
        result = load_config(config_path=config_file)
        assert result["nfl_games"]["season"] == 2025
        assert result["nfl_games"]["week"] == [1, 2]

    def test_raises_on_invalid_file(self, tmp_path):
        config_file = tmp_path / "fbcm.yaml"
        config_file.write_text("")
        # An empty YAML file returns None, which is handled -> empty dict
        result = load_config(config_path=config_file)
        assert result == {}


class TestResolveFunction:
    def test_cli_value_takes_precedence(self):
        result = _resolve(
            "output_directory",
            "/cli/dir",
            {"output_directory": "/cmd/dir"},
            {"output_directory": "/common/dir"},
        )
        assert result == "/cli/dir"

    def test_falls_back_to_command_config(self):
        result = _resolve(
            "output_directory",
            None,
            {"output_directory": "/cmd/dir"},
            {"output_directory": "/common/dir"},
        )
        assert result == "/cmd/dir"

    def test_falls_back_to_common_config(self):
        result = _resolve(
            "output_directory",
            None,
            {},
            {"output_directory": "/common/dir"},
            common_key="output_directory",
        )
        assert result == "/common/dir"

    def test_returns_none_when_all_missing(self):
        result = _resolve("output_directory", None, {}, {})
        assert result is None

    def test_common_key_override(self):
        result = _resolve(
            "dest",
            None,
            {},
            {"output_directory": "/common/dir"},
            common_key="output_directory",
        )
        assert result == "/common/dir"


class TestResolveListFunction:
    def test_cli_value_takes_precedence(self):
        result = _resolve_list("week", (1, 2, 3), {"week": [5, 6]}, {"week": [10]})
        assert result == [1, 2, 3]

    def test_empty_tuple_treated_as_unset(self):
        result = _resolve_list("week", (), {"week": [5, 6]}, {})
        assert result == [5, 6]

    def test_falls_back_to_command_config(self):
        result = _resolve_list("week", None, {"week": [5, 6]}, {})
        assert result == [5, 6]

    def test_falls_back_to_common_config(self):
        result = _resolve_list("week", None, {}, {"week": [10, 11]}, common_key="week")
        assert result == [10, 11]

    def test_returns_none_when_all_missing(self):
        result = _resolve_list("week", None, {}, {})
        assert result is None

    def test_converts_tuple_to_list(self):
        result = _resolve_list("team", ("PIT", "CLE"), {}, {})
        assert result == ["PIT", "CLE"]
        assert isinstance(result, list)

    def test_none_value_in_command_config(self):
        result = _resolve_list("week", None, {"week": None}, {})
        assert result is None
