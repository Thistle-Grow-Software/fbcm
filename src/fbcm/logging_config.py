import logging
import sys


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
) -> None:
    """
    Configure the fbcm package logger with console and optional file output.

    :param level: The logging level (e.g. logging.DEBUG, logging.INFO).
    :param log_file: Optional path to a log file. If provided, logs are written
        to both the console and the file.
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    root_logger = logging.getLogger("fbcm")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
