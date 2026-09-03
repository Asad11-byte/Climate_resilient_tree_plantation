import pytest

from app.repositories.environmental_repository import EnvironmentalRepository
from app.services.environment.base import EnvironmentalReading
from app.services.environment.service import EnvironmentDataService
from tests.fakes import FakeEnvironmentProvider, FakeSupabaseClient


class FakeSettings:
    """Minimal settings stub for sentinel-provider tests."""

    sentinel_collection = "COPERNICUS/S2_SR_HARMONIZED"
    max_cloud_cover = 20
    lookback_days = 30
    cloud_free_threshold = 0.1

    def __getattr__(self, name):
        return None


@pytest.mark.asyncio
async def test_returns_cached_record_without_calling_providers():
    client = FakeSupabaseClient()
    client.seed("environmental_data", [
        {"id": "1", "latitude": 32.585, "longitude": 73.492, "soil_ph": 7.1,
         "data_source": "SoilGrids", "retrieved_at": "2026-01-01T00:00:00Z"},
    ])
    repo = EnvironmentalRepository(client)
    soil = FakeEnvironmentProvider("SoilGrids")
    climate = FakeEnvironmentProvider("NASA POWER")
    service = EnvironmentDataService(repo, [soil, climate])

    result = await service.get_environment(32.585, 73.492)

    assert result.available is True
    assert result.record["soil_ph"] == 7.1
    assert soil.calls == []  # cache hit — live providers never touched
    assert climate.calls == []


@pytest.mark.asyncio
async def test_cache_miss_falls_back_to_live_providers_and_caches_result():
    client = FakeSupabaseClient()  # empty cache
    repo = EnvironmentalRepository(client)
    soil = FakeEnvironmentProvider("SoilGrids", reading=EnvironmentalReading(soil_ph=6.8, clay=22.0))
    climate = FakeEnvironmentProvider("NASA POWER", reading=EnvironmentalReading(temperature=28.5, rainfall=650.0))
    service = EnvironmentDataService(repo, [soil, climate])

    result = await service.get_environment(32.585, 73.492)

    assert result.available is True
    assert result.record["soil_ph"] == 6.8
    assert result.record["temperature"] == 28.5
    assert "SoilGrids" in result.record["data_source"]
    assert "NASA POWER" in result.record["data_source"]
    # it should now be cached
    cached = await repo.find_near(32.585, 73.492)
    assert cached is not None
    assert cached["soil_ph"] == 6.8


@pytest.mark.asyncio
async def test_one_provider_failing_does_not_block_the_other():
    client = FakeSupabaseClient()
    repo = EnvironmentalRepository(client)
    soil = FakeEnvironmentProvider("SoilGrids", fail=True)
    climate = FakeEnvironmentProvider("NASA POWER", reading=EnvironmentalReading(temperature=30.0))
    service = EnvironmentDataService(repo, [soil, climate])

    result = await service.get_environment(32.585, 73.492)

    assert result.available is True
    assert result.record["temperature"] == 30.0
    assert result.record.get("soil_ph") is None
    assert result.record["data_source"] == "NASA POWER"


@pytest.mark.asyncio
async def test_all_providers_failing_or_empty_reports_unavailable_honestly():
    client = FakeSupabaseClient()
    repo = EnvironmentalRepository(client)
    soil = FakeEnvironmentProvider("SoilGrids", fail=True)
    climate = FakeEnvironmentProvider("NASA POWER", reading=None)  # reachable but no data for this point
    service = EnvironmentDataService(repo, [soil, climate])

    result = await service.get_environment(0.0, 0.0)

    assert result.available is False
    assert result.record is None
    assert result.message == "Data unavailable for this location."
async def test_merges_three_providers(self):
    """Proves the soil + climate + Sentinel-2 fields all merge into one
    EnvironmentalReading, per the same merge behavior already used for
    two providers."""
    soil = FakeEnvironmentProvider(reading=EnvironmentalReading(soil_ph=6.8, clay=22.0, sand=41.0, organic_carbon=9.5))
    climate = FakeEnvironmentProvider(reading=EnvironmentalReading(temperature=24.1, rainfall=680.0))
    sentinel = FakeEnvironmentProvider(reading=EnvironmentalReading(ndvi=0.42, ndwi=0.11, land_cover="Cropland"))

    service = EnvironmentDataService([soil, climate, sentinel])
    result = await service.get_environment(32.585, 73.492)

    assert result.soil_ph == 6.8
    assert result.temperature == 24.1
    assert result.ndvi == 0.42
    assert result.land_cover == "Cropland"


async def test_sentinel_provider_returns_none_when_no_cloud_free_image(self, monkeypatch):
    """No cloud-free image in the lookback window is a legitimate 'no
    data' — must return None, not raise."""
    import app.services.environment.sentinel_provider as mod

    class FakeCollection:
        def filterBounds(self, *_): return self
        def filterDate(self, *_): return self
        def filter(self, *_): return self
        def sort(self, *_a, **_k): return self
        def size(self): return self
        def getInfo(self): return 0  # empty collection

    monkeypatch.setattr(mod, "gee_client", type("_", (), {"ensure_initialized": lambda *_a, **_k: _async_noop()})())
    monkeypatch.setattr(mod.ee, "ImageCollection", lambda *_: FakeCollection())
    monkeypatch.setattr(mod.ee, "Geometry", type("_", (), {"Point": staticmethod(lambda *_: type("_", (), {"buffer": lambda self, *_: self})())}))
    monkeypatch.setattr(mod.ee, "Date", lambda *_: type("_", (), {"advance": lambda self, *_: self})())

    provider = mod.SentinelProvider(settings=FakeSettings())
    result = await provider.fetch(32.585, 73.492)
    assert result is None


async def _async_noop():
    return None