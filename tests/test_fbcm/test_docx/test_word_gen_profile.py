"""Tests for WordDocGenerator prospect profile generation using SDK models."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from griddy.draftbuzz.models import (
    BasicInfo,
    Comparison,
    DefenseStats,
    InterceptionStats,
    OffenseSkillPlayerStats,
    PassingSkills,
    PassingStats,
    ProspectProfile,
    RatingsAndRankings,
    ReceivingStats,
    RunningBackSkills,
    RushingStats,
    ScoutingReport,
    TackleStats,
)

from fbcm.docx.word_gen import WordDocGenerator


def _make_colors_file(tmp_path):
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
    return str(colors_file)


@pytest.fixture
def colors_file(tmp_path):
    return _make_colors_file(tmp_path)


def _make_full_prospect(**overrides):
    """Build a complete ProspectProfile suitable for full document generation."""
    defaults = dict(
        basic_info=BasicInfo(
            first_name="Cam",
            last_name="Ward",
            full_name="Cam Ward",
            position="QB",
            college="Miami",
            class_="Senior",
            jersey="#1",
            play_style="Dual Threat",
            draft_year="2026",
            height="6-2",
            weight="220",
            forty="4.65",
            age="23",
            hometown="West Columbia, TX",
            photo_url="https://example.com/photo.png",
        ),
        ratings=RatingsAndRankings(
            overall_rating=92.5,
            opposition_rating=78,
            espn=95.0,
            rtg_247=99.0,
            rivals=5.8,
            draft_projection="Top 5 Pick",
            overall_rank=3,
            position_rank="1",
            avg_overall_rank=5.2,
            avg_position_rank=2.1,
        ),
        skills=PassingSkills(
            release_speed=88,
            short_passing=90,
            medium_passing=85,
            long_passing=82,
            rush_scramble=78,
        ),
        comparisons=[
            Comparison(name="Patrick Mahomes", school="Kansas City", similarity=92),
            Comparison(name="Josh Allen", school="Buffalo", similarity=85),
        ],
        stats=[
            PassingStats(
                year=2025,
                games_played=13,
                snap_count=850,
                cmp=280,
                att=420,
                cmp_pct=66.7,
                yds=3800,
                td=32,
                ints=8,
                sack=15,
                qb_rtg=155.2,
            )
        ],
        scouting_report=ScoutingReport(
            bio="Draft Profile: Bio Elite quarterback prospect with dual-threat ability.",
            strengths=["Elite arm strength", "Quick release", "Pocket awareness"],
            weaknesses=["Footwork under pressure", "Holds ball too long"],
            summary="Scouting Report: Summary A top-tier prospect with franchise quarterback potential.",
        ),
    )
    defaults.update(overrides)
    return ProspectProfile(**defaults)


class TestSetProspectContext:
    def test_sets_active_stats_from_first_element(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )
        stats = [
            PassingStats(year=2025, cmp=280),
            PassingStats(year=2024, cmp=200),
        ]
        prospect = _make_full_prospect(stats=stats)
        gen._set_prospect_context(prospect)

        assert gen._active_stats is not None
        assert gen._active_stats.cmp == 280

    def test_sets_active_stats_none_when_empty(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )
        prospect = _make_full_prospect(stats=[])
        gen._set_prospect_context(prospect)

        assert gen._active_stats is None

    def test_sets_active_stats_none_when_stats_is_none(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )
        prospect = _make_full_prospect(stats=None)
        gen._set_prospect_context(prospect)

        assert gen._active_stats is None

    def test_sets_school_colors(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )
        prospect = _make_full_prospect()
        gen._set_prospect_context(prospect)

        assert gen.colors is not None
        assert gen.colors.primary == "#F47321"


class TestAddProspect:
    def test_adds_page_break_for_second_prospect(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )
        prospect = _make_full_prospect()

        with patch.object(gen, "_gen_prospect_profile"):
            gen.add_prospect(prospect)
            assert gen._prospect_count == 1
            assert gen._last_prospect_name == "Cam Ward"

            gen.add_prospect(prospect)
            assert gen._prospect_count == 2

    def test_increments_prospect_count(self, tmp_path, colors_file):
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path),
            colors_path=colors_file,
        )

        with patch.object(gen, "_gen_prospect_profile"):
            gen.add_prospect(_make_full_prospect())
            gen.add_prospect(_make_full_prospect())
            gen.add_prospect(_make_full_prospect())

        assert gen._prospect_count == 3


class TestGenProspectProfile:
    """Integration tests for full prospect profile document generation."""

    def _make_photo(self, tmp_path, name="Cam Ward"):
        """Create a tiny valid PNG so add_picture doesn't fail."""
        from PIL import Image

        photo_dir = Path(tmp_path / "player_photos")
        photo_dir.mkdir(exist_ok=True)
        photo_path = photo_dir / f"{name}.png"
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        img.save(str(photo_path), "PNG")
        return photo_path

    def test_generates_qb_profile_document(self, tmp_path, colors_file):
        self._make_photo(tmp_path)
        prospect = _make_full_prospect()

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_qb.docx")

        doc_path = tmp_path / "test_qb.docx"
        assert doc_path.exists()
        assert doc_path.stat().st_size > 0

    def test_generates_rb_profile_document(self, tmp_path, colors_file):
        self._make_photo(tmp_path, "Ashton Jeanty")

        prospect = _make_full_prospect(
            basic_info=BasicInfo(
                full_name="Ashton Jeanty",
                position="RB",
                college="Miami",
                class_="Junior",
                jersey="#2",
                play_style="Power Back",
                height="5-9",
                weight="215",
                forty="4.45",
                hometown="Somewhere, FL",
            ),
            skills=RunningBackSkills(
                rushing=92,
                break_tackles=88,
                receiving_hands=75,
                pass_blocking=60,
                run_blocking=65,
            ),
            stats=[
                OffenseSkillPlayerStats(
                    year=2025,
                    rushing=RushingStats(att=200, yds=1200, avg=6.0, td=14),
                    receiving=ReceivingStats(rec=30, yds=250, avg=8.3, td=2),
                )
            ],
        )

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_rb.docx")

        assert (tmp_path / "test_rb.docx").exists()

    def test_generates_profile_with_no_stats(self, tmp_path, colors_file):
        """OL prospects have no stats — should render the 'no stats' message."""
        self._make_photo(tmp_path, "Big OL Guy")

        prospect = _make_full_prospect(
            basic_info=BasicInfo(
                full_name="Big OL Guy",
                position="OL",
                college="Miami",
                class_="Senior",
                jersey="#75",
                play_style="Mauler",
                height="6-5",
                weight="315",
                forty="5.20",
                hometown="Dallas, TX",
            ),
            stats=[],
            skills=None,
        )

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            # Skills is None, so _gen_skills_and_comps would fail.
            # We test the stats bar specifically.
            gen._set_prospect_context(prospect)
            gen._gen_stats_bar()

    def test_generates_profile_with_no_comparisons(self, tmp_path, colors_file):
        self._make_photo(tmp_path)
        prospect = _make_full_prospect(comparisons=None)

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_no_comps.docx")

        assert (tmp_path / "test_no_comps.docx").exists()

    def test_generates_profile_with_no_scouting_report(self, tmp_path, colors_file):
        self._make_photo(tmp_path)
        prospect = _make_full_prospect(scouting_report=None)

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_no_scouting.docx")

        assert (tmp_path / "test_no_scouting.docx").exists()

    def test_generates_profile_with_empty_scouting_report(self, tmp_path, colors_file):
        self._make_photo(tmp_path)
        prospect = _make_full_prospect(
            scouting_report=ScoutingReport(
                bio=None, strengths=None, weaknesses=None, summary=None
            )
        )

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_empty_scouting.docx")

        assert (tmp_path / "test_empty_scouting.docx").exists()

    def test_constructor_with_prospect_calls_add_prospect(self, tmp_path, colors_file):
        self._make_photo(tmp_path)
        prospect = _make_full_prospect()

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
                prospect=prospect,
            )

        assert gen._prospect_count == 1
        assert gen._last_prospect_name == "Cam Ward"

    def test_defense_stats_profile(self, tmp_path, colors_file):
        self._make_photo(tmp_path, "Edge Rusher")

        from griddy.draftbuzz.models import DefensiveLinemanSkills

        prospect = _make_full_prospect(
            basic_info=BasicInfo(
                full_name="Edge Rusher",
                position="DL/EDGE",
                college="Miami",
                class_="Senior",
                jersey="#99",
                play_style="Speed Rusher",
                height="6-4",
                weight="255",
                forty="4.55",
                hometown="Atlanta, GA",
            ),
            skills=DefensiveLinemanSkills(
                tackling=80, pass_rush=92, run_defense=75, coverage=60
            ),
            stats=[
                DefenseStats(
                    year=2025,
                    tackle=TackleStats(total=65, solo=42, ff=3, sacks=8.5),
                    interception=InterceptionStats(ints=0, yds=0, td=0, pds=5),
                )
            ],
        )

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(prospect)
            gen.generate_complete_document(filename="test_dl.docx")

        assert (tmp_path / "test_dl.docx").exists()

    def test_multiple_prospects_in_one_document(self, tmp_path, colors_file):
        self._make_photo(tmp_path, "Cam Ward")
        self._make_photo(tmp_path, "Player Two")

        p1 = _make_full_prospect()
        p2 = _make_full_prospect(
            basic_info=BasicInfo(
                full_name="Player Two",
                position="QB",
                college="Miami",
                class_="Junior",
                jersey="#5",
                play_style="Pro Style",
                height="6-3",
                weight="225",
                forty="4.70",
                hometown="Houston, TX",
            ),
        )

        with patch(
            "fbcm.docx.word_gen.PHOTO_BASE_DIR", str(tmp_path / "player_photos")
        ):
            gen = WordDocGenerator(
                output_path=str(tmp_path),
                ring_image_base_dir=str(tmp_path),
                colors_path=colors_file,
            )
            gen.add_prospect(p1)
            gen.add_prospect(p2)
            gen.generate_complete_document(filename="multi.docx")

        assert (tmp_path / "multi.docx").exists()
        assert gen._prospect_count == 2
