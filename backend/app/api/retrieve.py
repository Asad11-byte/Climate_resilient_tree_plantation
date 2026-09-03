from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_retrieval_service
from app.core.exceptions import InsufficientEvidenceError, ProviderUnavailableError
from app.schemas.retrieval import (
    RetrievedChunkSchema,
    RetrieveRequest,
    RetrieveResponse,
    SourceSchema,
)
from app.services.citations.builder import build_sources
from app.services.query.classifier import classify_query
from app.services.retrieval.service import RetrievalService

router = APIRouter(tags=["retrieval"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(
    request: RetrieveRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RetrieveResponse:
    category = classify_query(request.query)

    try:
        chunks = await retrieval_service.retrieve(
            query=request.query,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter,
        )
    except InsufficientEvidenceError:
        # Not an error condition — an honest empty result. The chat layer
        # (Phase 3) uses this same signal to tell the user evidence is
        # unavailable instead of letting Groq guess.
        return RetrieveResponse(query=request.query, query_category=category, chunks=[], sources=[])
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sources = build_sources(chunks)

    return RetrieveResponse(
        query=request.query,
        query_category=category,
        chunks=[
            RetrievedChunkSchema(
                id=c.id,
                text=c.text,
                vector_score=c.vector_score,
                rerank_score=c.rerank_score,
                breadcrumb=c.payload.get("breadcrumb"),
                page=c.payload.get("page"),
            )
            for c in chunks
        ],
        sources=[SourceSchema(**s.__dict__) for s in sources],
    )
