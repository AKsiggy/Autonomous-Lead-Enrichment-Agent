import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


logger = logging.getLogger(__name__)


class Browser:
    """Small wrapper around Selenium Chrome."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.driver: webdriver.Chrome | None = None

    def start(self) -> webdriver.Chrome:
        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440,1200")

        options.add_argument(
            "--user-agent="
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)

        return self.driver

    def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception as exc:
                logger.warning(
                    "Failed to close browser cleanly: %s",
                    exc,
                )

            self.driver = None

    def __enter__(self) -> webdriver.Chrome:
        return self.start()

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
