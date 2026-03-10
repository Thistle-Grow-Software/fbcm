"""Tests for fbcm.models — dataclass serialization and deserialization."""

from fbcm.models import (
    BasicInfo,
    Comparison,
    DefenseStats,
    InterceptionStats,
    OffenseSkillPlayerStats,
    PassCatcherSkills,
    PassingSkills,
    PassingStats,
    ProspectDataSoup,
    RatingsAndRankings,
    RunningBackSkills,
    RushingStats,
    ScoutingReport,
    TackleStats,
)


class TestBaseModelToDict:
    def test_simple_dataclass_to_dict(self):
        stats = PassingStats(cmp=280, att=420, cmp_pct=66.7, yds=3800, td=32)
        result = stats.to_dict()
        assert result["cmp"] == 280
        assert result["att"] == 420
        assert result["td"] == 32

    def test_to_dict_includes_none_fields(self):
        stats = PassingStats(cmp=280)
        result = stats.to_dict()
        assert "att" in result
        assert result["att"] is None

    def test_to_dict_with_nested_dataclass(self):
        defense = DefenseStats(
            tackle=TackleStats(total=65, solo=42),
            interception=InterceptionStats(ints=2, td=1),
        )
        result = defense.to_dict()
        assert result["tackle"]["total"] == 65
        assert result["interception"]["ints"] == 2


class TestBaseModelFromDict:
    def test_simple_from_dict(self):
        data = {"cmp": 280, "att": 420, "cmp_pct": 66.7, "yds": 3800}
        stats = PassingStats.from_dict(data)
        assert stats.cmp == 280
        assert stats.att == 420
        assert stats.cmp_pct == 66.7

    def test_from_dict_with_none_value(self):
        data = {"cmp": 280, "att": None}
        stats = PassingStats.from_dict(data)
        assert stats.cmp == 280
        assert stats.att is None

    def test_from_dict_ignores_unknown_keys(self):
        data = {"cmp": 280, "unknown_field": "should be ignored"}
        stats = PassingStats.from_dict(data)
        assert stats.cmp == 280
        assert not hasattr(stats, "unknown_field")

    def test_from_dict_returns_none_for_none_input(self):
        result = PassingStats.from_dict(None)
        assert result is None

    def test_from_dict_with_nested_dataclass(self):
        data = {
            "tackle": {"total": 65, "solo": 42, "ff": 3, "sacks": 8.5},
            "interception": {"ints": 2, "yds": 35, "td": 1, "pds": 10},
        }
        defense = DefenseStats.from_dict(data)
        assert isinstance(defense.tackle, TackleStats)
        assert defense.tackle.total == 65
        assert isinstance(defense.interception, InterceptionStats)
        assert defense.interception.ints == 2

    def test_from_dict_with_list_of_dataclasses(self):
        data = {
            "bio": "Test bio",
            "strengths": ["Strong arm", "Quick release"],
            "weaknesses": ["Footwork"],
        }
        report = ScoutingReport.from_dict(data)
        assert report.bio == "Test bio"
        assert report.strengths == ["Strong arm", "Quick release"]
        assert report.weaknesses == ["Footwork"]


class TestConvertValue:
    def test_handles_union_with_none(self):
        # BasicInfo.photo_url is str | None
        data = {"first_name": "Cam", "photo_url": "http://example.com/photo.png"}
        info = BasicInfo.from_dict(data)
        assert info.photo_url == "http://example.com/photo.png"

    def test_handles_list_type(self):
        data = {"strengths": ["arm strength", "accuracy"], "bio": "test"}
        report = ScoutingReport.from_dict(data)
        assert len(report.strengths) == 2

    def test_handles_nested_in_union(self):
        # OffenseSkillPlayerStats has rushing: RushingStats | None
        data = {
            "rushing": {"att": 200, "yds": 1200, "avg": 6.0, "td": 14},
            "receiving": None,
        }
        stats = OffenseSkillPlayerStats.from_dict(data)
        assert isinstance(stats.rushing, RushingStats)
        assert stats.rushing.att == 200
        assert stats.receiving is None


class TestPassingStatsGet:
    def test_get_basic_field(self):
        stats = PassingStats(cmp=280, att=420, yds=3800)
        assert stats.get("cmp") == 280

    def test_get_rtg_maps_to_qb_rtg(self):
        stats = PassingStats(qb_rtg=155.2)
        assert stats.get("rtg") == 155.2

    def test_get_int_maps_to_ints(self):
        stats = PassingStats(ints=8)
        assert stats.get("int") == 8

    def test_get_pct_replacement(self):
        stats = PassingStats(cmp_pct=66.7)
        assert stats.get("cmp%") == 66.7


