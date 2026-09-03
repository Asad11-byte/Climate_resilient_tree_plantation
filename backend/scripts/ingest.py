#!/usr/bin/env python3
"""
CLI: ingest documents from a directory into Qdrant.

Usage:
    python scripts/ingest.py --path data/raw
    python scripts/ingest.py --path data/raw --source "Punjab Forest Department" --topic tree_species --year 2022

Per-file metadata overrides: place a "<filename>.meta.json" next to a file,
e.g. "daphar_plantation.pdf.meta.json":
    {"source": "Punjab Forest Department", "source_url": "https://...", "year": 2021, "topic": "plantation"}

Re-running this on the same files is safe — chunk IDs are deterministic, so
Qdrant upserts overwrite existing points instead of duplicating them.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import get_ingestion_pipeline  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant")
    parser.add_argument("--path", required=True, help="Directory containing PDF/DOCX/TXT/MD files")
    parser.add_argument("--source", default=None, help="Default source organization for all files")
    parser.add_argument("--source-url", default=None, help="Default source URL for all files")
    parser.add_argument("--topic", default=None, help="Default topic tag for all files")
    parser.add_argument("--document-type", default=None, help="Default document type for all files")
    parser.add_argument("--year", type=int, default=None, help="Default year for all files")
    args = parser.parse_args()

    configure_logging(debug=True)

    directory = Path(args.path)
    if not directory.exists():
        logger.error("Path does not exist: %s", directory)
        raise SystemExit(1)

    default_metadata = {
        k: v
        for k, v in {
            "source": args.source,
            "source_url": args.source_url,
            "topic": args.topic,
            "document_type": args.document_type,
            "year": args.year,
        }.items()
        if v is not None
    }

    pipeline = get_ingestion_pipeline()
    summary = await pipeline.ingest_directory(directory, default_metadata)

    if summary.files_found == 0:
        logger.warning("No supported files (.pdf/.docx/.txt/.md) found in %s", directory)
        return

    total_chunks = sum(r.chunks_indexed for r in summary.results)
    print(
        f"\nFound {summary.files_found} file(s). "
        f"Successfully ingested {len(summary.results)}, {total_chunks} chunk(s) total.\n"
    )
    for r in summary.results:
        status = "OK" if r.chunks_indexed > 0 else "SKIPPED (no content)"
        print(f"  [{status}] {r.source_path} -> {r.chunks_indexed} chunks (document_id={r.document_id})")

    if summary.failures:
        print(f"\n{len(summary.failures)} file(s) FAILED:")
        for failure in summary.failures:
            print(f"  [FAILED] {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
