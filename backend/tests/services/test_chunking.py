from app.services.ingestion.chunking import chunk_document
from app.services.ingestion.loaders import RawDocument


def test_markdown_chunks_carry_breadcrumb():
    text = (
        "# Tree Species\n\n"
        "## Shisham\n\n"
        "### Soil Requirements\n\n"
        "Shisham prefers well-drained alluvial soils with neutral to slightly "
        "alkaline pH. It tolerates a range of soil textures but performs poorly "
        "in waterlogged conditions.\n\n"
        "## Kikar\n\n"
        "Kikar is highly drought tolerant and grows in a wide range of soils.\n"
    )
    raw = RawDocument(document_id="doc1", title="Species Guide", source_path="x.md",
                       file_type="md", text=text)
    chunks = chunk_document(raw, chunk_size=200, chunk_overlap=20)

    assert len(chunks) >= 2
    assert any("Tree Species > Shisham > Soil Requirements" in c.breadcrumb for c in chunks)
    assert all(c.document_id == "doc1" for c in chunks)
    # chunk_index should be sequential starting at 0
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_pdf_chunks_carry_page_numbers():
    raw = RawDocument(
        document_id="doc2", title="Report", source_path="x.pdf", file_type="pdf",
        text="ignored for pdf path",
        pages=["Page one content about rainfall patterns in Punjab.", "Page two content about soil pH."],
    )
    chunks = chunk_document(raw, chunk_size=500, chunk_overlap=0)
    pages = {c.page for c in chunks}
    assert pages == {1, 2}


def test_empty_text_produces_no_chunks():
    raw = RawDocument(document_id="doc3", title="Empty", source_path="x.md", file_type="md", text="")
    chunks = chunk_document(raw)
    assert chunks == []
