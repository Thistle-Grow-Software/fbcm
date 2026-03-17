"""Tests for pure helper functions in fbcm.docx.word_gen."""

from pathlib import Path

import pytest
from griddy.draftbuzz.models import RatingsAndRankings

from fbcm.docx.word_gen import (
    get_photo_path,
    get_primary_position,
    get_recruiting_str,
    skill_bar,
)


class TestGetPrimaryPosition:
    def test_single_position(self):
        assert get_primary_position("QB") == "QB"

    def test_multi_position(self):
        assert get_primary_position("DL/EDGE") == "DL"

    def test_multi_position_with_spaces(self):
        assert get_primary_position(" WR / TE ") == "WR"

    def test_empty_string(self):
        assert get_primary_position("") == ""

    def test_lowercase_uppercased(self):
        assert get_primary_position("qb") == "QB"


class TestSkillBar:
    def test_zero_percent(self):
        result = skill_bar(0)
        assert result == "░" * 10

    def test_hundred_percent(self):
        result = skill_bar(100)
        assert result == "█" * 10

    def test_fifty_percent(self):
        result = skill_bar(50)
        assert result == "█" * 5 + "░" * 5

    def test_always_ten_chars(self):
        for pct in [0, 10, 25, 50, 75, 90, 100]:
            assert len(skill_bar(pct)) == 10

    def test_rounding(self):
        # 75 / 10 = 7.5, rounds to 8
        result = skill_bar(75)
        assert result.count("█") == 8


class TestSchoolColors:
    """Tests for SchoolColors helper methods (blend, darken, hex_to_rgb)."""

    @pytest.fixture
    def school_colors(self, tmp_path):
        import json

        from fbcm.docx.word_gen import SchoolColors

        colors_data = {
            "FBS": {
                "ACC": {
                    "Miami": {
                        "primary": "#F47321",
                        "secondary": "#005030",
                        "light": "#FDE8D3",
                    }
                }
            }
        }
        colors_file = tmp_path / "colors.json"
        colors_file.write_text(json.dumps(colors_data))
        return SchoolColors(colors_file=str(colors_file))

    def test_blend_colors_equal_ratio(self, school_colors):
        result = school_colors.blend_colors("#000000", "#ffffff", 0.5)
        # Each channel: 0 + (255 - 0) * 0.5 = 127
        assert result == "7f7f7f"

    def test_blend_colors_zero_ratio(self, school_colors):
        result = school_colors.blend_colors("#ff0000", "#0000ff", 0.0)
        assert result == "ff0000"

    def test_blend_colors_full_ratio(self, school_colors):
        result = school_colors.blend_colors("#ff0000", "#0000ff", 1.0)
        assert result == "0000ff"

    def test_darken_color_black_stays_black(self, school_colors):
        result = school_colors.darken_color("#000000", 0.3)
        assert result == "000000"

    def test_darken_color_white(self, school_colors):
        result = school_colors.darken_color("#ffffff", 0.5)
        # Each channel: 255 * 0.5 = 127
        assert result == "7f7f7f"

    def test_darken_color_strips_hash(self, school_colors):
        result = school_colors.darken_color("#FF0000", 0.0)
        assert result == "ff0000"

    def test_hex_to_rgb(self, school_colors):
        from docx.shared import RGBColor

        result = school_colors.hex_to_rgb("#FF8000")
        assert result == RGBColor(255, 128, 0)

    def test_hex_to_rgb_without_hash(self, school_colors):
        from docx.shared import RGBColor

        result = school_colors.hex_to_rgb("FF8000")
        assert result == RGBColor(255, 128, 0)

    def test_get_school_colors(self, school_colors):
        colors = school_colors.get_school_colors("Miami")
        assert colors.primary == "#F47321"
        assert colors.dark is not None
        assert colors.medium is not None
        assert colors.primary_rgb is not None
        assert colors.light_rgb is not None

    def test_get_school_colors_case_insensitive(self, school_colors):
        colors = school_colors.get_school_colors("MIAMI")
        assert colors.primary == "#F47321"

    def test_normalize_flattens_divisions(self, school_colors):
        assert "miami" in school_colors.color_data


class TestGetPhotoPath:
    def test_returns_path_with_name(self):
        result = get_photo_path("Cam Ward")
        assert isinstance(result, Path)
        assert result.name == "Cam Ward.png"

    def test_includes_photo_base_dir(self):
        result = get_photo_path("Test Player")
        assert str(result).endswith("Test Player.png")


class TestGetRecruitingStr:
    def test_all_outlets(self):
        ratings = RatingsAndRankings(espn=95.0, rtg_247=99.0, rivals=5.8)
        result = get_recruiting_str(ratings)
        assert "ESPN: 95" in result
        assert "247: 99" in result
        assert "Rivals: 5.8" in result
        assert "\u2022" in result

    def test_partial_outlets(self):
        ratings = RatingsAndRankings(espn=95.0)
        result = get_recruiting_str(ratings)
        assert result == "ESPN: 95"

    def test_no_outlets(self):
        ratings = RatingsAndRankings()
        assert get_recruiting_str(ratings) == ""
