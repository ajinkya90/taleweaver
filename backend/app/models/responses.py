from pydantic import BaseModel
from typing import Optional


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
    stages: list[str]
    current_stage: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current_stage: str
    progress: int = 0
    total_segments: int = 0


class JobCompleteResponse(BaseModel):
    job_id: str
    status: str
    title: str
    duration_seconds: int
    audio_url: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
