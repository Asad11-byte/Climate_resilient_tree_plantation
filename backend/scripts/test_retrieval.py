#!/usr/bin/env python3
"""
CLI: test retrieval (vector search + Jina rerank) against whatever is
currently indexed in Qdrant.

Usage:
    python scripts/test_retrieval.py "Which trees are drought tolerant near Mandi Bahauddin?"
    python scripts/test_retrieval.py "soil pH for Shisham" --top-k 3 --filter topic=soil
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import get_retrieval_service  # noqa: E402
from app.core.exceptions import InsufficientEvidenceError, ProviderUnavailableError  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.services.citations.builder import build_sources  # noqa: E402
from app.services.query.classifier import classify_query  # noqa: E402


def _parse_filter(pairs):
    if not pairs:
        return None
    result = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        result[key] = value
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test retrieval quality")
    parser.add_argument("query", help="Question to retrieve evidence for")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument(
        "--filter", action="append", default=None,
        help="Metadata filter as key=value, repeatable, e.g. --filter topic=soil",
    )
    args = parser.parse_args()

    configure_logging(debug=False)

    print(f"Query: {args.query}")
    print(f"Classified as: {classify_query(args.query)}\n")

    retrieval_service = get_retrieval_service()
    try:
        chunks = await retrieval_service.retrieve(
            query=args.query, top_k=args.top_k, metadata_filter=_parse_filter(args.filter)
        )
    except InsufficientEvidenceError:
        print("No relevant evidence found — the system would report evidence as unavailable.")
        return
    except ProviderUnavailableError as exc:
        print(f"Provider error: {exc}")
        return

    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Result {i} ---")
        print(f"vector_score={chunk.vector_score:.4f}  rerank_score={chunk.rerank_score}")
        print(f"breadcrumb: {chunk.payload.get('breadcrumb') or '(none)'}")
        print(f"page: {chunk.payload.get('page') or '(n/a)'}")
        print(chunk.text[:300].replace("\n", " ") + ("..." if len(chunk.text) > 300 else ""))
        print()

    print("Sources:")
    for source in build_sources(chunks):
        print(f"  - {source.title} | {source.source} | {source.year or 'n/a'} | {source.source_url or 'no URL'}")


if __name__ == "__main__":
    asyncio.run(main())