class TestRatingsAndRankings:
    def test_get_recruiting_str_all_outlets(self):
        ratings = RatingsAndRankings(espn=95, rtg_247=99, rivals=5.8)
        result = ratings.get_recruiting_str()
        assert "ESPN: 95" in result
        assert "247: 99" in result
        assert "Rivals: 5.8" in result
        assert "  •  " in result

    def test_get_recruiting_str_partial(self):
        ratings = RatingsAndRankings(espn=95)
        result = ratings.get_recruiting_str()
        assert result == "ESPN: 95"

    def test_get_recruiting_str_empty(self):
        ratings = RatingsAndRankings()
        assert ratings.get_recruiting_str() == ""


class TestProspectDataSoupFromDict:
    def test_qb_uses_passing_stats(self):
        data = {
            "basic_info": {"first_name": "Cam", "last_name": "Ward", "position": "QB"},
            "stats": {"cmp": 280, "att": 420, "yds": 3800, "td": 32},
            "skills": {"release_speed": 88, "short_passing": 90},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, PassingStats)
        assert isinstance(prospect.skills, PassingSkills)
        assert prospect.stats.cmp == 280

    def test_rb_uses_offense_skill_player_stats(self):
        data = {
            "basic_info": {"position": "RB"},
            "stats": {
                "rushing": {"att": 200, "yds": 1200},
                "receiving": {"rec": 30, "yds": 250},
            },
            "skills": {"rushing": 92, "break_tackles": 88},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, OffenseSkillPlayerStats)
        assert isinstance(prospect.skills, RunningBackSkills)

    def test_wr_uses_pass_catcher_skills(self):
        data = {
            "basic_info": {"position": "WR"},
            "skills": {"hands": 90, "deep_threat": 85},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.skills, PassCatcherSkills)

    def test_db_uses_defense_stats(self):
        data = {
            "basic_info": {"position": "DB"},
            "stats": {
                "tackle": {"total": 45, "solo": 30},
                "interception": {"ints": 5, "pds": 12},
            },
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, DefenseStats)

    def test_multi_position_uses_primary(self):
        data = {
            "basic_info": {"position": "DL/EDGE"},
            "stats": {
                "tackle": {"total": 50},
                "interception": {"ints": 0},
            },
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, DefenseStats)

    def test_comparisons_deserialized(self):
        data = {
            "basic_info": {"position": "QB"},
            "comparisons": [
                {"name": "Patrick Mahomes", "school": "Kansas City", "similarity": 92},
                {"name": "Josh Allen", "school": "Buffalo", "similarity": 85},
            ],
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert len(prospect.comparisons) == 2
        assert isinstance(prospect.comparisons[0], Comparison)
        assert prospect.comparisons[0].name == "Patrick Mahomes"

    def test_scouting_report_deserialized(self):
        data = {
            "basic_info": {"position": "QB"},
            "scouting_report": {
                "bio": "Elite prospect",
                "strengths": ["Arm strength"],
                "weaknesses": ["Footwork"],
                "summary": "High upside",
            },
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.scouting_report, ScoutingReport)
        assert prospect.scouting_report.bio == "Elite prospect"

    def test_none_input_returns_none(self):
        result = ProspectDataSoup.from_dict(None)
        assert result is None

    def test_missing_optional_fields(self):
        data = {"basic_info": {"position": "QB"}}
        prospect = ProspectDataSoup.from_dict(data)
        assert prospect.basic_info is not None
        assert prospect.stats is None
        assert prospect.skills is None
        assert prospect.comparisons is None
        assert prospect.scouting_report is None

    def test_roundtrip_to_dict_from_dict(self):
        original = ProspectDataSoup(
            basic_info=BasicInfo(
                first_name="Cam", last_name="Ward", position="QB", college="Miami"
            ),
            ratings=RatingsAndRankings(overall_rating=92.5, espn=95),
            skills=PassingSkills(release_speed=88, short_passing=90),
            comparisons=[
                Comparison(name="Mahomes", school="KC", similarity=92),
            ],
            stats=PassingStats(cmp=280, att=420, yds=3800),
            scouting_report=ScoutingReport(
                bio="Test", strengths=["Arm"], weaknesses=["Feet"]
            ),
        )
        data = original.to_dict()
        restored = ProspectDataSoup.from_dict(data)

        assert restored.basic_info.first_name == "Cam"
        assert restored.ratings.overall_rating == 92.5
        assert restored.stats.cmp == 280
        assert len(restored.comparisons) == 1
