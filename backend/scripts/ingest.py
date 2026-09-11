#!/usr/bin/env python3
"""
CLI: ingest documents from a directory into Qdrant with per-file metadata.

Expected structure:

    data/
    ├── raw/
    │   ├── 2024-japs-2746.pdf
    │   ├── agriculture-12-00295-v2.pdf
    │   ├── Ethnomedicinal_Flora_of_District_Mandi_B.pdf
    │   └── sustainability-14-13312.pdf
    │
    └── metadata/
        ├── 2024-japs-2746.pdf.meta.json
        ├── agriculture-12-00295-v2.pdf.meta.json
        ├── Ethnomedicinal_Flora_of_District_Mandi_B.pdf.meta.json
        └── sustainability-14-13312.pdf.meta.json

The metadata filename must be:

    <document filename>.meta.json

Example:

    agriculture-12-00295-v2.pdf
    agriculture-12-00295-v2.pdf.meta.json

The metadata JSON is copied beside the source document before ingestion,
because the ingestion pipeline supports per-file "<filename>.meta.json"
overrides.

Metadata example:

    {
        "title": "Carbon Storage Potential of Agroforestry System near Brick Kilns",
        "source": "MDPI Agriculture",
        "source_url": "https://...",
        "document_type": "research paper",
        "year": 2024,
        "topic": "tree_species",
        "location": "Mandi Bahauddin"
    }

Re-running this script is safe. Existing chunks are upserted using the
pipeline's deterministic chunk IDs.
"""

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import get_ingestion_pipeline  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402


logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_and_sync_metadata(
    raw_directory: Path,
    metadata_directory: Path,
) -> int:
    """
    Validate metadata JSON files and copy them next to their corresponding
    source documents.

    Example:

        data/metadata/paper.pdf.meta.json
                ↓
        data/raw/paper.pdf.meta.json

    Returns:
        Number of metadata files successfully synchronized.
    """

    if not metadata_directory.exists():
        logger.warning(
            "Metadata directory does not exist: %s",
            metadata_directory,
        )
        return 0

    metadata_files = list(metadata_directory.glob("*.meta.json"))

    if not metadata_files:
        logger.warning(
            "No .meta.json files found in %s",
            metadata_directory,
        )
        return 0

    synced = 0

    for metadata_file in metadata_files:
        try:
            # Validate JSON first
            with metadata_file.open("r", encoding="utf-8") as f:
                metadata: Dict[str, Any] = json.load(f)

            if not isinstance(metadata, dict):
                raise ValueError("Metadata JSON must contain an object")

            # Recover original document filename.
            #
            # Example:
            # agriculture-12-00295-v2.pdf.meta.json
            #                  ↓
            # agriculture-12-00295-v2.pdf
            document_name = metadata_file.name[:-len(".meta.json")]

            document_path = raw_directory / document_name

            if not document_path.exists():
                logger.warning(
                    "Metadata has no matching document: %s -> %s",
                    metadata_file.name,
                    document_name,
                )
                continue

            # Copy metadata beside the document.
            destination = raw_directory / metadata_file.name

            shutil.copy2(metadata_file, destination)

            logger.info(
                "Metadata synchronized: %s -> %s",
                metadata_file,
                destination,
            )

            synced += 1

        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON in metadata file %s: %s",
                metadata_file,
                exc,
            )

        except Exception as exc:
            logger.error(
                "Failed to process metadata %s: %s",
                metadata_file,
                exc,
            )

    return synced


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents and their metadata into Qdrant"
    )

    parser.add_argument(
        "--path",
        default="data/raw",
        help="Directory containing PDF/DOCX/TXT/MD files",
    )

    parser.add_argument(
        "--metadata-path",
        default="data/metadata",
        help="Directory containing <filename>.meta.json files",
    )

    parser.add_argument(
        "--source",
        default=None,
        help="Default source organization for all files",
    )

    parser.add_argument(
        "--source-url",
        default=None,
        help="Default source URL for all files",
    )

    parser.add_argument(
        "--topic",
        default=None,
        help="Default topic tag for all files",
    )

    parser.add_argument(
        "--document-type",
        default=None,
        help="Default document type for all files",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Default year for all files",
    )

    args = parser.parse_args()

    configure_logging(debug=True)

    raw_directory = Path(args.path)
    metadata_directory = Path(args.metadata_path)

    if not raw_directory.exists():
        logger.error(
            "Raw document path does not exist: %s",
            raw_directory,
        )
        raise SystemExit(1)

    # ---------------------------------------------------------
    # 1. Synchronize metadata beside corresponding documents
    # ---------------------------------------------------------

    print("\nSynchronizing metadata...")

    metadata_count = load_and_sync_metadata(
        raw_directory,
        metadata_directory,
    )

    print(
        f"Metadata synchronized: {metadata_count} file(s)"
    )

    # ---------------------------------------------------------
    # 2. Build default metadata
    # ---------------------------------------------------------

    default_metadata = {
        key: value
        for key, value in {
            "source": args.source,
            "source_url": args.source_url,
            "topic": args.topic,
            "document_type": args.document_type,
            "year": args.year,
        }.items()
        if value is not None
    }

    # ---------------------------------------------------------
    # 3. Start ingestion pipeline
    # ---------------------------------------------------------

    print("\nStarting document ingestion...")

    pipeline = get_ingestion_pipeline()

    summary = await pipeline.ingest_directory(
        raw_directory,
        default_metadata,
    )

    # ---------------------------------------------------------
    # 4. Handle empty directory
    # ---------------------------------------------------------

    if summary.files_found == 0:
        logger.warning(
            "No supported files (.pdf/.docx/.txt/.md) found in %s",
            raw_directory,
        )
        return

    # ---------------------------------------------------------
    # 5. Print ingestion summary
    # ---------------------------------------------------------

    total_chunks = sum(
        result.chunks_indexed
        for result in summary.results
    )

    print(
        f"\nFound {summary.files_found} file(s). "
        f"Successfully ingested {len(summary.results)}, "
        f"{total_chunks} chunk(s) total.\n"
    )

    for result in summary.results:
        status = (
            "OK"
            if result.chunks_indexed > 0
            else "SKIPPED (no content)"
        )

        print(
            f"  [{status}] "
            f"{result.source_path} -> "
            f"{result.chunks_indexed} chunks "
            f"(document_id={result.document_id})"
        )

    # ---------------------------------------------------------
    # 6. Handle failures
    # ---------------------------------------------------------

    if summary.failures:
        print(
            f"\n{len(summary.failures)} file(s) FAILED:"
        )

        for failure in summary.failures:
            print(f"  [FAILED] {failure}")

        raise SystemExit(1)

    print("\nIngestion completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())