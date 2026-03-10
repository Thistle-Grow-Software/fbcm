"""Tests for fbcm.metadata.MetaDataCreator."""

import pytest

from fbcm.metadata import MetaDataCreator


class TestMetaDataCreatorCreateTitleString:
    @pytest.fixture
    def creator(self, tmp_path):
        return MetaDataCreator(
            base_dir=tmp_path,
            game_dates={"2024": {"1": "2024-09-08", "5": "2024-10-06"}},
            league="nfl",
        )

    def test_regular_week(self, creator):
        result = creator._create_title_string(
            "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL"
        )
        assert "2024 Week 1" in result
        assert "Pittsburgh" in result
        assert "Atlanta" in result

    def test_preserves_at_vs(self, creator):
        result = creator._create_title_string(
            "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL"
        )
        assert "at" in result

    def test_super_bowl(self, creator):
        creator_2021 = MetaDataCreator(
            base_dir=creator.base_dir,
            game_dates={"2024": {"22": "2025-02-09"}},
            league="nfl",
        )
        result = creator_2021._create_title_string(
            "NFL Full Game - s2024e270 - 2024_SBLVIII_KC_vs_SF"
        )
        assert "Super Bowl" in result

    def test_raises_on_unknown_team(self, creator):
        with pytest.raises(ValueError, match="Could not find team"):
            creator._create_title_string(
                "NFL Full Game - s2024e001 - 2024_Wk01_FAKE_at_ATL"
            )


class TestMetaDataCreatorConstructMetadataXml:
    def test_produces_valid_xml(self, tmp_path):
        creator = MetaDataCreator(
            base_dir=tmp_path,
            game_dates={"2024": {"1": "2024-09-08"}},
        )
        xml = creator.construct_metadata_xml_for_game(
            "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL"
        )
        assert "<episodedetails>" in xml
        assert "<title>" in xml
        assert "<season>2024</season>" in xml
        assert "<episode>1</episode>" in xml
        assert "<aired>2024-09-08</aired>" in xml


class TestMetaDataCreatorCreateNfoForSeason:
    def test_creates_nfo_files(self, tmp_path):
        season_dir = tmp_path / "Season 2024"
        season_dir.mkdir()
        (season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.mp4").touch()

        creator = MetaDataCreator(
            base_dir=tmp_path,
            game_dates={"2024": {"1": "2024-09-08"}},
        )
        creator.create_nfo_for_season(year=2024)

        nfo = season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.nfo"
        assert nfo.exists()
        content = nfo.read_text()
        assert "<title>" in content

    def test_skips_existing_nfo_without_overwrite(self, tmp_path):
        season_dir = tmp_path / "Season 2024"
        season_dir.mkdir()
        (season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.mp4").touch()
        nfo = season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.nfo"
        nfo.write_text("existing content")

        creator = MetaDataCreator(
            base_dir=tmp_path,
            game_dates={"2024": {"1": "2024-09-08"}},
        )
        creator.create_nfo_for_season(year=2024, overwrite=False)

        assert nfo.read_text() == "existing content"

    def test_overwrites_existing_nfo_when_flag_set(self, tmp_path):
        season_dir = tmp_path / "Season 2024"
        season_dir.mkdir()
        (season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.mp4").touch()
        nfo = season_dir / "NFL Full Game - s2024e001 - 2024_Wk01_PIT_at_ATL.nfo"
        nfo.write_text("old content")

        creator = MetaDataCreator(
            base_dir=tmp_path,
            game_dates={"2024": {"1": "2024-09-08"}},
        )
        creator.create_nfo_for_season(year=2024, overwrite=True)

        assert nfo.read_text() != "old content"
        assert "<episodedetails>" in nfo.read_text()

    def test_raises_on_missing_season_dir(self, tmp_path):
        creator = MetaDataCreator(base_dir=tmp_path, game_dates={})
        with pytest.raises(FileNotFoundError):
            creator.create_nfo_for_season(year=2099)


class TestMetaDataCreatorRenameFilesForSeason:
    def test_renames_files(self, tmp_path):
        season_dir = tmp_path / "Season 2024"
        season_dir.mkdir()
        original = season_dir / "2024_Wk01_PIT_at_ATL.mp4"
        original.touch()

        creator = MetaDataCreator(base_dir=tmp_path, game_dates={})
        creator.rename_files_for_season(year=2024, series_name="NFL Games")

        renamed_files = list(season_dir.glob("NFL Games*"))
        assert len(renamed_files) == 1
        assert "s2024e" in renamed_files[0].name
