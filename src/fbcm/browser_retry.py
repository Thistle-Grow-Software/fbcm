import time
from collections.abc import Callable
from typing import TypeVar

from playwright.sync_api import Browser, Playwright
from playwright.sync_api import Error as PlaywrightError

T = TypeVar("T")

RECOVERABLE_ERROR_PHRASES = ("target closed", "browser has been closed")


def is_recoverable_browser_error(error: PlaywrightError) -> bool:
    """Check if a PlaywrightError is a recoverable browser crash."""
    error_msg = str(error).lower()
    return any(phrase in error_msg for phrase in RECOVERABLE_ERROR_PHRASES)


class BrowserRetryHandler:
    """Reusable retry handler for Playwright browser operations.

    Automatically relaunches the browser and retries when a recoverable
    browser crash (e.g. "target closed", "browser has been closed") occurs.

    Args:
        playwright: The Playwright instance used to launch browsers.
        launch_browser: Callable that launches and returns a new Browser instance.
        max_retries: Maximum number of retry attempts (default 3).
        retry_delay: Seconds to wait between retries (default 1).
    """

    def __init__(
        self,
        playwright: Playwright,
        launch_browser: Callable[[], Browser],
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.playwright = playwright
        self.launch_browser = launch_browser
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute(
        self,
        operation: Callable[[Browser], T],
        browser: Browser,
    ) -> tuple[T, Browser]:
        """Execute an operation with automatic browser crash recovery.

        Args:
            operation: A callable that takes a Browser and returns a result.
                       If the browser crashes, the operation is retried with
                       a fresh browser.
            browser: The current browser instance.

        Returns:
            A tuple of (operation result, browser). The browser may be a new
            instance if a relaunch occurred during retry.

        Raises:
            PlaywrightError: If all retries are exhausted or a non-recoverable
                             error occurs.
        """
        last_error: PlaywrightError | None = None

        for attempt in range(self.max_retries):
            try:
                result = operation(browser)
                return result, browser
            except PlaywrightError as e:
                if not is_recoverable_browser_error(e):
                    raise
                last_error = e
                print(
                    f"Browser/target closed (attempt {attempt + 1}/{self.max_retries}), "
                    f"relaunching..."
                )
                try:
                    browser.close()
                except Exception:
                    pass  # Browser may already be closed
                browser = self.launch_browser()
                time.sleep(self.retry_delay)

        raise last_error  # type: ignore[misc]
