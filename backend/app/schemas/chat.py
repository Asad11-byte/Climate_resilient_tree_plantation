from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.retrieval import SourceSchema


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    query: str
    query_category: str
    evidence_available: bool
    answer: str
    sources: List[SourceSchema]
    model: Optional[str] = None
