import pytest

from app.repositories.environmental_repository import EnvironmentalRepository
from app.repositories.species_repository import SpeciesRepository
from tests.fakes import FakeSupabaseClient


@pytest.mark.asyncio
async def test_list_all_species():
    client = FakeSupabaseClient()
    client.seed("tree_species", [
        {"id": "1", "common_name": "Shisham", "scientific_name": "Dalbergia sissoo"},
        {"id": "2", "common_name": "Kikar", "scientific_name": "Acacia nilotica"},
    ])
    repo = SpeciesRepository(client)
    rows = await repo.list_all()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_get_species_by_id_found_and_missing():
    client = FakeSupabaseClient()
    client.seed("tree_species", [{"id": "1", "common_name": "Shisham", "scientific_name": "Dalbergia sissoo"}])
    repo = SpeciesRepository(client)

    found = await repo.get_by_id("1")
    assert found["common_name"] == "Shisham"

    missing = await repo.get_by_id("does-not-exist")
    assert missing is None


@pytest.mark.asyncio
async def test_species_create_returns_created_row():
    client = FakeSupabaseClient()
    repo = SpeciesRepository(client)
    created = await repo.create({"common_name": "Kikar", "scientific_name": "Acacia nilotica"})
    assert created["common_name"] == "Kikar"
    assert "id" in created


@pytest.mark.asyncio
async def test_environmental_find_near_returns_closest_within_tolerance():
    client = FakeSupabaseClient()
    client.seed("environmental_data", [
        {"id": "a", "latitude": 32.585, "longitude": 73.492, "data_source": "SoilGrids"},   # exact match
        {"id": "b", "latitude": 32.60, "longitude": 73.50, "data_source": "SoilGrids"},      # further away, still in box
        {"id": "c", "latitude": 40.0, "longitude": 90.0, "data_source": "SoilGrids"},        # way out of range
    ])
    repo = EnvironmentalRepository(client)
    result = await repo.find_near(32.585, 73.492, tolerance=0.05)
    assert result is not None
    assert result["id"] == "a"


@pytest.mark.asyncio
async def test_environmental_find_near_returns_none_when_no_data_cached():
    client = FakeSupabaseClient()  # empty
    repo = EnvironmentalRepository(client)
    result = await repo.find_near(32.585, 73.492)
    assert result is None


@pytest.mark.asyncio
async def test_environmental_upsert():
    client = FakeSupabaseClient()
    repo = EnvironmentalRepository(client)
    record = await repo.upsert({"latitude": 32.585, "longitude": 73.492, "data_source": "SoilGrids", "soil_ph": 7.2})
    assert record["soil_ph"] == 7.2
