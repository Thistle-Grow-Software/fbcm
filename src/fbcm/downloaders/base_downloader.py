import logging
import os
from pathlib import Path

from ..constants import CONCURRENT_FRAGMENTS, THROTTLED_RATE_LIMIT

logger = logging.getLogger(__name__)


class BaseDownloader:
    """
    A wrapper around YoutubeDL that allows for download a list of generic URLs stored in a file.
    """

    def __init__(
        self,
        cookie_file_path: str | Path | None = None,
        destination_dir: str | Path | None = None,
        add_yt_opts: dict | None = None,
        browser: str = "firefox",
    ) -> None:
        """
        Construct the BaseDownloader and store specification information to be passed to ydl.

        :param cookie_file_path: A Netscape formatted .txt file containing cookies to be used for authentication.
        :type cookie_file_path: str | Path | None

        :param destination_dir: The directory downloaded files should be stored in. Can be a string or a Path object.
        :type destination_dir: str | Path | None

        :param add_yt_opts: A dict of options to pass along to YoutubeDL in addition to the base parameters used by
            fbdl. The values passed in this parameter will supersede any base parameters, and can be overriden when
            download_from_file is invoked.
        :type add_yt_opts: Dict

        :param browser: Lower case name of the browser cookies are being extracted from.
        :type browser: str
        """
        self.cookie_file_path = cookie_file_path
        self.base_yt_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": CONCURRENT_FRAGMENTS,
            "addmetadata": True,
            "throttledratelimit": THROTTLED_RATE_LIMIT,
            "embedsubs": True,
            "writesubs": True,
            "subtitleslangs": ["en"],
        }

        if self.cookie_file_path is not None:
            self.base_yt_opts["cookiesfrombrowser"] = (browser, self.cookie_file_path)

        if add_yt_opts:
            self.base_yt_opts.update(add_yt_opts)

        if destination_dir is None:
            destination_dir = os.getcwd()

        if isinstance(destination_dir, str):
            destination_dir = Path(destination_dir)

        self.destination_dir = destination_dir

    def download_from_file(
        self,
        input_file: Path,
        dlp_overrides: dict | None = None,
        output_file_name_template: str = "%(title)s.%(ext)s",
    ) -> None:
        """
        Use YoutubeDL to download the videos stored at each URL from input_file.

        :param input_file: The file where URLs are listed, one per line, to be downloaded.
        :type input_file: Path

        :param dlp_overrides: A dict storing YoutubeDL parameters to be used for this invocation of download_from_file
        :type dlp_overrides: Dict | None

        :param output_file_name_template: A string using Python's string formatting rules that will dictate the downloaded file's name. See yt-dlp docs for more.
        :type output_file_name_template: str
        :return:
        """
        logger.info(f"Downloading files from {input_file.name}")

        urls = input_file.read_text().splitlines()
        output_template = str(self.destination_dir / output_file_name_template)
        overridden_opts = {
            **self.base_yt_opts,
            "outtmpl": output_template,
        }

        if dlp_overrides:
            overridden_opts.update(dlp_overrides)

        from yt_dlp import YoutubeDL

        with YoutubeDL(params=overridden_opts) as ydl:
            ydl.download(urls)
