# Backward-compatibility re-exports.
# New code should import from the dedicated modules directly.
from .downloaders import BaseDownloader  # noqa: F401

# is_bowl_game and transform_file_name now live in file_namer
from .file_namer import is_bowl_game, transform_file_name  # noqa: F401
from .file_operations import (  # noqa: F401
    FileOperationsUtil,
    get_max_episode_number_in_dir,
)
from .metadata import (  # noqa: F401
    MetaDataCreator,
    convert_cfl_playoff_name_to_int,
    convert_nfl_playoff_name_to_int,
    convert_ufl_playoff_name_to_int,
    get_week_int_as_string,
    is_playoff_week,
)
