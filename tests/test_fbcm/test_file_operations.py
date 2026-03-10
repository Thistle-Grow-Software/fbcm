"""Tests for fbcm.file_operations — file conversion, renaming, metadata updates."""

import pytest

from fbcm.file_operations import FileOperationsUtil, get_max_episode_number_in_dir


class TestGetMaxEpisodeNumberInDir:
    def test_single_file(self, tmp_path):
        (tmp_path / "NFL Full Game - s2024e005 - 2024_Wk01_ATL_at_PIT.mp4").touch()
        assert get_max_episode_number_in_dir(tmp_path) == 5

    def test_multiple_files_returns_max(self, tmp_path):
        (tmp_path / "NFL Full Game - s2024e001 - game1.mp4").touch()
        (tmp_path / "NFL Full Game - s2024e010 - game2.mp4").touch()
        (tmp_path / "NFL Full Game - s2024e003 - game3.mp4").touch()
        assert get_max_episode_number_in_dir(tmp_path) == 10

    def test_skips_nfo_files(self, tmp_path):
        (tmp_path / "NFL Full Game - s2024e005 - game.mp4").touch()
        (tmp_path / "NFL Full Game - s2024e099 - game.nfo").touch()
        assert get_max_episode_number_in_dir(tmp_path) == 5

    def test_case_insensitive(self, tmp_path):
        (tmp_path / "NFL Full Game - S2024E007 - game.mp4").touch()
        assert get_max_episode_number_in_dir(tmp_path) == 7

    def test_raises_on_no_match(self, tmp_path):
        (tmp_path / "no_episode_pattern.mp4").touch()
        with pytest.raises(ValueError, match="No appropriate sXXeXX string"):
            get_max_episode_number_in_dir(tmp_path)


class TestFileOperationsUtilConstructMp4Title:
    @pytest.fixture
    def util(self, tmp_path):
        return FileOperationsUtil(directory_path=tmp_path)

    def test_regular_game(self, util):
        result = util._construct_mp4_title("2024_Wk01_PIT_at_ATL")
        assert result == "2024 Wk01 - Pittsburgh at Atlanta"

    def test_super_bowl_uses_vs(self, util):
        result = util._construct_mp4_title("2024_SB_KC_at_SF")
        assert "vs" in result

    def test_regular_week_uses_at(self, util):
        result = util._construct_mp4_title("2024_Wk05_BUF_at_MIA")
        assert "at" in result


class TestFileOperationsUtilRenameFiles:
    def test_renames_matching_files(self, tmp_path):
        # Create files matching pattern: xyy-<name>.mp4
        (tmp_path / "101-Pilot Episode.mp4").touch()
        (tmp_path / "102-Second Episode.mp4").touch()

        util = FileOperationsUtil(directory_path=tmp_path)
        util.rename_files(series_name="My Show")

        files = sorted(f.name for f in tmp_path.glob("*.mp4"))
        assert files == [
            "My Show - s01e01 - Pilot Episode.mp4",
            "My Show - s01e02 - Second Episode.mp4",
        ]

    def test_pretend_does_not_rename(self, tmp_path):
        (tmp_path / "101-Pilot.mp4").touch()

        util = FileOperationsUtil(directory_path=tmp_path, pretend=True)
        util.rename_files(series_name="My Show")

        assert (tmp_path / "101-Pilot.mp4").exists()
        assert not (tmp_path / "My Show - s01e01 - Pilot.mp4").exists()

    def test_raises_on_existing_file_without_replace(self, tmp_path):
        (tmp_path / "101-Pilot.mp4").touch()
        (tmp_path / "My Show - s01e01 - Pilot.mp4").touch()

        util = FileOperationsUtil(directory_path=tmp_path)
        with pytest.raises(FileExistsError):
            util.rename_files(series_name="My Show", replace=False)

    def test_replace_overwrites_existing(self, tmp_path):
        (tmp_path / "101-Pilot.mp4").touch()
        (tmp_path / "My Show - s01e01 - Pilot.mp4").touch()

        util = FileOperationsUtil(directory_path=tmp_path)
        util.rename_files(series_name="My Show", replace=True)

        assert (tmp_path / "My Show - s01e01 - Pilot.mp4").exists()

    def test_ignores_non_matching_files(self, tmp_path):
        (tmp_path / "random_video.mp4").touch()
        (tmp_path / "101-Pilot.mp4").touch()

        util = FileOperationsUtil(directory_path=tmp_path)
        util.rename_files(series_name="My Show")

        assert (tmp_path / "random_video.mp4").exists()
        assert (tmp_path / "My Show - s01e01 - Pilot.mp4").exists()


class TestFileOperationsUtilConvertFormats:
    def test_pretend_does_not_convert(self, tmp_path):
        (tmp_path / "video.mkv").write_bytes(b"fake mkv")

        util = FileOperationsUtil(directory_path=tmp_path, pretend=True)
        result = util.convert_formats(orig_format="mkv", new_format="mp4")

        assert result == ["video"]
        assert not (tmp_path / "video.mp4").exists()
        assert (tmp_path / "video.mkv").exists()
