import logging

from .config import Settings
from .extractor import ContextBuilder
from .llm import GroqExtractor
from .models import CompanyIntelligence
from .scraper import WebsiteScraper


logger = logging.getLogger(__name__)


class LeadEnrichmentPipeline:

    def __init__(self, settings: Settings):

        self.scraper = WebsiteScraper(
            timeout=settings.page_timeout,
            max_pages=settings.max_pages_per_domain,
        )

        self.context_builder = ContextBuilder(
            max_chars=settings.max_context_chars,
        )

        self.llm = GroqExtractor(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )

    def process(
        self,
        domain: str,
    ) -> CompanyIntelligence | None:

        logger.info(
            "Starting enrichment: %s",
            domain,
        )

        try:
            scraped = self.scraper.crawl(
                domain
            )

            if not scraped.pages:
                logger.warning(
                    "No usable pages found for %s",
                    domain,
                )
                return None

            context = self.context_builder.build(
                scraped
            )

            return self.llm.extract(
                domain,
                context,
            )

        except Exception as exc:
            logger.exception(
                "Failed enrichment for %s: %s",
                domain,
                exc,
            )

            # Important:
            # return None rather than killing the whole run.
            return None

    def process_many(
        self,
        domains: list[str],
    ) -> list[CompanyIntelligence]:

        results = []

        for domain in domains:

            result = self.process(domain)

            if result:
                results.append(result)

        return results
