import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.db import (
    get_story_audio,
    get_user_stories,
    get_user_stories_count,
    get_user_story,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/my-stories")


def _get_user_email(request: Request) -> str:
    email = getattr(request.state, "user_email", "")
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return email


@router.get("")
async def list_my_stories(request: Request, limit: int = 20, offset: int = 0):
    email = _get_user_email(request)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    stories = await get_user_stories(email, limit=limit, offset=offset)
    total = await get_user_stories_count(email)
    for s in stories:
        if s.get("created_at"):
            s["created_at"] = s["created_at"].isoformat()
    return {"stories": stories, "total": total, "limit": limit, "offset": offset}


@router.get("/{story_id}")
async def get_my_story(story_id: int, request: Request):
    email = _get_user_email(request)
    story = await get_user_story(story_id, email)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.get("created_at"):
        story["created_at"] = story["created_at"].isoformat()
    if story.get("job_id"):
        story["job_id"] = str(story["job_id"])
    return story


@router.get("/{story_id}/audio")
async def get_my_story_audio(story_id: int, request: Request):
    email = _get_user_email(request)
    story = await get_user_story(story_id, email)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    audio = await get_story_audio(story_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not available")
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="story-{story_id}.mp3"',
            "Content-Length": str(len(audio)),
        },
    )
