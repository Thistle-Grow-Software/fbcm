from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Error as PlaywrightError

from fbcm.browser_retry import (
    RECOVERABLE_ERROR_PHRASES,
    BrowserRetryHandler,
    is_recoverable_browser_error,
)


class TestIsRecoverableBrowserError:
    def test_target_closed_is_recoverable(self):
        error = PlaywrightError("Target closed")
        assert is_recoverable_browser_error(error) is True

    def test_browser_has_been_closed_is_recoverable(self):
        error = PlaywrightError("browser has been closed")
        assert is_recoverable_browser_error(error) is True

    def test_case_insensitive_matching(self):
        error = PlaywrightError("TARGET CLOSED unexpectedly")
        assert is_recoverable_browser_error(error) is True

    def test_non_recoverable_error(self):
        error = PlaywrightError("Element not found")
        assert is_recoverable_browser_error(error) is False

    def test_timeout_is_not_recoverable(self):
        error = PlaywrightError("Timeout 30000ms exceeded")
        assert is_recoverable_browser_error(error) is False


class TestBrowserRetryHandler:
    def _make_handler(self, max_retries=3, retry_delay=0.0):
        playwright = MagicMock()
        mock_browser = MagicMock()
        launch_browser = MagicMock(return_value=mock_browser)
        handler = BrowserRetryHandler(
            playwright=playwright,
            launch_browser=launch_browser,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        return handler, launch_browser, mock_browser

    def test_successful_operation_returns_result_and_same_browser(self):
        handler, _, _ = self._make_handler()
        browser = MagicMock()
        operation = MagicMock(return_value="success")

        result, returned_browser = handler.execute(operation, browser)

        assert result == "success"
        assert returned_browser is browser
        operation.assert_called_once_with(browser)

    def test_non_recoverable_error_raises_immediately(self):
        handler, launch_browser, _ = self._make_handler()
        browser = MagicMock()
        operation = MagicMock(side_effect=PlaywrightError("Element not found"))

        with pytest.raises(PlaywrightError, match="Element not found"):
            handler.execute(operation, browser)

        operation.assert_called_once()
        launch_browser.assert_not_called()

    @patch("fbcm.browser_retry.time.sleep")
    def test_recoverable_error_triggers_retry_and_relaunch(self, mock_sleep):
        handler, launch_browser, new_browser = self._make_handler()
        original_browser = MagicMock()

        operation = MagicMock(
            side_effect=[PlaywrightError("Target closed"), "recovered"]
        )

        result, returned_browser = handler.execute(operation, original_browser)

        assert result == "recovered"
        assert returned_browser is new_browser
        assert operation.call_count == 2
        original_browser.close.assert_called_once()
        launch_browser.assert_called_once()
        mock_sleep.assert_called_once_with(0.0)

    @patch("fbcm.browser_retry.time.sleep")
    def test_all_retries_exhausted_raises_last_error(self, mock_sleep):
        handler, launch_browser, _ = self._make_handler(max_retries=2)
        browser = MagicMock()

        error1 = PlaywrightError("Target closed")
        error2 = PlaywrightError("browser has been closed")
        operation = MagicMock(side_effect=[error1, error2])

        with pytest.raises(PlaywrightError, match="browser has been closed"):
            handler.execute(operation, browser)

        assert operation.call_count == 2
        assert launch_browser.call_count == 2

    @patch("fbcm.browser_retry.time.sleep")
    def test_browser_close_failure_is_ignored(self, mock_sleep):
        handler, launch_browser, new_browser = self._make_handler()
        original_browser = MagicMock()
        original_browser.close.side_effect = Exception("Already closed")

        operation = MagicMock(side_effect=[PlaywrightError("Target closed"), "ok"])

        result, returned_browser = handler.execute(operation, original_browser)

        assert result == "ok"
        assert returned_browser is new_browser

    @patch("fbcm.browser_retry.time.sleep")
    def test_custom_retry_delay(self, mock_sleep):
        handler, _, _ = self._make_handler(retry_delay=2.5)
        browser = MagicMock()

        operation = MagicMock(side_effect=[PlaywrightError("Target closed"), "ok"])

        handler.execute(operation, browser)

        mock_sleep.assert_called_once_with(2.5)

    @patch("fbcm.browser_retry.time.sleep")
    def test_multiple_retries_before_success(self, mock_sleep):
        handler, launch_browser, _ = self._make_handler(max_retries=4)
        browser = MagicMock()

        operation = MagicMock(
            side_effect=[
                PlaywrightError("Target closed"),
                PlaywrightError("browser has been closed"),
                PlaywrightError("Target closed"),
                "finally",
            ]
        )

        result, _ = handler.execute(operation, browser)

        assert result == "finally"
        assert operation.call_count == 4
        assert launch_browser.call_count == 3


class TestRecoverableErrorPhrases:
    def test_phrases_are_lowercase(self):
        for phrase in RECOVERABLE_ERROR_PHRASES:
            assert phrase == phrase.lower()
