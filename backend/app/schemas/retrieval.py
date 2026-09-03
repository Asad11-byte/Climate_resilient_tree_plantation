from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    metadata_filter: Optional[Dict[str, Any]] = None


class SourceSchema(BaseModel):
    document_id: str
    title: str
    source: str
    source_url: Optional[str] = None
    document_type: str
    year: Optional[int] = None
    location: str
    page: Optional[int] = None


class RetrievedChunkSchema(BaseModel):
    id: str
    text: str
    vector_score: float
    rerank_score: Optional[float] = None
    breadcrumb: Optional[str] = None
    page: Optional[int] = None


class RetrieveResponse(BaseModel):
    query: str
    query_category: str
    chunks: List[RetrievedChunkSchema]
    sources: List[SourceSchema]
