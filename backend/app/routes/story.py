import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.graph.pipeline import create_story_pipeline
from app.models.requests import CustomStoryRequest, HistoricalStoryRequest
from app.models.responses import JobCreatedResponse, JobStatusResponse, JobCompleteResponse

router = APIRouter(prefix="/api/story")

DATA_DIR = Path(__file__).parent.parent / "data"

# In-memory job store
jobs: dict[str, dict] = {}


def _format_kid_details(kid) -> str:
    parts = []
    if kid.favorite_animal:
        parts.append(f"Favorite animal: {kid.favorite_animal}")
    if kid.favorite_color:
        parts.append(f"Favorite color: {kid.favorite_color}")
    if kid.hobby:
        parts.append(f"Hobby: {kid.hobby}")
    if kid.best_friend:
        parts.append(f"Best friend: {kid.best_friend}")
    if kid.pet_name:
        parts.append(f"Pet: {kid.pet_name}")
    if kid.personality:
        parts.append(f"Personality: {kid.personality}")
    return ". ".join(parts)


def _load_event(event_id: str) -> Optional[dict]:
    with open(DATA_DIR / "historical_events.yaml") as f:
        events = yaml.safe_load(f)
    for event in events:
        if event["id"] == event_id:
            return event
    return None


async def run_pipeline(job_id: str, state: dict):
    try:
        pipeline = create_story_pipeline()

        logger.info(f"[{job_id}] Starting pipeline: type={state['story_type']}, kid={state['kid_name']}, age={state['kid_age']}")
        jobs[job_id]["current_stage"] = "writing"
        result = await pipeline.ainvoke(state)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["current_stage"] = "done"
        jobs[job_id]["title"] = result["title"]
        jobs[job_id]["duration_seconds"] = result["duration_seconds"]
        jobs[job_id]["final_audio"] = result["final_audio"]

        logger.info(f"[{job_id}] Pipeline complete: title='{result['title']}', duration={result['duration_seconds']}s")
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("/custom", response_model=JobCreatedResponse)
async def create_custom_story(request: CustomStoryRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "current_stage": "writing",
        "stages": ["writing", "splitting", "synthesizing", "stitching"],
    }

    state = {
        "kid_name": request.kid.name,
        "kid_age": request.kid.age,
        "kid_details": _format_kid_details(request.kid),
        "story_type": "custom",
        "genre": request.genre,
        "description": request.description,
        "event_id": None,
        "event_data": None,
        "mood": request.mood,
        "length": request.length,
        "story_text": "",
        "title": "",
        "segments": [],
        "audio_segments": [],
        "final_audio": b"",
        "duration_seconds": 0,
        "error": None,
    }

    asyncio.create_task(run_pipeline(job_id, state))

    return JobCreatedResponse(
        job_id=job_id,
        status="processing",
        stages=["writing", "splitting", "synthesizing", "stitching"],
        current_stage="writing",
    )


@router.post("/historical", response_model=JobCreatedResponse)
async def create_historical_story(request: HistoricalStoryRequest):
    event_data = _load_event(request.event_id)
    if not event_data:
        raise HTTPException(status_code=404, detail=f"Event '{request.event_id}' not found")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "current_stage": "writing",
        "stages": ["writing", "splitting", "synthesizing", "stitching"],
    }

    state = {
        "kid_name": request.kid.name,
        "kid_age": request.kid.age,
        "kid_details": _format_kid_details(request.kid),
        "story_type": "historical",
        "genre": None,
        "description": None,
        "event_id": request.event_id,
        "event_data": event_data,
        "mood": request.mood,
        "length": request.length,
        "story_text": "",
        "title": "",
        "segments": [],
        "audio_segments": [],
        "final_audio": b"",
        "duration_seconds": 0,
        "error": None,
    }

    asyncio.create_task(run_pipeline(job_id, state))

    return JobCreatedResponse(
        job_id=job_id,
        status="processing",
        stages=["writing", "splitting", "synthesizing", "stitching"],
        current_stage="writing",
    )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == "complete":
        return JobCompleteResponse(
            job_id=job_id,
            status="complete",
            title=job["title"],
            duration_seconds=job["duration_seconds"],
            audio_url=f"/api/story/audio/{job_id}",
        )

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        current_stage=job.get("current_stage", ""),
        progress=job.get("progress", 0),
        total_segments=job.get("total_segments", 0),
    )


@router.get("/audio/{job_id}")
async def get_audio(job_id: str, download: bool = False):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "complete" or "final_audio" not in job:
        raise HTTPException(status_code=404, detail="Audio not ready")

    audio_bytes = job["final_audio"]
    disposition = "attachment" if download else "inline"

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'{disposition}; filename="story-{job_id}.mp3"',
            "Content-Length": str(len(audio_bytes)),
            "Accept-Ranges": "bytes",
        },
    )
