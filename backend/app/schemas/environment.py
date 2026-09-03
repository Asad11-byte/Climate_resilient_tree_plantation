from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EnvironmentalRecord(BaseModel):
    id: Optional[UUID] = None
    """None when this reading came from a live provider but couldn't be
    cached (e.g. Supabase temporarily unreachable) — still real data, just
    not yet persisted."""
    latitude: float
    longitude: float
    soil_ph: Optional[float] = None
    clay: Optional[float] = None
    sand: Optional[float] = None
    organic_carbon: Optional[float] = None
    temperature: Optional[float] = None
    rainfall: Optional[float] = None
    ndvi: Optional[float] = None
    ndwi: Optional[float] = None
    land_cover: Optional[str] = None
    data_source: str
    retrieved_at: datetime


class EnvironmentQuery(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class EnvironmentResponse(BaseModel):
    available: bool
    record: Optional[EnvironmentalRecord] = None
    message: Optional[str] = None
    """Set when `available` is False, e.g. 'Data unavailable for this
    location' — the API must never fabricate values to fill this gap."""
