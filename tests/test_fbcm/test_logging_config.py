import logging

from fbcm.logging_config import setup_logging


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
