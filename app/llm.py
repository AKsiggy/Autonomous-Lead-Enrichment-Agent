import json
import logging

from groq import Groq
from pydantic import ValidationError

from .models import CompanyIntelligence


logger = logging.getLogger(__name__)


class GroqExtractor:
    """
    Handles communication with the Groq API and converts the
    response into a validated CompanyIntelligence object.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self.client = Groq(api_key=api_key)
        self.model = model

        # Generate the schema directly from the Pydantic model.
        # This keeps the LLM prompt synchronized with models.py.
        self.schema = CompanyIntelligence.model_json_schema()

        self.system_prompt = f"""
You are a B2B lead enrichment analyst.

Analyze public company website content and extract reliable
company intelligence.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. The JSON MUST conform to the supplied Pydantic JSON schema.
3. Every required field MUST be present.
4. NEVER omit a required field.
5. NEVER invent facts unsupported by the supplied website content.
6. company_overview MUST contain exactly two concise sentences.
7. target_audience_icp MUST always be present.
8. Determine target_audience_icp from the company's products,
   services, positioning, customers, use cases, and other supplied
   website content.
9. If the exact ICP is not explicitly stated, make a conservative
   inference from the available website evidence. Do not invent
   specific companies, job titles, industries, or demographics
   without supporting evidence.
10. Only include contact email addresses that actually appear in
    the supplied source data.
11. Include leadership/team members only when their name and role
    are supported by the supplied website content.
12. Include LinkedIn URLs only when explicitly available.
13. contact_points may be an empty list when no emails are found.
14. key_leadership_team may be an empty list when no leadership
    information is found.
15. data_confidence_score must be between 0.0 and 1.0.
16. Do not add commentary outside the JSON.
17. Do not return markdown.
18. Do not omit fields simply because the website does not explicitly
    state them.

Pydantic JSON Schema:

{json.dumps(self.schema, indent=2)}
"""

    def extract(
        self,
        domain: str,
        context: str,
    ) -> CompanyIntelligence:
        """
        Extract structured company intelligence from website context.

        Raises:
            RuntimeError: If the Groq API request fails.
            ValueError: If the response is empty, invalid JSON,
                        or fails Pydantic validation.
        """

        logger.info(
            "Sending %s to Groq for enrichment",
            domain,
        )

        # --------------------------------------------------------
        # Call Groq
        # --------------------------------------------------------

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={
                    "type": "json_object",
                },
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Extract company intelligence "
                            f"for {domain}.\n\n"
                            f"SOURCE DATA:\n{context}"
                        ),
                    },
                ],
            )

        except Exception as exc:
            logger.error(
                "Groq API request failed for %s: %s",
                domain,
                exc,
            )

            raise RuntimeError(
                f"LLM request failed for {domain}"
            ) from exc

        # --------------------------------------------------------
        # Validate response structure
        # --------------------------------------------------------

        if not response.choices:
            raise ValueError(
                f"Groq returned no choices for {domain}"
            )

        raw = response.choices[0].message.content

        if not raw:
            raise ValueError(
                f"Groq returned an empty response for {domain}"
            )

        logger.debug(
            "Raw Groq response for %s: %s",
            domain,
            raw,
        )

        # --------------------------------------------------------
        # Parse JSON
        # --------------------------------------------------------

        try:
            data = json.loads(raw)

        except json.JSONDecodeError as exc:
            logger.error(
                "Groq returned invalid JSON for %s: %s",
                domain,
                raw[:2000],
            )

            raise ValueError(
                f"Groq returned invalid JSON for {domain}"
            ) from exc

        # --------------------------------------------------------
        # Validate against Pydantic schema
        # --------------------------------------------------------

        try:
            result = CompanyIntelligence.model_validate(data)

        except ValidationError as exc:
            logger.error(
                "Groq response failed schema validation "
                "for %s:\n%s\nRaw response:\n%s",
                domain,
                exc,
                raw[:2000],
            )

            raise ValueError(
                f"Invalid LLM response schema for {domain}"
            ) from exc

        # --------------------------------------------------------
        # Token usage
        # --------------------------------------------------------

        if response.usage:
            logger.info(
                "LLM usage | domain=%s | "
                "prompt=%s | completion=%s | total=%s",
                domain,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )

        logger.info(
            "Successfully enriched %s",
            domain,
        )

        return result
