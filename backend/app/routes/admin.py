import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db import (
    _get_admin_emails,
    add_allowed_email,
    get_stories,
    get_stories_count,
    get_story,
    list_allowed_emails,
    remove_allowed_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin")


def _require_admin(request: Request) -> str:
    email = getattr(request.state, "user_email", "")
    if not email or email not in _get_admin_emails():
        raise HTTPException(status_code=403, detail="Admin access required")
    return email


class AddEmailRequest(BaseModel):
    email: str


@router.get("/me")
async def admin_me(request: Request):
    email = getattr(request.state, "user_email", "")
    is_admin = email in _get_admin_emails() if email else False
    return {"email": email, "is_admin": is_admin}


@router.get("/emails")
async def admin_list_emails(request: Request):
    _require_admin(request)
    emails = await list_allowed_emails()
    for e in emails:
        if e.get("added_at"):
            e["added_at"] = e["added_at"].isoformat()
    return {"emails": emails}


@router.post("/emails")
async def admin_add_email(body: AddEmailRequest, request: Request):
    _require_admin(request)
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    added = await add_allowed_email(email)
    if not added:
        raise HTTPException(status_code=409, detail="Email already exists")
    return {"email": email, "status": "added"}


@router.delete("/emails/{email}")
async def admin_remove_email(email: str, request: Request):
    _require_admin(request)
    removed = await remove_allowed_email(email)
    if not removed:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"email": email, "status": "removed"}


@router.get("/stories")
async def admin_list_stories(request: Request, limit: int = 20, offset: int = 0):
    _require_admin(request)
    stories = await get_stories(limit=min(limit, 100), offset=offset)
    total = await get_stories_count()
    for s in stories:
        if s.get("created_at"):
            s["created_at"] = s["created_at"].isoformat()
        if s.get("job_id"):
            s["job_id"] = str(s["job_id"])
    return {"stories": stories, "total": total, "limit": limit, "offset": offset}


@router.get("/stories/{story_id}")
async def admin_get_story(story_id: int, request: Request):
    _require_admin(request)
    story = await get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.get("created_at"):
        story["created_at"] = story["created_at"].isoformat()
    if story.get("job_id"):
        story["job_id"] = str(story["job_id"])
    return story
