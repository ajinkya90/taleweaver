from pydantic import BaseModel, Field
from typing import Optional


class KidProfile(BaseModel):
    name: str
    age: int = Field(ge=3, le=12)
    favorite_animal: Optional[str] = None
    favorite_color: Optional[str] = None
    hobby: Optional[str] = None
    best_friend: Optional[str] = None
    pet_name: Optional[str] = None
    personality: Optional[str] = None


class CustomStoryRequest(BaseModel):
    kid: KidProfile
    genre: str
    description: str
    mood: Optional[str] = None      # exciting, heartwarming, funny, mysterious
    length: Optional[str] = None    # short, medium, long


class HistoricalStoryRequest(BaseModel):
    kid: KidProfile
    event_id: str
    mood: Optional[str] = None      # exciting, heartwarming, funny, mysterious
    length: Optional[str] = None    # short, medium, long
