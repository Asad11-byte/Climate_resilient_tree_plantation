from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.retrieval import SourceSchema

# NOTE: reconstructed from how app/api/chat.py uses these models (I haven't
# seen your original app/schemas/chat.py). If your real file has extra
# fields or validators beyond query/latitude/longitude/top_k and
# query_category/evidence_available/answer/sources/model, carry those over
# — only `session_id` is new here.


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    top_k: Optional[int] = None
    # Omit to start a new session; pass an existing session's id to
    # continue that conversation.
    session_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    query: str
    query_category: str
    evidence_available: bool
    answer: str
    sources: List[SourceSchema] = Field(default_factory=list)
    model: Optional[str] = None
    # Always populated on the way out — the frontend uses this to know which
    # session to attach the next message in this thread to.
    session_id: UUID