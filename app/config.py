import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str 

    page_timeout: int = 20
    max_pages_per_domain: int = 7
    max_context_chars: int = 24_000

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Add it to your .env file."
            )

        return cls(
            groq_api_key=api_key,
            groq_model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-120b",
            ),
        )
