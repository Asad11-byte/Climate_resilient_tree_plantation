from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import CurrentUser, get_current_user
from app.core.dependencies import get_species_repository
from app.core.exceptions import ProviderUnavailableError
from app.schemas.species import TreeSpecies

router = APIRouter(tags=["species"])


@router.get("/species", response_model=List[TreeSpecies])
async def list_species(current_user: CurrentUser = Depends(get_current_user)) -> List[TreeSpecies]:
    try:
        repo = get_species_repository()
        rows = await repo.list_all()
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return [TreeSpecies(**row) for row in rows]


@router.get("/species/{species_id}", response_model=TreeSpecies)
async def get_species(
    species_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> TreeSpecies:
    try:
        repo = get_species_repository()
        row = await repo.get_by_id(species_id)
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return TreeSpecies(**row)