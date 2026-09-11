from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionSchema(BaseModel):
    # populate_by_name lets this be built from a Supabase row (snake_case
    # attrs) while serializing to camelCase for the frontend, since
    # FastAPI's response_model_by_alias defaults to True.
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    title: Optional[str] = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class RenameSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class MessageSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    role: str
    content: str
    query_category: Optional[str] = Field(default=None, serialization_alias="queryCategory")
    evidence_available: Optional[bool] = Field(default=None, serialization_alias="evidenceAvailable")
    sources: Optional[list[dict[str, Any]]] = None
    created_at: datetime = Field(serialization_alias="createdAt")