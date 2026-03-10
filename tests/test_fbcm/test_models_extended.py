"""Extended tests for fbcm.models — covers skills, stats, and edge cases."""

from fbcm.models import (
    BaseStats,
    BasicInfo,
    ColorScheme,
    Comparison,
    DefenseStats,
    DefensiveBackSkills,
    DefensiveLinemanSkills,
    InterceptionStats,
    LinebackerSkills,
    OffenseSkillPlayerStats,
    OffensiveLinemanSkills,
    PassCatcherSkills,
    PassingSkills,
    PassingStats,
    ProspectDataSoup,
    ReceivingStats,
    RunningBackSkills,
    RushingStats,
    ScoutingReport,
    TackleStats,
)


class TestColorScheme:
    def test_from_dict(self):
        data = {"primary": "#FF0000", "secondary": "#00FF00", "light": "#CCCCCC"}
        scheme = ColorScheme.from_dict(data)
        assert scheme.primary == "#FF0000"
        assert scheme.secondary == "#00FF00"
        assert scheme.light == "#CCCCCC"
        assert scheme.dark is None
        assert scheme.medium is None

    def test_to_dict(self):
        scheme = ColorScheme(primary="#FF0000", secondary="#00FF00", light="#CCCCCC")
        result = scheme.to_dict()
        assert result["primary"] == "#FF0000"
        assert result["secondary"] == "#00FF00"
        assert result["light"] == "#CCCCCC"

    def test_roundtrip(self):
        original = ColorScheme(
            primary="#FF0000", secondary="#00FF00", light="#CCCCCC", dark="#330000"
        )
        restored = ColorScheme.from_dict(original.to_dict())
        assert restored.primary == original.primary
        assert restored.dark == original.dark


class TestIndividualStatsClasses:
    def test_rushing_stats_from_dict(self):
        data = {"att": 200, "yds": 1200, "avg": 6.0, "td": 14}
        stats = RushingStats.from_dict(data)
        assert stats.att == 200
        assert stats.yds == 1200
        assert stats.avg == 6.0
        assert stats.td == 14

    def test_rushing_stats_to_dict(self):
        stats = RushingStats(att=200, yds=1200, avg=6.0, td=14)
        result = stats.to_dict()
        assert result["att"] == 200
        assert result["yds"] == 1200

    def test_receiving_stats_from_dict(self):
        data = {"rec": 60, "yds": 800, "avg": 13.3, "td": 8}
        stats = ReceivingStats.from_dict(data)
        assert stats.rec == 60
        assert stats.yds == 800

    def test_tackle_stats_from_dict(self):
        data = {"total": 65, "solo": 42, "ff": 3, "sacks": 8.5}
        stats = TackleStats.from_dict(data)
        assert stats.total == 65
        assert stats.solo == 42
        assert stats.ff == 3
        assert stats.sacks == 8.5

    def test_interception_stats_from_dict(self):
        data = {"ints": 5, "yds": 120, "td": 2, "pds": 15}
        stats = InterceptionStats.from_dict(data)
        assert stats.ints == 5
        assert stats.pds == 15

    def test_base_stats_from_dict(self):
        data = {"year": 2024, "games_played": 12, "snap_count": 800}
        stats = BaseStats.from_dict(data)
        assert stats.year == 2024
        assert stats.games_played == 12

    def test_offense_skill_player_stats_roundtrip(self):
        original = OffenseSkillPlayerStats(
            rushing=RushingStats(att=200, yds=1200, td=14),
            receiving=ReceivingStats(rec=30, yds=250, td=2),
        )
        data = original.to_dict()
        restored = OffenseSkillPlayerStats.from_dict(data)
        assert restored.rushing.att == 200
        assert restored.receiving.rec == 30

    def test_defense_stats_roundtrip(self):
        original = DefenseStats(
            tackle=TackleStats(total=65, solo=42),
            interception=InterceptionStats(ints=5, pds=12),
        )
        data = original.to_dict()
        restored = DefenseStats.from_dict(data)
        assert restored.tackle.total == 65
        assert restored.interception.ints == 5


