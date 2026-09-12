import argparse
import json
import logging
from pathlib import Path

from app.config import Settings
from app.pipeline import LeadEnrichmentPipeline


DEFAULT_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous company lead enrichment agent."
    )

    parser.add_argument(
        "domains",
        nargs="*",
        help=(
            "Company domains to enrich. "
            "If omitted, the three assignment domains are used."
        ),
    )

    parser.add_argument(
        "--output",
        default="output/results.json",
        help="Output JSON file path.",
    )

    return parser.parse_args()


def save_results(results, output_path: str) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            [
                result.model_dump()
                for result in results
            ],
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    args = parse_args()

    domains = args.domains or DEFAULT_DOMAINS

    settings = Settings.from_env()

    pipeline = LeadEnrichmentPipeline(
        settings
    )

    results = pipeline.process_many(
        domains
    )

    save_results(
        results,
        args.output,
    )

    print(
        f"\nSuccessfully enriched "
        f"{len(results)}/{len(domains)} domains."
    )

    print(
        f"Results saved to: {args.output}"
    )


if __name__ == "__main__":
    main()
