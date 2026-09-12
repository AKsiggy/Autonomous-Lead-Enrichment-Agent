import json

from .models import DomainContext


class ContextBuilder:
    def __init__(
        self,
        max_chars: int = 30000,
        max_chars_per_page: int = 5000,
    ):
        self.max_chars = max_chars
        self.max_chars_per_page = max_chars_per_page

    def build(self, scraped):
        sections = []

        all_emails = sorted(
            {
                email
                for page in scraped.pages
                for email in page.emails
            }
        )

        all_linkedin = sorted(
            {
                url
                for page in scraped.pages
                for url in page.linkedin_urls
            }
        )

        sections.append(
            f"DOMAIN\n{scraped.domain}"
        )

        sections.append(
            "PUBLIC EMAILS\n"
            + (
                "\n".join(all_emails)
                if all_emails
                else "None found"
            )
        )

        sections.append(
            "LINKEDIN URLS\n"
            + (
                "\n".join(all_linkedin)
                if all_linkedin
                else "None found"
            )
        )

        remaining = self.max_chars

        for page in scraped.pages:
            if remaining <= 0:
                break

            text = page.text.strip()

            if not text:
                continue

            text = text[:min(
                self.max_chars_per_page,
                remaining,
            )]

            sections.append(
                f"PAGE URL\n{page.url}\n\n"
                f"PAGE TITLE\n{page.title}\n\n"
                f"PAGE CONTENT\n{text}"
            )

            remaining -= len(text)

        return "\n\n====================\n\n".join(
            sections
        )
