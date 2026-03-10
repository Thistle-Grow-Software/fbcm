import logging
import re
from pathlib import Path
from typing import Any

from .mappings import ABBREVIATION_MAP

logger = logging.getLogger(__name__)


def get_max_episode_number_in_dir(directory: Path) -> int:
    season_ep_reg = r"[sS]\d+[eE]\d+"

    max_ep = -1
    for f in directory.iterdir():
        if f.name.endswith(".nfo"):
            continue

        matches = re.findall(season_ep_reg, f.name)

        if not matches:
            raise ValueError(
                f"No appropriate sXXeXX string found in file name: {f.name}"
            )

        season_episode = matches[0]
        episode_num = int(season_episode.lower().split("e")[-1])
        if episode_num > max_ep:
            max_ep = episode_num

    return max_ep


class FileOperationsUtil:
    """
    A utility class for file operations such as renaming, converting, etc.
    """

    def __init__(
        self,
        directory_path: str | Path,
        pretend: bool = False,
        verbose: bool = False,
    ) -> None:
        """
        Create a util object, storing the directory we will be working in.

        Directory path is managed via a :class:`~fbcm.file_namer.FileNamer`
        instance so that output path construction is centralized.

        :param directory_path: The directory containing the files on which we will be operating.
        :type directory_path: str | Path
        :param pretend: If True, only simulate operations.
        :type pretend: bool
        :param verbose: If True, enable verbose logging.
        :type verbose: bool
        """
        from .file_namer import FileNamer

        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        self.file_namer = FileNamer(base_directory=directory_path)
        self.directory_path = directory_path
        self.pretend = pretend
        self.verbose = verbose

    def _log_var(self, name: str, var: Any) -> None:
        """
        Log the variable's name and its string representation.

        :param name: (Typically) the name of the object being logged.
        :type name: str
        :param var: The object to log.
        :type var: Any
        """

        if self.verbose:
            logger.debug(f"Variable: {name}")
            logger.debug(f"Value: {var}")

    def _construct_mp4_title(self, file_stem: str) -> str:
        """
        Given a file stem create a pretty string for display in media client

        :param file_stem: The file's name without file extension. Matches pattern YYYY_WkXX_ABC_at|vs_XYZ
        :type file_stem: str

        :return: The pretty string used to display in UIs
        :rtype: str
        """
        self._log_var("Base Name", file_stem)

        name_parts = file_stem.split("_")
        self._log_var("Name Parts", name_parts)

        year = name_parts[0]
        self._log_var("Year", year)

        away_city = ABBREVIATION_MAP[name_parts[2]]
        home_city = ABBREVIATION_MAP[name_parts[4]]
        at_vs = "vs" if "SB" in name_parts[1] else "at"

        self._log_var("@ or vs", at_vs)

        return f"{year} {name_parts[1]} - {away_city} {at_vs} {home_city}"

    def update_mp4_title_from_filename(self, file_obj: Path) -> None:
        """
        Using information stored in a mp4 file's name, update the title stored in its metadata

        :param file_obj: The file to update.
        :type file_obj: Path
        """
        if self.pretend:
            logger.info("Pretend flag was passed. Will not save updates.")

        logger.info(f"Updating metadata for games in {self.directory_path}")

        logger.info(f"Working on {file_obj.name}")

        from mutagen.mp4 import MP4

        try:
            audio = MP4(file_obj)
            audio["\xa9nam"] = self._construct_mp4_title(file_stem=file_obj.stem)

            if not self.pretend:
                logger.info("Saving file.")
                audio.save()

            logger.info(f"Updated title for '{file_obj.name}' to: '{audio['\xa9nam']}'")
        except Exception as e:
            logger.error(f"Error processing '{file_obj.name}': {e}")
            raise e

    def iter_and_update_children(self) -> None:
        """
        Update all mp4 files in the current directory and all its children.
        """
        for item in self.directory_path.rglob("*.mp4"):
            self.update_mp4_title_from_filename(item)

    def convert_formats(
        self, orig_format: str = "mkv", new_format: str = "mp4", delete: bool = False
    ) -> list[str]:
        """
        Use ffmpeg to convert video files in self.directory_path from one format to another.

        :param orig_format: Convert all videos of this format
        :type orig_format: str

        :param new_format: The new format to store the videos in.
        :type new_format: str

        :param delete: If True, delete the original files of the old format.

        :return: List of file names (stem only) that were successfully converted.
        :rtype: List[str]
        """

        import ffmpeg

        successfully_converted = []
        for mkv_file in self.directory_path.rglob(f"*.{orig_format}"):
            orig_stem = mkv_file.stem

            stream = ffmpeg.input(str(mkv_file))
            output_path = str(mkv_file.with_suffix(f".{new_format}"))
            stream = ffmpeg.output(
                stream, output_path, vcodec="copy", acodec="copy", format="mp4"
            )
            if self.pretend:
                log_str = f"Would convert {mkv_file} to {output_path}."
                if delete:
                    log_str += f"\nWould delete {mkv_file} as well."
                logger.info(log_str)
                successfully_converted.append(orig_stem)
            else:
                logger.info(f"Converting {mkv_file} to {output_path}")
                ffmpeg.run(stream)
                successfully_converted.append(orig_stem)
                if delete:
                    logger.info(f"Deleting {mkv_file}.")
                    mkv_file.unlink()

        return successfully_converted

    def rename_files(self, series_name: str, replace: bool = False) -> None:
        """
        A specialized method to rename TV series episode files from the format
            XYY-<episode_name>.mp4 to <series_name> - sXXeYY - <episode_name>.mp4
            Where X is the episode season, and YY is the episode number within that season.

        :param series_name: Name of the TV series we should rename files for.
        :type series_name: str
        :param replace: If True, overwrite any files which happen to exist with the
            target name already.
        """
        # Regular expression to match the xyy-<Episode Name>.mp4 format
        pattern = r"^(\d{1})(\d{2,3})-(.+)\.mp4$"

        # Iterate through all subdirectories
        for file_path in self.directory_path.rglob("*.mp4"):
            # Check if file matches the expected pattern
            match = re.match(pattern, file_path.name)
            if match:
                season = match.group(1)  # Extract season number (x)
                episode = match.group(2)  # Extract episode number (yy)
                episode_name = match.group(3)  # Extract episode name

                new_filename = f"{series_name} - s{season.zfill(2)}e{episode.zfill(2)} - {episode_name}.mp4"
                new_file_path = file_path.with_name(new_filename)
                delete_ = new_file_path.exists()

                if self.pretend:
                    if delete_:
                        logger.info(
                            f"{new_filename} already exists, would be replaced."
                        )
                    logger.info(
                        f"Would rename {file_path.name} to {new_filename}."
                        f" --pretend was passed, so we will not attempt the operation."
                    )
                else:
                    if delete_ and not replace:
                        raise FileExistsError(
                            f"File {new_filename} already exists and replace is False"
                        )

                    logger.info(f"Renaming {file_path.name} to {new_file_path.name}")
                    file_path.replace(new_file_path)
                    logger.info("Success.")
