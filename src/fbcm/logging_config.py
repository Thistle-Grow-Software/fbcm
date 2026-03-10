import json
import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import LoggingConfig

TEXT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, DATE_FORMAT),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    logging_config: LoggingConfig | None = None,
) -> None:
    """Configure the fbcm package logger.

    When a ``LoggingConfig`` is provided it takes precedence and drives all
    behaviour (level, format, output targets, rotation, per-module levels).
    The ``level`` and ``log_file`` parameters are kept for backward
    compatibility with existing call-sites.

    :param level: The logging level (used only when *logging_config* is None).
    :param log_file: Optional log file path (used only when *logging_config* is None).
    :param logging_config: Full logging configuration dataclass.
    """
    root_logger = logging.getLogger("fbcm")
    root_logger.handlers.clear()

    if logging_config is not None:
        _apply_config(root_logger, logging_config)
    else:
        _apply_simple(root_logger, level, log_file)


def _build_formatter(log_format: str) -> logging.Formatter:
    if log_format == "json":
        return JsonFormatter()
    return logging.Formatter(fmt=TEXT_FORMAT, datefmt=DATE_FORMAT)


def _apply_config(root_logger: logging.Logger, cfg: LoggingConfig) -> None:
    root_logger.setLevel(cfg.numeric_level)
    formatter = _build_formatter(cfg.log_format)

    if cfg.output in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if cfg.output in ("file", "both") and cfg.log_file:
        file_handler = RotatingFileHandler(
            cfg.log_file,
            maxBytes=cfg.max_file_size,
            backupCount=cfg.backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    for module_name, level_str in cfg.module_levels.items():
        full_name = (
            module_name if module_name.startswith("fbcm") else f"fbcm.{module_name}"
        )
        module_logger = logging.getLogger(full_name)
        module_logger.setLevel(getattr(logging, level_str))


def _apply_simple(
    root_logger: logging.Logger, level: int, log_file: str | None
) -> None:
    """Backward-compatible simple setup (console + optional file)."""
    root_logger.setLevel(level)
    formatter = logging.Formatter(fmt=TEXT_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