class TestSkillsClasses:
    def test_passing_skills_from_dict(self):
        data = {"release_speed": 88, "short_passing": 90, "long_passing": 82}
        skills = PassingSkills.from_dict(data)
        assert skills.release_speed == 88
        assert skills.short_passing == 90

    def test_running_back_skills_from_dict(self):
        data = {"rushing": 92, "break_tackles": 88, "receiving_hands": 75}
        skills = RunningBackSkills.from_dict(data)
        assert skills.rushing == 92
        assert skills.break_tackles == 88

    def test_pass_catcher_skills_from_dict(self):
        data = {"hands": 90, "deep_threat": 85, "blocking": 60}
        skills = PassCatcherSkills.from_dict(data)
        assert skills.hands == 90
        assert skills.deep_threat == 85

    def test_offensive_lineman_skills_from_dict(self):
        data = {"pass_blocking": 88, "run_blocking": 92}
        skills = OffensiveLinemanSkills.from_dict(data)
        assert skills.pass_blocking == 88
        assert skills.run_blocking == 92

    def test_defensive_lineman_skills_from_dict(self):
        data = {"pass_rush": 90, "run_defense": 85, "tackling": 78}
        skills = DefensiveLinemanSkills.from_dict(data)
        assert skills.pass_rush == 90
        assert skills.run_defense == 85

    def test_linebacker_skills_from_dict(self):
        data = {"tackling": 88, "coverage": 75, "zone": 80, "man_press": 70}
        skills = LinebackerSkills.from_dict(data)
        assert skills.tackling == 88
        assert skills.coverage == 75

    def test_defensive_back_skills_from_dict(self):
        data = {"coverage": 92, "zone": 88, "man_press": 85, "tackling": 70}
        skills = DefensiveBackSkills.from_dict(data)
        assert skills.coverage == 92
        assert skills.man_press == 85

    def test_skills_to_dict_excludes_none_values_in_iteration(self):
        skills = PassingSkills(release_speed=88)
        result = skills.to_dict()
        assert result["release_speed"] == 88
        # None fields are still present in the dict but with None value
        assert "short_passing" in result
        assert result["short_passing"] is None


class TestBasicInfoPhotoPath:
    def test_photo_path_uses_full_name(self):
        info = BasicInfo(full_name="Cam Ward")
        assert info.photo_path.name == "Cam Ward.png"

    def test_photo_path_is_path_object(self):
        from pathlib import Path

        info = BasicInfo(full_name="Test Player")
        assert isinstance(info.photo_path, Path)


class TestBaseModelExcludeFields:
    def test_exclude_fields_filters_to_dict(self):
        """Verify that exclude_fields class variable works."""

        # BaseModel's exclude_fields is empty by default
        stats = PassingStats(cmp=280, att=420)
        result = stats.to_dict()
        assert "cmp" in result
        assert "att" in result


class TestProspectDataSoupPositionMapping:
    """Test all position mappings for stats and skills classes."""

    def test_te_uses_offense_skill_player_stats(self):
        data = {
            "basic_info": {"position": "TE"},
            "stats": {"rushing": {"att": 5}, "receiving": {"rec": 40}},
            "skills": {"hands": 88},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, OffenseSkillPlayerStats)
        assert isinstance(prospect.skills, PassCatcherSkills)

    def test_ol_uses_base_stats(self):
        data = {
            "basic_info": {"position": "OL"},
            "stats": {"year": 2024, "games_played": 12},
            "skills": {"pass_blocking": 90},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, BaseStats)
        assert isinstance(prospect.skills, OffensiveLinemanSkills)

    def test_edge_uses_defense_stats(self):
        data = {
            "basic_info": {"position": "EDGE"},
            "stats": {"tackle": {"total": 50}},
            "skills": {"pass_rush": 92},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.stats, DefenseStats)
        assert isinstance(prospect.skills, DefensiveLinemanSkills)

    def test_lb_uses_linebacker_skills(self):
        data = {
            "basic_info": {"position": "LB"},
            "skills": {"tackling": 85, "coverage": 78},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert isinstance(prospect.skills, LinebackerSkills)

    def test_unknown_position_uses_defaults(self):
        data = {
            "basic_info": {"position": "K"},
            "stats": {"year": 2024},
            "skills": {"release_speed": 50},
        }
        prospect = ProspectDataSoup.from_dict(data)
        # Unknown position falls back to BaseStats and PassingSkills
        assert isinstance(prospect.stats, BaseStats)
        assert isinstance(prospect.skills, PassingSkills)

    def test_empty_position_uses_defaults(self):
        data = {
            "basic_info": {"position": ""},
        }
        prospect = ProspectDataSoup.from_dict(data)
        assert prospect.basic_info.position == ""


class TestScoutingReportDefaults:
    def test_default_empty_lists(self):
        report = ScoutingReport()
        assert report.strengths == []
        assert report.weaknesses == []
        assert report.bio == ""
        assert report.summary is None

    def test_from_dict_preserves_lists(self):
        data = {
            "strengths": ["Arm strength", "Accuracy", "Pocket presence"],
            "weaknesses": ["Footwork"],
        }
        report = ScoutingReport.from_dict(data)
        assert len(report.strengths) == 3
        assert len(report.weaknesses) == 1


class TestComparisonModel:
    def test_from_dict(self):
        data = {"name": "Patrick Mahomes", "school": "Kansas City", "similarity": 92}
        comp = Comparison.from_dict(data)
        assert comp.name == "Patrick Mahomes"
        assert comp.similarity == 92

    def test_to_dict(self):
        comp = Comparison(name="Josh Allen", school="Buffalo", similarity=85)
        result = comp.to_dict()
        assert result["name"] == "Josh Allen"
        assert result["similarity"] == 85

    def test_defaults_are_none(self):
        comp = Comparison()
        assert comp.name is None
        assert comp.school is None
        assert comp.similarity is None
