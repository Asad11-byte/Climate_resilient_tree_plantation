"""Bare-minimum GEE auth check — no app imports, so failures here can only
be about the credential/project, not your code."""
import os
from dotenv import load_dotenv
import ee

load_dotenv()  # reads ./.env by default — run this script from the backend/ folder

EMAIL = os.environ["GEE_SERVICE_ACCOUNT_EMAIL"]
KEY_PATH = os.environ["GEE_SERVICE_ACCOUNT_KEY_PATH"]

print(f"Authenticating as {EMAIL}...")
credentials = ee.ServiceAccountCredentials(EMAIL, KEY_PATH)
ee.Initialize(credentials)

print("ee.Number(1).getInfo():", ee.Number(1).getInfo())

img = ee.Image("projects/soilgrids-isric/phh2o_mean")
print("Sample band names:", img.bandNames().getInfo()[:3])