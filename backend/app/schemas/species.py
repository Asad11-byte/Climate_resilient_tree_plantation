from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

NOT_AVAILABLE = "Not available in current evidence"


class TreeSpecies(BaseModel):
    id: UUID
    common_name: str
    scientific_name: str
    local_names: Optional[List[str]] = None
    image_url: Optional[str] = None
    image_source: Optional[str] = None
    soil_requirements: Optional[str] = None
    water_requirement: Optional[str] = None
    drought_tolerance: Optional[str] = None
    heat_tolerance: Optional[str] = None
    flood_tolerance: Optional[str] = None
    growth_rate: Optional[str] = None
    planting_season: Optional[str] = None
    plantation_use: Optional[str] = None
    local_presence: Optional[str] = None
    description: Optional[str] = None
    source_ids: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    def display_dict(self) -> dict:
        """Render nulls as the explicit 'not available' string for API/UI
        consumption — never silently omit or fabricate a value.

        image_url / image_source are deliberately excluded from this
        substitution: a missing image should render as the frontend's
        placeholder icon, not as literal "Not available in current
        evidence" text sitting where a photo would go."""
        data = self.model_dump()
        for field in (
            "soil_requirements", "water_requirement", "drought_tolerance",
            "heat_tolerance", "flood_tolerance", "growth_rate", "planting_season",
            "plantation_use", "local_presence", "description",
        ):
            if data.get(field) is None:
                data[field] = NOT_AVAILABLE
        return data