import asyncio
import logging
import time
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

# Max age for completed jobs (1 hour)
JOB_TTL_SECONDS = 3600


def _cleanup_old_jobs():
    """Remove completed/failed jobs older than JOB_TTL_SECONDS."""
    now = time.time()
    expired = [
        jid for jid, job in jobs.items()
        if job["status"] in ("complete", "failed")
        and now - job.get("created_at", now) > JOB_TTL_SECONDS
    ]
    for jid in expired:
        del jobs[jid]
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired jobs")


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


# Cache YAML data at module level
_events_cache: Optional[list] = None


def _load_events() -> list:
    global _events_cache
    if _events_cache is None:
        with open(DATA_DIR / "historical_events.yaml") as f:
            _events_cache = yaml.safe_load(f)
    return _events_cache


def _load_event(event_id: str) -> Optional[dict]:
    for event in _load_events():
        if event["id"] == event_id:
            return event
    return None


# Maps LangGraph node names to frontend stage names
NODE_TO_STAGE = {
    "story_writer": "writing",
    "script_splitter": "splitting",
    "voice_synthesizer": "synthesizing",
    "audio_stitcher": "stitching",
}
STAGE_ORDER = list(NODE_TO_STAGE.keys())


def _friendly_error(e: Exception) -> str:
    """Convert raw exceptions into user-friendly error messages."""
    msg = str(e).lower()
    if "quota_exceeded" in msg or "quota" in msg:
        return "ElevenLabs voice generation quota exceeded. Please upgrade your plan or wait for it to reset."
    if "invalid api key" in msg or "invalid_api_key" in msg:
        return "Invalid ElevenLabs API key. Please check your key in backend/.env."
    if "401" in msg and "elevenlabs" in msg:
        return "ElevenLabs authentication failed. Please check your API key or quota."
    if "rate_limit" in msg or "rate limit" in msg or "429" in msg:
        return "API rate limit reached. Please wait a moment and try again."
    if "timeout" in msg or "timed out" in msg:
        return "The request timed out. Please try again."
    if "anthropic" in msg or "openai" in msg or "groq" in msg:
        return "LLM provider error. Please check your API key and try again."
    return "Something unexpected went wrong. Check the server logs for details."


async def run_pipeline(job_id: str, state: dict):
    try:
        pipeline = create_story_pipeline()

        logger.info(f"[{job_id}] Starting pipeline: type={state['story_type']}")
        jobs[job_id]["current_stage"] = "writing"

        # Stream node-by-node to track progress
        final_state = None
        async for event in pipeline.astream(state):
            # event is {node_name: node_output_dict}
            for node_name in event:
                # After a node completes, advance to the next stage
                idx = STAGE_ORDER.index(node_name) if node_name in STAGE_ORDER else -1
                if idx + 1 < len(STAGE_ORDER):
                    next_stage = NODE_TO_STAGE[STAGE_ORDER[idx + 1]]
                    jobs[job_id]["current_stage"] = next_stage
                    logger.info(f"[{job_id}] Stage: {next_stage}")
                # Merge node output into our tracked state
                if final_state is None:
                    final_state = {**state, **event[node_name]}
                else:
                    final_state.update(event[node_name])

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["current_stage"] = "done"
        jobs[job_id]["title"] = final_state["title"]
        jobs[job_id]["duration_seconds"] = final_state["duration_seconds"]
        jobs[job_id]["final_audio"] = final_state["final_audio"]
        jobs[job_id]["transcript"] = final_state.get("story_text", "")

        logger.info(f"[{job_id}] Pipeline complete: title='{final_state['title']}', duration={final_state['duration_seconds']}s")
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = _friendly_error(e)


@router.post("/custom", response_model=JobCreatedResponse)
async def create_custom_story(request: CustomStoryRequest):
    _cleanup_old_jobs()

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "current_stage": "writing",
        "stages": ["writing", "splitting", "synthesizing", "stitching"],
        "created_at": time.time(),
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

    task = asyncio.create_task(run_pipeline(job_id, state))
    jobs[job_id]["_task"] = task

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

    _cleanup_old_jobs()

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "current_stage": "writing",
        "stages": ["writing", "splitting", "synthesizing", "stitching"],
        "created_at": time.time(),
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

    task = asyncio.create_task(run_pipeline(job_id, state))
    jobs[job_id]["_task"] = task

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
            transcript=job.get("transcript", ""),
        )

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        current_stage=job.get("current_stage", ""),
        progress=job.get("progress", 0),
        total_segments=job.get("total_segments", 0),
        error=job.get("error", ""),
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
