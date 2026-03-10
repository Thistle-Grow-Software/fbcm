import json
import logging
from logging.handlers import RotatingFileHandler

from fbcm.config import LoggingConfig
from fbcm.logging_config import JsonFormatter, setup_logging


class TestSetupLogging:
    def teardown_method(self):
        """Clean up the fbcm logger after each test."""
        fbcm_logger = logging.getLogger("fbcm")
        fbcm_logger.handlers.clear()
        fbcm_logger.setLevel(logging.WARNING)

    def test_setup_logging_creates_console_handler(self):
        setup_logging()
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 1
        assert isinstance(fbcm_logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_sets_info_level_by_default(self):
        setup_logging()
        fbcm_logger = logging.getLogger("fbcm")

        assert fbcm_logger.level == logging.INFO

    def test_setup_logging_sets_custom_level(self):
        setup_logging(level=logging.DEBUG)
        fbcm_logger = logging.getLogger("fbcm")

        assert fbcm_logger.level == logging.DEBUG

    def test_setup_logging_adds_file_handler(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        setup_logging(log_file=log_file)
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 2
        handler_types = [type(h) for h in fbcm_logger.handlers]
        assert logging.StreamHandler in handler_types
        assert logging.FileHandler in handler_types

    def test_setup_logging_file_handler_writes(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        test_logger = logging.getLogger("fbcm.test")
        test_logger.info("test message")

        # Flush handlers
        for handler in logging.getLogger("fbcm").handlers:
            handler.flush()

        log_content = log_file.read_text()
        assert "test message" in log_content

    def test_setup_logging_clears_existing_handlers(self):
        setup_logging()
        setup_logging()
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 1

    def test_setup_logging_formatter_includes_timestamp(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        test_logger = logging.getLogger("fbcm.test")
        test_logger.info("timestamp check")

        for handler in logging.getLogger("fbcm").handlers:
            handler.flush()

        log_content = log_file.read_text()
        # Format: "YYYY-MM-DD HH:MM:SS [LEVEL] name: message"
        assert "[INFO]" in log_content
        assert "fbcm.test" in log_content

    def test_child_loggers_propagate_to_fbcm(self):
        setup_logging(level=logging.DEBUG)
        child_logger = logging.getLogger("fbcm.base")

        # Child loggers should propagate to parent
        assert child_logger.parent.name == "fbcm"


class TestSetupLoggingWithConfig:
    def teardown_method(self):
        fbcm_logger = logging.getLogger("fbcm")
        fbcm_logger.handlers.clear()
        fbcm_logger.setLevel(logging.WARNING)
        # Clean up any module-level loggers we set
        for name in ["fbcm.nfl", "fbcm.draft_buzz", "fbcm.file_operations"]:
            mod_logger = logging.getLogger(name)
            mod_logger.setLevel(logging.NOTSET)

    def test_config_sets_level(self):
        cfg = LoggingConfig(level="WARNING")
        setup_logging(logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        assert fbcm_logger.level == logging.WARNING

    def test_config_console_only(self):
        cfg = LoggingConfig(level="INFO", output="console")
        setup_logging(logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 1
        assert isinstance(fbcm_logger.handlers[0], logging.StreamHandler)

    def test_config_file_only(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        cfg = LoggingConfig(level="INFO", output="file", log_file=log_file)
        setup_logging(logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 1
        assert isinstance(fbcm_logger.handlers[0], RotatingFileHandler)

    def test_config_both_outputs(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        cfg = LoggingConfig(level="INFO", output="both", log_file=log_file)
        setup_logging(logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        assert len(fbcm_logger.handlers) == 2
        handler_types = [type(h) for h in fbcm_logger.handlers]
        assert logging.StreamHandler in handler_types
        assert RotatingFileHandler in handler_types

    def test_config_json_format(self, tmp_path):
        log_file = tmp_path / "test.log"
        cfg = LoggingConfig(
            level="INFO", output="both", log_file=str(log_file), log_format="json"
        )
        setup_logging(logging_config=cfg)
        test_logger = logging.getLogger("fbcm.test")
        test_logger.info("json test message")

        for handler in logging.getLogger("fbcm").handlers:
            handler.flush()

        log_content = log_file.read_text().strip()
        parsed = json.loads(log_content)
        assert parsed["level"] == "INFO"
        assert parsed["module"] == "fbcm.test"
        assert parsed["message"] == "json test message"
        assert "timestamp" in parsed

    def test_config_text_format(self, tmp_path):
        log_file = tmp_path / "test.log"
        cfg = LoggingConfig(
            level="INFO", output="both", log_file=str(log_file), log_format="text"
        )
        setup_logging(logging_config=cfg)
        test_logger = logging.getLogger("fbcm.test")
        test_logger.info("text test message")

        for handler in logging.getLogger("fbcm").handlers:
            handler.flush()

        log_content = log_file.read_text()
        assert "[INFO]" in log_content
        assert "fbcm.test" in log_content
        assert "text test message" in log_content

    def test_config_module_levels(self):
        cfg = LoggingConfig(
            level="INFO",
            module_levels={"nfl": "DEBUG", "draft_buzz": "WARNING"},
        )
        setup_logging(logging_config=cfg)

        nfl_logger = logging.getLogger("fbcm.nfl")
        draft_buzz_logger = logging.getLogger("fbcm.draft_buzz")

        assert nfl_logger.level == logging.DEBUG
        assert draft_buzz_logger.level == logging.WARNING

    def test_config_module_levels_with_fbcm_prefix(self):
        cfg = LoggingConfig(
            level="INFO",
            module_levels={"fbcm.nfl": "ERROR"},
        )
        setup_logging(logging_config=cfg)

        nfl_logger = logging.getLogger("fbcm.nfl")
        assert nfl_logger.level == logging.ERROR

    def test_config_rotating_file_handler_params(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        cfg = LoggingConfig(
            level="INFO",
            output="file",
            log_file=log_file,
            max_file_size=5_000_000,
            backup_count=3,
        )
        setup_logging(logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        handler = fbcm_logger.handlers[0]
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 5_000_000
        assert handler.backupCount == 3

    def test_config_overrides_simple_params(self):
        """LoggingConfig takes precedence over level/log_file params."""
        cfg = LoggingConfig(level="ERROR")
        setup_logging(level=logging.DEBUG, logging_config=cfg)
        fbcm_logger = logging.getLogger("fbcm")

        assert fbcm_logger.level == logging.ERROR


class TestJsonFormatter:
    def test_formats_as_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="fbcm.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["module"] == "fbcm.test"
        assert parsed["message"] == "test message"
        assert "timestamp" in parsed
        assert "exception" not in parsed

    def test_includes_exception_info(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="fbcm.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error occurred",
            args=None,
            exc_info=exc_info,
        )
        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "ERROR"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_no_exception_key_when_no_exc_info(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="fbcm.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="no error",
            args=None,
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" not in parsed
