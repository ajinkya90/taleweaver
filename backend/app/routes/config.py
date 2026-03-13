from pathlib import Path

import yaml
from fastapi import APIRouter

router = APIRouter(prefix="/api")

DATA_DIR = Path(__file__).parent.parent / "data"

# Load YAML data once at import time
with open(DATA_DIR / "genres.yaml") as f:
    _genres = yaml.safe_load(f)

with open(DATA_DIR / "historical_events.yaml") as f:
    _historical_events = yaml.safe_load(f)


@router.get("/genres")
async def get_genres():
    return _genres


@router.get("/historical-events")
async def get_historical_events():
    return _historical_events
