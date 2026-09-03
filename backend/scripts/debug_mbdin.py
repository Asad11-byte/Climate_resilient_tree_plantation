"""Debug script — tests several SoilGrids sampling strategies against
Mandi Bahauddin to find one that returns real values."""
import os
from dotenv import load_dotenv

load_dotenv()
import ee

EMAIL = os.environ["GEE_SERVICE_ACCOUNT_EMAIL"]
KEY_PATH = os.environ["GEE_SERVICE_ACCOUNT_KEY_PATH"]
LAT, LON = 32.585, 73.492

print(f"Authenticating as {EMAIL}...")
ee.Initialize(ee.ServiceAccountCredentials(EMAIL, KEY_PATH))
print("Auth OK\n")

point = ee.Geometry.Point([LON, LAT])

print("=== SoilGrids sampling strategies ===")
img = ee.Image("projects/soilgrids-isric/phh2o_mean").select("phh2o_0-5cm_mean")
native_crs = img.projection()
print("  Native projection:", native_crs.getInfo())

strategies = {
    "A: mean, buffer(250), default crs": lambda: img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(250), scale=250, maxPixels=1e8
    ),
    "B: first, point directly, tileScale=4": lambda: img.reduceRegion(
        reducer=ee.Reducer.first(), geometry=point, scale=250, tileScale=4
    ),
    "C: mean, buffer(500), bestEffort=True": lambda: img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(500), bestEffort=True, tileScale=4
    ),
    "D: mean, buffer(250), explicit native crs": lambda: img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(250), crs=native_crs, scale=250, maxPixels=1e8
    ),
}

for label, fn in strategies.items():
    try:
        print(f"  {label}: {fn().getInfo()}")
    except Exception as exc:
        print(f"  {label}: ERROR — {exc}")