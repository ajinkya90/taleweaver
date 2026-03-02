from pathlib import Path

import yaml
from fastapi import APIRouter

router = APIRouter(prefix="/api")

DATA_DIR = Path(__file__).parent.parent / "data"


@router.get("/genres")
async def get_genres():
    with open(DATA_DIR / "genres.yaml") as f:
        return yaml.safe_load(f)


@router.get("/historical-events")
async def get_historical_events():
    with open(DATA_DIR / "historical_events.yaml") as f:
        return yaml.safe_load(f)
