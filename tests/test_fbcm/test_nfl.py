import json
from unittest.mock import patch

from fbcm.nfl import NFLShowDownloader


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
