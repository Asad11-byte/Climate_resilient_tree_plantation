"""
Chunk inspector — loads ONE document through the real loader + semantic
chunker (no embedding upsert, no Qdrant write) and writes two files:
  1. the raw extracted text, page by page — check this FIRST for
     two-column PDF scrambling (sentences from the left and right column
     interleaved) before blaming chunking for anything.
  2. every resulting chunk, with its breadcrumb/page/char count — check
     this to confirm a specific fact survives as one coherent, retrievable
     unit rather than split mid-sentence.

Usage (run from the backend/ project root):
    python scripts/inspect_chunks.py data/raw/agriculture-12-00295-v2.pdf

Writes to:
    eval/chunk_inspection/<filename>.raw.txt
    eval/chunk_inspection/<filename>.chunks.txt
"""
import sys
from pathlib import Path

# Must happen before any `from app...` import below — running this file
# directly (`python scripts/inspect_chunks.py`) only puts scripts/ itself
# on sys.path, not backend/, so `app` isn't importable otherwise. If your
# other scripts (ingest.py etc.) already have a similar line, or the
# project is pip-installed with `pip install -e .`, this is redundant but
# harmless; if they DON'T have it, they likely only work when run as
# `python -m scripts.ingest` instead of `python scripts/ingest.py` — worth
# checking if you've hit this same error there too.
PROJECT_ROOT = Path(__file__).parent.parent  # backend/ — scripts/ is one level below this
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio  # noqa: E402

from app.core.dependencies import get_embedding_provider  # noqa: E402
from app.services.ingestion.chunking import chunk_document  # noqa: E402
from app.services.ingestion.loaders import load_file  # noqa: E402  <-- adjust if named differently

OUT_DIR = PROJECT_ROOT / "eval" / "chunk_inspection"


def resolve_input_path(raw_arg: str) -> Path:
    """Accepts the path as given (relative to wherever you happen to be
    running the command from) OR relative to the backend project root."""
    candidate = Path(raw_arg)
    if candidate.is_file():
        return candidate

    from_root = PROJECT_ROOT / raw_arg
    if from_root.is_file():
        return from_root

    raise FileNotFoundError(
        f"Could not find '{raw_arg}' as given, nor as '{from_root}'.\n"
        f"Run this from the backend/ root, e.g.:\n"
        f"  cd backend\n"
        f"  python scripts/inspect_chunks.py data/raw/your-file.pdf\n"
        f"...or pass an absolute path instead."
    )


def write_raw_dump(path: Path, raw) -> Path:
    out_path = OUT_DIR / f"{path.stem}.raw.txt"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"Source: {path}\n")
        f.write(f"document_id: {raw.document_id}\n")
        f.write(f"file_type: {raw.file_type}\n\n")

        if raw.pages:
            f.write(f"Extracted as {len(raw.pages)} page(s).\n")
            f.write("=" * 80 + "\n\n")
            for i, page_text in enumerate(raw.pages, start=1):
                f.write(f"--- page {i} ({len(page_text)} chars) ---\n")
                f.write(page_text)
                f.write("\n\n")
        else:
            f.write("No page structure (markdown/txt). Full text:\n")
            f.write("=" * 80 + "\n\n")
            f.write(raw.text)
    return out_path


def write_chunk_dump(path: Path, raw, chunks) -> Path:
    out_path = OUT_DIR / f"{path.stem}.chunks.txt"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"Source: {path}\n")
        f.write(f"document_id: {raw.document_id}\n")
        f.write(f"Total chunks: {len(chunks)}\n")
        f.write("=" * 80 + "\n\n")
        for chunk in chunks:
            f.write(f"--- chunk_index={chunk.chunk_index}  page={chunk.page}  chars={len(chunk.text)} ---\n")
            if chunk.breadcrumb:
                f.write(f"breadcrumb: {chunk.breadcrumb}\n")
            f.write(chunk.text)
            f.write("\n\n")
    return out_path


async def main(path: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading {path}...")
    raw = load_file(path)
    print(f"  document_id: {raw.document_id}")
    print(f"  file_type:   {raw.file_type}")
    print(f"  pages:       {len(raw.pages) if raw.pages else 'n/a (no page structure)'}")

    raw_out = write_raw_dump(path, raw)
    print(f"\nRaw extraction written to {raw_out}")
    print("  -> Open this FIRST. Read a paragraph you know the source text of.")
    print("     If sentences jump between unrelated topics mid-paragraph,")
    print("     that's two-column extraction scrambling — a loader problem,")
    print("     not a chunking problem.")

    embedding_provider = get_embedding_provider()
    print("\nChunking (semantic — this calls the embedding API)...")
    chunks = await chunk_document(raw, embedding_provider)
    print(f"  {len(chunks)} chunks produced")

    chunks_out = write_chunk_dump(path, raw, chunks)
    print(f"\nChunks written to {chunks_out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_chunks.py <path-to-document>")
        sys.exit(1)
    try:
        resolved = resolve_input_path(sys.argv[1])
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(resolved))