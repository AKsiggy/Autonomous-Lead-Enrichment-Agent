import logging
import re

from collections import deque
from urllib.parse import urljoin, urldefrag, urlparse

from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from .browser import Browser
from .models import CrawlResult, ScrapedPage


logger = logging.getLogger(__name__)


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

#weights
IMPORTANT_PATH_KEYWORDS = {
    "about": 10,
    "company": 10,
    "team": 10,
    "leadership": 10,
    "people": 10,
    "contact": 9,
    "sales": 9,
    "pricing": 8,
    "customers": 7,
    "careers": 6,
    "press": 5,
    "investors": 5,
}


class WebsiteScraper:
    """
    Selenium-based website crawler.

    Renders JavaScript pages, discovers internal links,
    extracts useful text, emails, and LinkedIn URLs.
    """

    def __init__(
        self,
        timeout: int = 20,
        max_pages: int = 7,
    ):
        self.timeout = timeout
        self.max_pages = max_pages

    def crawl(
        self,
        domain: str,
    ) -> CrawlResult:

        normalized_domain = self._normalize_domain(
            domain
        )

        base_url = f"https://{normalized_domain}"

        pages = []
        discovered_urls = []

        queue = deque([base_url])
        visited = set()

        try:
            with Browser(
                timeout=self.timeout
            ) as driver:

                while (
                    queue
                    and len(pages) < self.max_pages
                ):
                    url = queue.popleft()

                    if url in visited:
                        continue

                    visited.add(url)

                    try:
                        logger.info(
                            "Fetching %s",
                            url,
                        )

                        driver.get(url)

                        html = driver.page_source

                        page = self._parse_html(
                            html,
                            url,
                        )

                        pages.append(page)

                        # Discover links from the
                        # rendered Selenium DOM.
                        new_urls = self._discover_links(
                            driver,
                            base_url,
                        )

                        for new_url in new_urls:
                            if new_url not in discovered_urls:
                                discovered_urls.append(
                                    new_url
                                )

                        # Prioritize useful pages.
                        prioritized_urls = sorted(
                            new_urls,
                            key=self._url_score,
                            reverse=True,
                        )

                        for next_url in prioritized_urls:
                            if (
                                next_url not in visited
                                and next_url not in queue
                            ):
                                queue.append(
                                    next_url
                                )

                    except Exception as exc:
                        logger.warning(
                            "Failed to scrape %s: %s",
                            url,
                            exc,
                        )

        except Exception as exc:
            logger.error(
                "Browser failed for %s: %s",
                domain,
                exc,
            )

        return CrawlResult(
            domain=normalized_domain,
            pages=pages,
            discovered_urls=discovered_urls,
        )

    @staticmethod
    def _normalize_domain(
        domain: str,
    ) -> str:

        domain = domain.strip()

        if not domain:
            raise ValueError(
                "Domain cannot be empty."
            )

        if not domain.startswith(
            ("http://", "https://")
        ):
            domain = "https://" + domain

        parsed = urlparse(domain)

        if not parsed.netloc:
            raise ValueError(
                f"Invalid domain: {domain}"
            )

        return parsed.netloc.lower()

    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:

        url, _ = urldefrag(url)

        parsed = urlparse(url)

        if (
            parsed.path != "/"
            and url.endswith("/")
        ):
            url = url[:-1]

        return url

    @classmethod
    def _discover_links(
        cls,
        driver,
        base_url: str,
    ) -> list[str]:

        results = []

        try:
            anchors = driver.find_elements(
                By.CSS_SELECTOR,
                "a[href]",
            )

        except WebDriverException as exc:
            logger.warning(
                "Could not inspect links: %s",
                exc,
            )
            return results

        for anchor in anchors:

            try:
                href = anchor.get_attribute(
                    "href"
                )

                if not href:
                    continue

                absolute_url = urljoin(
                    base_url,
                    href,
                )

                absolute_url = cls._normalize_url(
                    absolute_url
                )

                if not cls._is_internal_url(
                    absolute_url,
                    base_url,
                ):
                    continue

                if not cls._is_html_page(
                    absolute_url
                ):
                    continue

                if absolute_url not in results:
                    results.append(
                        absolute_url
                    )

            except WebDriverException:
                continue

        return results

    @staticmethod
    def _is_internal_url(
        url: str,
        base_url: str,
    ) -> bool:

        url_host = urlparse(
            url
        ).netloc.lower()

        base_host = urlparse(
            base_url
        ).netloc.lower()

        return (
            url_host == base_host
            or url_host.endswith(
                "." + base_host
            )
        )

    @staticmethod
    def _is_html_page(
        url: str,
    ) -> bool:

        path = urlparse(
            url
        ).path.lower()

        blocked_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".ico",
            ".pdf",
            ".zip",
            ".mp4",
            ".mp3",
            ".css",
            ".js",
            ".xml",
        )

        return not path.endswith(
            blocked_extensions
        )

    @classmethod
    def _url_score(
        cls,
        url: str,
    ) -> int:

        path = urlparse(
            url
        ).path.lower()

        score = 0

        for keyword, points in (
            IMPORTANT_PATH_KEYWORDS.items()
        ):
            if keyword in path:
                score += points

        if path.count("/") <= 2:
            score += 2

        return score

    @staticmethod
    def _parse_html(
        html: str,
        url: str,
    ) -> ScrapedPage:

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # ==================================================
        # IMPORTANT:
        # Extract metadata BEFORE removing footer/nav.
        #
        # Postman's LinkedIn URL is in the footer.
        # ==================================================

        raw_text = soup.get_text(
            " ",
            strip=True,
        )

        # --------------------------------------------------
        # Emails
        # --------------------------------------------------

        emails = sorted(
            set(
                EMAIL_PATTERN.findall(
                    raw_text
                )
            )
        )

        # --------------------------------------------------
        # LinkedIn URLs
        # --------------------------------------------------

        linkedin_urls = []

        for anchor in soup.find_all(
            "a",
            href=True,
        ):
            href = anchor.get(
                "href"
            )

            if not isinstance(
                href,
                str,
            ):
                continue

            href = href.strip()

            if "linkedin.com" not in href.lower():
                continue

            linkedin_url = urljoin(
                url,
                href,
            )

            # Remove URL fragments.
            linkedin_url, _ = urldefrag(
                linkedin_url
            )

            linkedin_urls.append(
                linkedin_url
            )

        linkedin_urls = sorted(
            set(linkedin_urls)
        )

        # ==================================================
        # NOW clean the DOM for the LLM.
        # ==================================================

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "canvas",
                "iframe",
                "nav",
                "footer",
                "form",
            ]
        ):
            element.decompose()

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        title = ""

        if soup.title:
            title = soup.title.get_text(
                " ",
                strip=True,
            )

        # --------------------------------------------------
        # Main content
        # --------------------------------------------------

        root = (
            soup.find("main")
            or soup.find("article")
            or soup.body
            or soup
        )

        text = root.get_text(
            "\n",
            strip=True,
        )

        lines = []

        for line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                line,
            ).strip()

            if line:
                lines.append(
                    line
                )

        clean_text = "\n".join(
            lines
        )

        return ScrapedPage(
            url=url,
            title=title,
            text=clean_text,
            emails=emails,
            linkedin_urls=linkedin_urls,
        )
