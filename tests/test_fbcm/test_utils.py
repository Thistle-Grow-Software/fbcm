from fbcm.utils import generate_episode_metadata_xml


class TestGenerateEpisodeMetadataXml:
    def test_generates_correct_xml(self):
        result = generate_episode_metadata_xml(
            title="2025 Week 2 - Cleveland at Baltimore",
            season="2025",
            episode="18",
            aired="2025-09-14",
        )
        assert result == (
            "<episodedetails>\n"
            "\t<title>2025 Week 2 - Cleveland at Baltimore</title>\n"
            "\t<season>2025</season>\n"
            "\t<episode>18</episode>\n"
            "\t<aired>2025-09-14</aired>\n"
            "</episodedetails>"
        )

    def test_works_with_integer_season_and_episode(self):
        result = generate_episode_metadata_xml(
            title="2024 Week 1 - Pittsburgh at Atlanta",
            season=2024,
            episode=1,
            aired="2024-09-08",
        )
        assert result == (
            "<episodedetails>\n"
            "\t<title>2024 Week 1 - Pittsburgh at Atlanta</title>\n"
            "\t<season>2024</season>\n"
            "\t<episode>1</episode>\n"
            "\t<aired>2024-09-08</aired>\n"
            "</episodedetails>"
        )

    def test_works_with_replay_type_in_title(self):
        result = generate_episode_metadata_xml(
            title="2024 Week 5 - (Full Game) Steelers at Cowboys",
            season=2024,
            episode=42,
            aired="2024-10-06",
        )
        assert "<title>2024 Week 5 - (Full Game) Steelers at Cowboys</title>" in result
