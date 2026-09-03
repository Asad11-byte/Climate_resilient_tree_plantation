from fastapi import APIRouter, HTTPException

from app.core.dependencies import get_environment_service
from app.core.exceptions import ProviderUnavailableError
from app.schemas.environment import EnvironmentalRecord, EnvironmentResponse

router = APIRouter(tags=["environment"])


@router.get("/environment", response_model=EnvironmentResponse)
async def get_environment(latitude: float, longitude: float) -> EnvironmentResponse:
    """
    Returns environmental data near the given coordinates: a cached Supabase
    row if one exists nearby, otherwise a live lookup (SoilGrids for soil
    properties, NASA POWER for temperature/rainfall) which is then cached.
    If neither the cache nor any live provider has data, this reports
    `available: false` honestly rather than estimating a value.
    """
    try:
        service = get_environment_service()
        result = await service.get_environment(latitude, longitude)
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not result.available:
        return EnvironmentResponse(available=False, message=result.message)
    return EnvironmentResponse(available=True, record=EnvironmentalRecord(**result.record))
