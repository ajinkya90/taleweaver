# Audio Story Creator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web app where parents create personalized audio stories for kids, with custom story and historical adventure modes.

**Architecture:** FastAPI backend with LangGraph pipeline for story generation and ElevenLabs TTS. React (Vite) frontend with a step-by-step wizard. Job-based polling for async story generation.

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, ElevenLabs SDK, pydub, React 18, Vite, TypeScript, Tailwind CSS

---

### Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`

**Step 1: Create backend directory structure**

```bash
cd /path/to/audio-story-creator
mkdir -p backend/app/routes backend/app/graph/nodes backend/app/models backend/app/data backend/app/prompts
touch backend/app/__init__.py backend/app/routes/__init__.py backend/app/graph/__init__.py backend/app/graph/nodes/__init__.py backend/app/models/__init__.py backend/app/prompts/__init__.py
```

**Step 2: Create requirements.txt**

```
# backend/requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
langgraph==0.2.60
langchain-core==0.3.28
langchain-groq==0.2.4
langchain-openai==0.2.14
elevenlabs==1.15.0
pydub==0.25.1
python-dotenv==1.0.1
pyyaml==6.0.2
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

**Step 3: Create .env.example**

```
# backend/.env.example
GROQ_API_KEY=your-groq-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
LLM_PROVIDER=groq
# Options: groq, openai, anthropic
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ElevenLabs Voice IDs (find at https://elevenlabs.io/app/voice-library)
NARRATOR_VOICE_ID=pNInz6obpgDQGcFmaJgB
CHARACTER_MALE_VOICE_ID=ErXwobaYiN019PkySvjV
CHARACTER_FEMALE_VOICE_ID=EXAVITQu4vr4xnSDxMaL
CHARACTER_CHILD_VOICE_ID=jBpfuIE2acCO8z3wKNLl
```

**Step 4: Create config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    llm_provider: str = "groq"

    narrator_voice_id: str = "pNInz6obpgDQGcFmaJgB"
    character_male_voice_id: str = "ErXwobaYiN019PkySvjV"
    character_female_voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    character_child_voice_id: str = "jBpfuIE2acCO8z3wKNLl"

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 5: Create main.py with health check**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Audio Story Creator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

**Step 6: Create virtual env, install deps, verify server starts**

```bash
cd /path/to/audio-story-creator/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 &
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
kill %1
```

**Step 7: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend with FastAPI, deps, and config"
```

---

### Task 2: Pydantic Request/Response Models

**Files:**
- Create: `backend/app/models/requests.py`
- Create: `backend/app/models/responses.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_models.py
import pytest
from app.models.requests import KidProfile, CustomStoryRequest, HistoricalStoryRequest
from app.models.responses import JobCreatedResponse, JobStatusResponse, JobCompleteResponse


def test_kid_profile_required_fields():
    kid = KidProfile(name="Arjun", age=7)
    assert kid.name == "Arjun"
    assert kid.age == 7
    assert kid.favorite_animal is None


def test_kid_profile_all_fields():
    kid = KidProfile(
        name="Arjun", age=7, favorite_animal="tiger",
        favorite_color="blue", hobby="drawing",
        best_friend="Riya", pet_name="Bruno",
        personality="adventurous"
    )
    assert kid.favorite_animal == "tiger"
    assert kid.personality == "adventurous"


def test_kid_profile_age_validation():
    with pytest.raises(Exception):
        KidProfile(name="Arjun", age=2)
    with pytest.raises(Exception):
        KidProfile(name="Arjun", age=13)


def test_custom_story_request():
    req = CustomStoryRequest(
        kid=KidProfile(name="Arjun", age=7),
        genre="fantasy",
        description="A magical paintbrush"
    )
    assert req.genre == "fantasy"


def test_historical_story_request():
    req = HistoricalStoryRequest(
        kid=KidProfile(name="Arjun", age=7),
        event_id="shivaji-agra-escape"
    )
    assert req.event_id == "shivaji-agra-escape"


def test_job_created_response():
    resp = JobCreatedResponse(
        job_id="abc-123",
        status="processing",
        stages=["writing", "splitting", "synthesizing", "stitching"],
        current_stage="writing"
    )
    assert resp.job_id == "abc-123"


def test_job_status_response():
    resp = JobStatusResponse(
        job_id="abc-123",
        status="processing",
        current_stage="synthesizing",
        progress=3,
        total_segments=8
    )
    assert resp.progress == 3


def test_job_complete_response():
    resp = JobCompleteResponse(
        job_id="abc-123",
        status="complete",
        title="Arjun and the Magical Paintbrush",
        duration_seconds=285,
        audio_url="/api/story/audio/abc-123"
    )
    assert resp.title == "Arjun and the Magical Paintbrush"
```

**Step 2: Run test to verify it fails**

```bash
cd /path/to/audio-story-creator/backend
source venv/bin/activate
python -m pytest tests/test_models.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write requests.py**

```python
# backend/app/models/requests.py
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


class HistoricalStoryRequest(BaseModel):
    kid: KidProfile
    event_id: str
```

**Step 4: Write responses.py**

```python
# backend/app/models/responses.py
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
```

**Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_models.py -v
# Expected: All 8 tests PASS
```

**Step 6: Commit**

```bash
git add backend/app/models/ backend/tests/
git commit -m "feat: add Pydantic request/response models with validation"
```

---

### Task 3: Config Endpoints (Genres & Historical Events)

**Files:**
- Create: `backend/app/data/genres.yaml`
- Create: `backend/app/data/historical_events.yaml`
- Create: `backend/app/routes/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_config_routes.py`

**Step 1: Create genres.yaml**

```yaml
# backend/app/data/genres.yaml
- id: adventure
  name: Adventure
  description: Exciting journeys to unknown lands
  icon: "🗺️"

- id: fantasy
  name: Fantasy
  description: Magical worlds with mythical creatures
  icon: "🧙"

- id: bedtime
  name: Bedtime
  description: Calm, soothing stories to drift off to sleep
  icon: "🌙"

- id: funny
  name: Funny
  description: Silly stories that make you laugh
  icon: "😂"

- id: space
  name: Space
  description: Cosmic adventures among the stars
  icon: "🚀"

- id: underwater
  name: Underwater
  description: Deep sea explorations and ocean friends
  icon: "🐠"

- id: magical-forest
  name: Magical Forest
  description: Enchanted woods full of surprises
  icon: "🌳"
```

**Step 2: Create historical_events.yaml**

```yaml
# backend/app/data/historical_events.yaml
- id: shivaji-agra-escape
  title: "Shivaji Maharaj's Great Escape from Agra"
  figure: "Chhatrapati Shivaji Maharaj"
  year: 1666
  summary: "The brave Maratha king outwits the mighty Mughal emperor Aurangzeb and escapes from captivity in Agra."
  key_facts:
    - "Shivaji was summoned to Aurangzeb's court in Agra in 1666"
    - "He was placed under house arrest when he protested his treatment at court"
    - "He escaped by hiding in large fruit baskets carried by servants"
    - "He disguised himself as a sadhu (holy man) on the journey home"
    - "He safely returned to Maharashtra after months of travel"
  thumbnail: "shivaji-escape.webp"

- id: gandhi-salt-march
  title: "Gandhi's Salt March to Dandi"
  figure: "Mahatma Gandhi"
  year: 1930
  summary: "Gandhi leads thousands on a 240-mile march to the sea to make salt, defying British colonial law."
  key_facts:
    - "The British Salt Act of 1882 made it illegal for Indians to collect or sell salt"
    - "Gandhi began the march on March 12, 1930 from Sabarmati Ashram"
    - "He walked 240 miles over 24 days to the coastal village of Dandi"
    - "Thousands of people joined the march along the way"
    - "On April 6, Gandhi picked up a lump of natural salt from the shore"
  thumbnail: "gandhi-salt-march.webp"

- id: apollo-11-moon-landing
  title: "The First Moon Landing"
  figure: "Neil Armstrong"
  year: 1969
  summary: "Astronauts Neil Armstrong and Buzz Aldrin become the first humans to walk on the Moon."
  key_facts:
    - "Apollo 11 launched on July 16, 1969 from Kennedy Space Center"
    - "The crew was Neil Armstrong, Buzz Aldrin, and Michael Collins"
    - "Collins stayed in lunar orbit while Armstrong and Aldrin descended"
    - "Armstrong stepped onto the Moon on July 20, 1969"
    - "He said 'That's one small step for man, one giant leap for mankind'"
  thumbnail: "moon-landing.webp"

- id: wright-brothers-flight
  title: "The Wright Brothers' First Flight"
  figure: "Orville and Wilbur Wright"
  year: 1903
  summary: "Two bicycle mechanics from Ohio achieve the impossible — powered, controlled flight."
  key_facts:
    - "Orville and Wilbur Wright built their airplane, the Flyer, in their bicycle shop"
    - "They chose Kitty Hawk, North Carolina for its steady winds and soft sand"
    - "On December 17, 1903, Orville made the first flight lasting 12 seconds"
    - "They made four flights that day, the longest covering 852 feet in 59 seconds"
    - "Only five people witnessed the historic event"
  thumbnail: "wright-brothers.webp"

- id: rani-laxmibai-jhansi
  title: "Rani Laxmibai's Battle for Jhansi"
  figure: "Rani Laxmibai"
  year: 1858
  summary: "The fearless queen of Jhansi fights against the British East India Company to defend her kingdom."
  key_facts:
    - "Rani Laxmibai became queen of Jhansi after her husband's death in 1853"
    - "The British tried to annex Jhansi under the Doctrine of Lapse"
    - "She refused to give up her kingdom, declaring 'I shall not surrender my Jhansi'"
    - "She led her troops into battle on horseback with her young son on her back"
    - "She is remembered as one of the bravest freedom fighters in Indian history"
  thumbnail: "rani-laxmibai.webp"

- id: discovery-of-fire
  title: "When Humans Discovered Fire"
  figure: "Early Humans"
  year: -400000
  summary: "Follow our earliest ancestors as they discover how to control fire, changing humanity forever."
  key_facts:
    - "Early humans first used fire found naturally from lightning strikes or volcanic activity"
    - "They learned to keep fire burning by feeding it wood and dry grass"
    - "Fire provided warmth, protection from animals, and light at night"
    - "Cooking food over fire made it easier to eat and digest"
    - "The ability to control fire was one of humanity's greatest achievements"
  thumbnail: "discovery-of-fire.webp"
```

**Step 3: Write the failing test**

```python
# backend/tests/test_config_routes.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_genres():
    response = client.get("/api/genres")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
    assert data[0]["id"] == "adventure"
    assert "name" in data[0]
    assert "description" in data[0]


def test_get_historical_events():
    response = client.get("/api/historical-events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6
    first = data[0]
    assert "id" in first
    assert "title" in first
    assert "figure" in first
    assert "year" in first
    assert "summary" in first
    assert "key_facts" in first


def test_historical_event_has_shivaji():
    response = client.get("/api/historical-events")
    data = response.json()
    ids = [e["id"] for e in data]
    assert "shivaji-agra-escape" in ids
```

**Step 4: Run test to verify it fails**

```bash
python -m pytest tests/test_config_routes.py -v
# Expected: FAIL — 404 on /api/genres
```

**Step 5: Write config routes**

```python
# backend/app/routes/config.py
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
```

**Step 6: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.config import router as config_router

app.include_router(config_router)
```

**Step 7: Run tests to verify they pass**

```bash
python -m pytest tests/test_config_routes.py -v
# Expected: All 3 tests PASS
```

**Step 8: Commit**

```bash
git add backend/app/data/ backend/app/routes/config.py backend/app/main.py backend/tests/test_config_routes.py
git commit -m "feat: add genres and historical events config endpoints"
```

---

### Task 4: LLM Provider Setup

**Files:**
- Create: `backend/app/graph/llm.py`
- Test: `backend/tests/test_llm.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_llm.py
from unittest.mock import patch
from app.graph.llm import get_llm


def test_get_llm_groq():
    with patch("app.graph.llm.settings") as mock_settings:
        mock_settings.llm_provider = "groq"
        mock_settings.groq_api_key = "test-key"
        llm = get_llm()
        assert llm is not None


def test_get_llm_openai():
    with patch("app.graph.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        llm = get_llm()
        assert llm is not None


def test_get_llm_invalid_provider():
    with patch("app.graph.llm.settings") as mock_settings:
        mock_settings.llm_provider = "invalid"
        try:
            get_llm()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_llm.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write llm.py**

```python
# backend/app/graph/llm.py
from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile")
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_llm.py -v
# Expected: All 3 tests PASS
```

**Step 5: Commit**

```bash
git add backend/app/graph/llm.py backend/tests/test_llm.py
git commit -m "feat: add configurable LLM provider (Groq/OpenAI)"
```

---

### Task 5: LangGraph State & Prompts

**Files:**
- Create: `backend/app/graph/state.py`
- Create: `backend/app/prompts/custom_story.py`
- Create: `backend/app/prompts/historical_story.py`
- Test: `backend/tests/test_prompts.py`

**Step 1: Create graph state**

```python
# backend/app/graph/state.py
from typing import Optional
from typing_extensions import TypedDict


class Segment(TypedDict):
    speaker: str
    voice_type: str  # "narrator", "male", "female", "child"
    text: str


class StoryState(TypedDict):
    # Input
    kid_name: str
    kid_age: int
    kid_details: str  # Formatted optional details
    story_type: str  # "custom" or "historical"
    genre: Optional[str]
    description: Optional[str]
    event_id: Optional[str]
    event_data: Optional[dict]

    # Pipeline outputs
    story_text: str
    title: str
    segments: list[Segment]
    audio_segments: list[bytes]
    final_audio: bytes
    duration_seconds: int
    error: Optional[str]
```

**Step 2: Write the failing test for prompts**

```python
# backend/tests/test_prompts.py
from app.prompts.custom_story import build_custom_story_prompt
from app.prompts.historical_story import build_historical_story_prompt


def test_custom_prompt_includes_kid_name():
    prompt = build_custom_story_prompt(
        name="Arjun", age=7, details="loves tigers",
        genre="fantasy", description="A magical paintbrush"
    )
    assert "Arjun" in prompt
    assert "7" in prompt
    assert "fantasy" in prompt
    assert "magical paintbrush" in prompt


def test_custom_prompt_age_adaptation_young():
    prompt = build_custom_story_prompt(
        name="Ria", age=4, details="", genre="bedtime",
        description="A sleepy bunny"
    )
    assert "simple" in prompt.lower() or "short" in prompt.lower()


def test_custom_prompt_age_adaptation_older():
    prompt = build_custom_story_prompt(
        name="Ria", age=11, details="", genre="adventure",
        description="A treasure hunt"
    )
    assert "complex" in prompt.lower() or "detailed" in prompt.lower() or "rich" in prompt.lower()


def test_historical_prompt_includes_facts():
    event_data = {
        "title": "Shivaji's Escape",
        "figure": "Shivaji Maharaj",
        "year": 1666,
        "key_facts": ["Escaped in fruit baskets", "Disguised as sadhu"]
    }
    prompt = build_historical_story_prompt(
        name="Arjun", age=7, details="", event_data=event_data
    )
    assert "Arjun" in prompt
    assert "observer" in prompt.lower() or "watching" in prompt.lower()
    assert "fruit baskets" in prompt
    assert "Shivaji" in prompt


def test_historical_prompt_enforces_accuracy():
    event_data = {
        "title": "Test Event",
        "figure": "Test Figure",
        "year": 2000,
        "key_facts": ["Fact one"]
    }
    prompt = build_historical_story_prompt(
        name="Test", age=8, details="", event_data=event_data
    )
    assert "accurate" in prompt.lower() or "factual" in prompt.lower() or "historically" in prompt.lower()
```

**Step 3: Run test to verify it fails**

```bash
python -m pytest tests/test_prompts.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 4: Write custom_story.py prompt**

```python
# backend/app/prompts/custom_story.py

def _age_instructions(age: int) -> str:
    if age <= 5:
        return (
            "Use very simple words and short sentences. "
            "The story should be about 200-300 words (2-3 minutes when read aloud). "
            "Keep themes gentle and reassuring."
        )
    elif age <= 8:
        return (
            "Use moderate vocabulary appropriate for early readers. "
            "The story should be about 400-600 words (4-6 minutes when read aloud). "
            "Include mild adventure and excitement."
        )
    else:
        return (
            "Use rich, detailed language with more complex sentence structures. "
            "The story should be about 700-1000 words (7-10 minutes when read aloud). "
            "Include more complex plots and themes."
        )


def build_custom_story_prompt(
    name: str, age: int, details: str, genre: str, description: str
) -> str:
    age_guide = _age_instructions(age)

    return f"""You are a world-class children's storyteller. Write a {genre} story for a child.

IMPORTANT RULES:
- The main character of the story MUST be a child named {name}, who is {age} years old.
- {age_guide}
- Weave the child naturally into the story as the protagonist.
- The story must be safe, positive, and appropriate for children.
- Give the story a creative, engaging title.

CHILD'S DETAILS (weave these in naturally if provided):
{details if details else "No additional details provided."}

STORY CONCEPT:
Genre: {genre}
Description: {description}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [Your story title]
STORY:
[Your story text here. Use dialogue with character names. Format dialogue as: CharacterName: "dialogue text"]"""
```

**Step 5: Write historical_story.py prompt**

```python
# backend/app/prompts/historical_story.py

def _age_instructions(age: int) -> str:
    if age <= 5:
        return (
            "Use very simple words and short sentences. "
            "The story should be about 200-300 words (2-3 minutes when read aloud). "
            "Keep the historical events simple and easy to understand."
        )
    elif age <= 8:
        return (
            "Use moderate vocabulary appropriate for early readers. "
            "The story should be about 400-600 words (4-6 minutes when read aloud). "
            "Explain historical context in kid-friendly terms."
        )
    else:
        return (
            "Use rich, detailed language with more complex sentence structures. "
            "The story should be about 700-1000 words (7-10 minutes when read aloud). "
            "Include more historical detail and context."
        )


def build_historical_story_prompt(
    name: str, age: int, details: str, event_data: dict
) -> str:
    age_guide = _age_instructions(age)
    facts = "\n".join(f"- {f}" for f in event_data["key_facts"])

    return f"""You are a world-class children's storyteller who specializes in historically accurate stories.

IMPORTANT RULES:
- {name} (age {age}) is a silent observer who has been magically transported back in time to witness this event.
- {name} is watching the events unfold but does NOT change history. They are an invisible, time-traveling observer.
- You MUST be historically accurate and factual. Do NOT invent events that didn't happen.
- {age_guide}
- The story must be safe, positive, and appropriate for children.
- Make the experience vivid and immersive — describe what {name} sees, hears, and feels as they watch.

CHILD'S DETAILS:
{details if details else "No additional details provided."}

HISTORICAL EVENT:
Title: {event_data["title"]}
Historical Figure: {event_data["figure"]}
Year: {event_data["year"]}

KEY FACTS (you MUST include these accurately):
{facts}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [Your story title]
STORY:
[Your story text here. Use dialogue with character names. Format dialogue as: CharacterName: "dialogue text"]"""
```

**Step 6: Run tests to verify they pass**

```bash
python -m pytest tests/test_prompts.py -v
# Expected: All 5 tests PASS
```

**Step 7: Commit**

```bash
git add backend/app/graph/state.py backend/app/prompts/ backend/tests/test_prompts.py
git commit -m "feat: add graph state schema and story prompts with age adaptation"
```

---

### Task 6: Story Writer Node

**Files:**
- Create: `backend/app/graph/nodes/story_writer.py`
- Test: `backend/tests/test_story_writer.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_story_writer.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.graph.nodes.story_writer import story_writer


@pytest.mark.asyncio
async def test_story_writer_custom():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
        content='TITLE: Arjun and the Magic Tiger\nSTORY:\nOnce upon a time, Arjun found a glowing paintbrush.'
    ))

    with patch("app.graph.nodes.story_writer.get_llm", return_value=mock_llm):
        state = {
            "kid_name": "Arjun",
            "kid_age": 7,
            "kid_details": "loves tigers",
            "story_type": "custom",
            "genre": "fantasy",
            "description": "A magical paintbrush",
            "event_id": None,
            "event_data": None,
        }
        result = await story_writer(state)
        assert "story_text" in result
        assert "title" in result
        assert result["title"] == "Arjun and the Magic Tiger"
        assert "paintbrush" in result["story_text"]


@pytest.mark.asyncio
async def test_story_writer_historical():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
        content='TITLE: Arjun Witnesses the Great Escape\nSTORY:\nArjun blinked and found himself in Agra.'
    ))

    with patch("app.graph.nodes.story_writer.get_llm", return_value=mock_llm):
        state = {
            "kid_name": "Arjun",
            "kid_age": 7,
            "kid_details": "",
            "story_type": "historical",
            "genre": None,
            "description": None,
            "event_id": "shivaji-agra-escape",
            "event_data": {
                "title": "Shivaji's Escape",
                "figure": "Shivaji Maharaj",
                "year": 1666,
                "key_facts": ["Escaped in fruit baskets"]
            },
        }
        result = await story_writer(state)
        assert result["title"] == "Arjun Witnesses the Great Escape"
        assert "Agra" in result["story_text"]
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_story_writer.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write story_writer.py**

```python
# backend/app/graph/nodes/story_writer.py
from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.llm import get_llm
from app.graph.state import StoryState
from app.prompts.custom_story import build_custom_story_prompt
from app.prompts.historical_story import build_historical_story_prompt


async def story_writer(state: StoryState) -> dict:
    llm = get_llm()

    if state["story_type"] == "custom":
        prompt = build_custom_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            genre=state["genre"],
            description=state["description"],
        )
    else:
        prompt = build_historical_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            event_data=state["event_data"],
        )

    response = await llm.ainvoke([
        SystemMessage(content="You are a children's storyteller. Follow the instructions exactly."),
        HumanMessage(content=prompt),
    ])

    text = response.content
    title = ""
    story_text = text

    if "TITLE:" in text and "STORY:" in text:
        parts = text.split("STORY:", 1)
        title_part = parts[0]
        story_text = parts[1].strip()
        title = title_part.replace("TITLE:", "").strip()

    return {"story_text": story_text, "title": title}
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_story_writer.py -v
# Expected: All 2 tests PASS
```

**Step 5: Commit**

```bash
git add backend/app/graph/nodes/story_writer.py backend/tests/test_story_writer.py
git commit -m "feat: add story writer LangGraph node with custom/historical modes"
```

---

### Task 7: Script Splitter Node

**Files:**
- Create: `backend/app/graph/nodes/script_splitter.py`
- Test: `backend/tests/test_script_splitter.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_script_splitter.py
import pytest
from app.graph.nodes.script_splitter import script_splitter


@pytest.mark.asyncio
async def test_splits_narrator_and_dialogue():
    state = {
        "story_text": (
            'Once upon a time, Arjun found a magical cave. '
            'Arjun: "Wow, this is amazing!" '
            'A wise old owl sat on a branch. '
            'Owl: "Welcome, young traveler." '
            'Arjun smiled and walked deeper into the cave.'
        ),
        "kid_name": "Arjun",
    }
    result = await script_splitter(state)
    segments = result["segments"]
    assert len(segments) > 0
    narr = [s for s in segments if s["speaker"] == "narrator"]
    dial = [s for s in segments if s["speaker"] != "narrator"]
    assert len(narr) > 0
    assert len(dial) > 0


@pytest.mark.asyncio
async def test_assigns_voice_types():
    state = {
        "story_text": (
            'The king stood tall. '
            'King: "We march at dawn!" '
            'Princess: "I will join you, father." '
            'Arjun: "Can I come too?"'
        ),
        "kid_name": "Arjun",
    }
    result = await script_splitter(state)
    segments = result["segments"]
    voice_types = {s["voice_type"] for s in segments}
    assert "narrator" in voice_types


@pytest.mark.asyncio
async def test_no_dialogue_all_narrator():
    state = {
        "story_text": "Once upon a time there was a beautiful garden. The flowers bloomed every spring.",
        "kid_name": "Arjun",
    }
    result = await script_splitter(state)
    segments = result["segments"]
    assert len(segments) == 1
    assert segments[0]["speaker"] == "narrator"
    assert segments[0]["voice_type"] == "narrator"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_script_splitter.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write script_splitter.py**

```python
# backend/app/graph/nodes/script_splitter.py
import re

from app.graph.state import Segment, StoryState

# Pattern matches: CharacterName: "dialogue text"
DIALOGUE_PATTERN = re.compile(r'(\w[\w\s]*?):\s*"([^"]+)"')


def _assign_voice_type(speaker: str, kid_name: str) -> str:
    if speaker == "narrator":
        return "narrator"
    if speaker.lower() == kid_name.lower():
        return "child"
    # Simple heuristic: assign based on common gendered terms
    female_hints = {"queen", "princess", "mother", "mom", "sister", "aunt", "rani", "goddess", "witch", "fairy"}
    if speaker.lower() in female_hints:
        return "female"
    return "male"


async def script_splitter(state: StoryState) -> dict:
    text = state["story_text"]
    kid_name = state["kid_name"]
    segments: list[Segment] = []

    last_end = 0
    for match in DIALOGUE_PATTERN.finditer(text):
        start = match.start()
        # Narrator text before this dialogue
        narrator_text = text[last_end:start].strip()
        if narrator_text:
            segments.append({
                "speaker": "narrator",
                "voice_type": "narrator",
                "text": narrator_text,
            })

        speaker = match.group(1).strip()
        dialogue = match.group(2).strip()
        segments.append({
            "speaker": speaker,
            "voice_type": _assign_voice_type(speaker, kid_name),
            "text": dialogue,
        })
        last_end = match.end()

    # Remaining narrator text after last dialogue
    remaining = text[last_end:].strip()
    if remaining:
        segments.append({
            "speaker": "narrator",
            "voice_type": "narrator",
            "text": remaining,
        })

    # If no segments found (no dialogue), treat entire text as narrator
    if not segments:
        segments.append({
            "speaker": "narrator",
            "voice_type": "narrator",
            "text": text.strip(),
        })

    return {"segments": segments}
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_script_splitter.py -v
# Expected: All 3 tests PASS
```

**Step 5: Commit**

```bash
git add backend/app/graph/nodes/script_splitter.py backend/tests/test_script_splitter.py
git commit -m "feat: add script splitter node with dialogue parsing and voice assignment"
```

---

### Task 8: Voice Synthesizer Node

**Files:**
- Create: `backend/app/graph/nodes/voice_synthesizer.py`
- Test: `backend/tests/test_voice_synthesizer.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_voice_synthesizer.py
import pytest
from unittest.mock import patch, MagicMock
from app.graph.nodes.voice_synthesizer import voice_synthesizer


@pytest.mark.asyncio
async def test_synthesizes_all_segments():
    fake_audio = b"fake-audio-bytes"

    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([fake_audio])

    with patch("app.graph.nodes.voice_synthesizer.ElevenLabs", return_value=mock_client):
        state = {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Once upon a time."},
                {"speaker": "Arjun", "voice_type": "child", "text": "Hello!"},
                {"speaker": "King", "voice_type": "male", "text": "Welcome!"},
            ],
        }
        result = await voice_synthesizer(state)
        assert len(result["audio_segments"]) == 3
        assert all(isinstance(a, bytes) for a in result["audio_segments"])


@pytest.mark.asyncio
async def test_maps_voice_types_to_voice_ids():
    calls = []

    mock_client = MagicMock()
    def capture_call(**kwargs):
        calls.append(kwargs)
        return iter([b"audio"])
    mock_client.text_to_speech.convert.side_effect = capture_call

    with patch("app.graph.nodes.voice_synthesizer.ElevenLabs", return_value=mock_client):
        state = {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Text."},
                {"speaker": "Queen", "voice_type": "female", "text": "Text."},
            ],
        }
        result = await voice_synthesizer(state)
        assert len(calls) == 2
        # Verify different voice IDs used
        assert calls[0]["voice_id"] != calls[1]["voice_id"]
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_voice_synthesizer.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write voice_synthesizer.py**

```python
# backend/app/graph/nodes/voice_synthesizer.py
from elevenlabs import ElevenLabs

from app.config import settings
from app.graph.state import StoryState


def _get_voice_id(voice_type: str) -> str:
    mapping = {
        "narrator": settings.narrator_voice_id,
        "male": settings.character_male_voice_id,
        "female": settings.character_female_voice_id,
        "child": settings.character_child_voice_id,
    }
    return mapping.get(voice_type, settings.narrator_voice_id)


async def voice_synthesizer(state: StoryState) -> dict:
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    audio_segments: list[bytes] = []

    for segment in state["segments"]:
        voice_id = _get_voice_id(segment["voice_type"])
        audio_iter = client.text_to_speech.convert(
            voice_id=voice_id,
            text=segment["text"],
            model_id="eleven_multilingual_v2",
        )
        audio_bytes = b"".join(audio_iter)
        audio_segments.append(audio_bytes)

    return {"audio_segments": audio_segments}
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_voice_synthesizer.py -v
# Expected: All 2 tests PASS
```

**Step 5: Commit**

```bash
git add backend/app/graph/nodes/voice_synthesizer.py backend/tests/test_voice_synthesizer.py
git commit -m "feat: add voice synthesizer node with ElevenLabs multi-voice TTS"
```

---

### Task 9: Audio Stitcher Node

**Files:**
- Create: `backend/app/graph/nodes/audio_stitcher.py`
- Test: `backend/tests/test_audio_stitcher.py`

**Step 1: Write the failing test**

Note: pydub requires ffmpeg. Tests use actual small audio generation via pydub to create test fixtures.

```python
# backend/tests/test_audio_stitcher.py
import io
import pytest
from pydub import AudioSegment
from pydub.generators import Sine
from app.graph.nodes.audio_stitcher import audio_stitcher


def _make_test_audio(duration_ms: int = 500) -> bytes:
    """Generate a short sine wave as MP3 bytes."""
    tone = Sine(440).to_audio_segment(duration=duration_ms)
    buf = io.BytesIO()
    tone.export(buf, format="mp3")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_stitches_multiple_segments():
    seg1 = _make_test_audio(300)
    seg2 = _make_test_audio(500)
    seg3 = _make_test_audio(200)

    state = {"audio_segments": [seg1, seg2, seg3]}
    result = await audio_stitcher(state)

    assert "final_audio" in result
    assert isinstance(result["final_audio"], bytes)
    assert len(result["final_audio"]) > 0
    assert "duration_seconds" in result
    assert result["duration_seconds"] > 0


@pytest.mark.asyncio
async def test_single_segment():
    seg = _make_test_audio(1000)
    state = {"audio_segments": [seg]}
    result = await audio_stitcher(state)
    assert result["duration_seconds"] >= 1


@pytest.mark.asyncio
async def test_adds_pauses_between_segments():
    seg1 = _make_test_audio(500)
    seg2 = _make_test_audio(500)

    state_single = {"audio_segments": [seg1]}
    result_single = await audio_stitcher(state_single)

    state_double = {"audio_segments": [seg1, seg2]}
    result_double = await audio_stitcher(state_double)

    # Two segments with a pause should be longer than just the sum
    assert result_double["duration_seconds"] >= result_single["duration_seconds"]
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_audio_stitcher.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write audio_stitcher.py**

```python
# backend/app/graph/nodes/audio_stitcher.py
import io

from pydub import AudioSegment

from app.graph.state import StoryState

PAUSE_MS = 500  # Half-second pause between segments


async def audio_stitcher(state: StoryState) -> dict:
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for i, audio_bytes in enumerate(state["audio_segments"]):
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        combined += segment
        if i < len(state["audio_segments"]) - 1:
            combined += pause

    buf = io.BytesIO()
    combined.export(buf, format="mp3")
    final_bytes = buf.getvalue()
    duration_seconds = int(len(combined) / 1000)

    return {"final_audio": final_bytes, "duration_seconds": duration_seconds}
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_audio_stitcher.py -v
# Expected: All 3 tests PASS (requires ffmpeg installed: brew install ffmpeg)
```

**Step 5: Commit**

```bash
git add backend/app/graph/nodes/audio_stitcher.py backend/tests/test_audio_stitcher.py
git commit -m "feat: add audio stitcher node with pydub MP3 concatenation"
```

---

### Task 10: LangGraph Pipeline Assembly

**Files:**
- Create: `backend/app/graph/pipeline.py`
- Test: `backend/tests/test_pipeline.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_pipeline.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.graph.pipeline import create_story_pipeline


def test_pipeline_creates_graph():
    pipeline = create_story_pipeline()
    assert pipeline is not None


@pytest.mark.asyncio
async def test_pipeline_runs_all_nodes():
    """Integration test with all nodes mocked."""
    nodes_called = []

    async def mock_story_writer(state):
        nodes_called.append("story_writer")
        return {
            "story_text": 'Narrator: "Once upon a time." Arjun: "Hello!"',
            "title": "Test Story"
        }

    async def mock_script_splitter(state):
        nodes_called.append("script_splitter")
        return {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Once upon a time."},
                {"speaker": "Arjun", "voice_type": "child", "text": "Hello!"},
            ]
        }

    async def mock_voice_synthesizer(state):
        nodes_called.append("voice_synthesizer")
        return {"audio_segments": [b"audio1", b"audio2"]}

    async def mock_audio_stitcher(state):
        nodes_called.append("audio_stitcher")
        return {"final_audio": b"final-audio", "duration_seconds": 120}

    with patch("app.graph.pipeline.story_writer", mock_story_writer), \
         patch("app.graph.pipeline.script_splitter", mock_script_splitter), \
         patch("app.graph.pipeline.voice_synthesizer", mock_voice_synthesizer), \
         patch("app.graph.pipeline.audio_stitcher", mock_audio_stitcher):

        pipeline = create_story_pipeline()
        result = await pipeline.ainvoke({
            "kid_name": "Arjun",
            "kid_age": 7,
            "kid_details": "",
            "story_type": "custom",
            "genre": "fantasy",
            "description": "A test story",
            "event_id": None,
            "event_data": None,
            "story_text": "",
            "title": "",
            "segments": [],
            "audio_segments": [],
            "final_audio": b"",
            "duration_seconds": 0,
            "error": None,
        })

    assert nodes_called == ["story_writer", "script_splitter", "voice_synthesizer", "audio_stitcher"]
    assert result["title"] == "Test Story"
    assert result["final_audio"] == b"final-audio"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_pipeline.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: Write pipeline.py**

```python
# backend/app/graph/pipeline.py
from langgraph.graph import StateGraph, END

from app.graph.state import StoryState
from app.graph.nodes.story_writer import story_writer
from app.graph.nodes.script_splitter import script_splitter
from app.graph.nodes.voice_synthesizer import voice_synthesizer
from app.graph.nodes.audio_stitcher import audio_stitcher


def create_story_pipeline():
    graph = StateGraph(StoryState)

    graph.add_node("story_writer", story_writer)
    graph.add_node("script_splitter", script_splitter)
    graph.add_node("voice_synthesizer", voice_synthesizer)
    graph.add_node("audio_stitcher", audio_stitcher)

    graph.set_entry_point("story_writer")
    graph.add_edge("story_writer", "script_splitter")
    graph.add_edge("script_splitter", "voice_synthesizer")
    graph.add_edge("voice_synthesizer", "audio_stitcher")
    graph.add_edge("audio_stitcher", END)

    return graph.compile()
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_pipeline.py -v
# Expected: All 2 tests PASS
```

**Step 5: Commit**

```bash
git add backend/app/graph/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat: assemble LangGraph pipeline with 4 nodes"
```

---

### Task 11: Story Routes (Job Management)

**Files:**
- Create: `backend/app/routes/story.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_story_routes.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_story_routes.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_custom_story_returns_job():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/custom", json={
            "kid": {"name": "Arjun", "age": 7},
            "genre": "fantasy",
            "description": "A magical adventure"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        assert data["current_stage"] == "writing"


def test_create_historical_story_returns_job():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/historical", json={
            "kid": {"name": "Arjun", "age": 7},
            "event_id": "shivaji-agra-escape"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


def test_historical_story_invalid_event():
    response = client.post("/api/story/historical", json={
        "kid": {"name": "Arjun", "age": 7},
        "event_id": "nonexistent-event"
    })
    assert response.status_code == 404


def test_get_job_status_not_found():
    response = client.get("/api/story/status/nonexistent-id")
    assert response.status_code == 404


def test_get_audio_not_found():
    response = client.get("/api/story/audio/nonexistent-id")
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_story_routes.py -v
# Expected: FAIL — 404 or import errors
```

**Step 3: Write story routes**

```python
# backend/app/routes/story.py
import asyncio
import uuid
from pathlib import Path

import yaml
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


def _load_event(event_id: str) -> dict | None:
    with open(DATA_DIR / "historical_events.yaml") as f:
        events = yaml.safe_load(f)
    for event in events:
        if event["id"] == event_id:
            return event
    return None


async def run_pipeline(job_id: str, state: dict):
    try:
        pipeline = create_story_pipeline()

        jobs[job_id]["current_stage"] = "writing"
        result = await pipeline.ainvoke(state)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["current_stage"] = "done"
        jobs[job_id]["title"] = result["title"]
        jobs[job_id]["duration_seconds"] = result["duration_seconds"]
        jobs[job_id]["final_audio"] = result["final_audio"]
    except Exception as e:
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
async def get_audio(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "complete" or "final_audio" not in job:
        raise HTTPException(status_code=404, detail="Audio not ready")

    return Response(
        content=job["final_audio"],
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="story-{job_id}.mp3"'},
    )
```

**Step 4: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.story import router as story_router

app.include_router(story_router)
```

**Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_story_routes.py -v
# Expected: All 5 tests PASS
```

**Step 6: Commit**

```bash
git add backend/app/routes/story.py backend/app/main.py backend/tests/test_story_routes.py
git commit -m "feat: add story routes with job management and async pipeline execution"
```

---

### Task 12: Frontend Scaffolding

**Files:**
- Create: `frontend/` (via Vite scaffold)
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

**Step 1: Scaffold React + Vite + TypeScript project**

```bash
cd /path/to/audio-story-creator
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
```

**Step 2: Configure Tailwind in vite.config.ts**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

**Step 3: Add Tailwind import to CSS**

Replace contents of `frontend/src/index.css`:

```css
@import "tailwindcss";
```

**Step 4: Create TypeScript types**

```typescript
// frontend/src/types/index.ts
export interface KidProfile {
  name: string;
  age: number;
  favorite_animal?: string;
  favorite_color?: string;
  hobby?: string;
  best_friend?: string;
  pet_name?: string;
  personality?: string;
}

export interface Genre {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface HistoricalEvent {
  id: string;
  title: string;
  figure: string;
  year: number;
  summary: string;
  key_facts: string[];
  thumbnail: string;
}

export interface JobCreatedResponse {
  job_id: string;
  status: string;
  stages: string[];
  current_stage: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  current_stage: string;
  progress: number;
  total_segments: number;
}

export interface JobCompleteResponse {
  job_id: string;
  status: string;
  title: string;
  duration_seconds: number;
  audio_url: string;
}

export type StoryType = "custom" | "historical";

export type WizardStep =
  | "profile"
  | "story-type"
  | "custom-form"
  | "historical-pick"
  | "generating"
  | "listen";
```

**Step 5: Create API client**

```typescript
// frontend/src/api/client.ts
import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
} from "../types";

const BASE = "/api";

export async function fetchGenres(): Promise<Genre[]> {
  const res = await fetch(`${BASE}/genres`);
  return res.json();
}

export async function fetchHistoricalEvents(): Promise<HistoricalEvent[]> {
  const res = await fetch(`${BASE}/historical-events`);
  return res.json();
}

export async function createCustomStory(
  kid: KidProfile,
  genre: string,
  description: string
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, genre, description }),
  });
  return res.json();
}

export async function createHistoricalStory(
  kid: KidProfile,
  eventId: string
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/historical`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, event_id: eventId }),
  });
  return res.json();
}

export async function pollJobStatus(
  jobId: string
): Promise<JobStatusResponse | JobCompleteResponse> {
  const res = await fetch(`${BASE}/story/status/${jobId}`);
  return res.json();
}

export function getAudioUrl(jobId: string): string {
  return `${BASE}/story/audio/${jobId}`;
}
```

**Step 6: Verify frontend starts**

```bash
cd /path/to/audio-story-creator/frontend
npm run dev &
curl http://localhost:5173
# Expected: HTML response
kill %1
```

**Step 7: Commit**

```bash
cd /path/to/audio-story-creator
git add frontend/
git commit -m "feat: scaffold React frontend with Vite, Tailwind, types, and API client"
```

---

### Task 13: Frontend Components — KidProfileForm

**Files:**
- Create: `frontend/src/components/KidProfileForm.tsx`

**Step 1: Build the component**

Use @frontend-design:frontend-design skill for styling guidance.

```typescript
// frontend/src/components/KidProfileForm.tsx
import { useState } from "react";
import type { KidProfile } from "../types";

interface Props {
  onSubmit: (profile: KidProfile) => void;
}

const PERSONALITIES = ["adventurous", "curious", "shy", "funny"];

export default function KidProfileForm({ onSubmit }: Props) {
  const [name, setName] = useState("");
  const [age, setAge] = useState(7);
  const [favoriteAnimal, setFavoriteAnimal] = useState("");
  const [favoriteColor, setFavoriteColor] = useState("");
  const [hobby, setHobby] = useState("");
  const [bestFriend, setBestFriend] = useState("");
  const [petName, setPetName] = useState("");
  const [personality, setPersonality] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const profile: KidProfile = {
      name,
      age,
      ...(favoriteAnimal && { favorite_animal: favoriteAnimal }),
      ...(favoriteColor && { favorite_color: favoriteColor }),
      ...(hobby && { hobby }),
      ...(bestFriend && { best_friend: bestFriend }),
      ...(petName && { pet_name: petName }),
      ...(personality && { personality }),
    };
    onSubmit(profile);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-lg mx-auto space-y-6">
      <h2 className="text-3xl font-bold text-center text-purple-700">
        Tell us about your child
      </h2>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Name *
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full px-4 py-2 border-2 border-purple-200 rounded-xl focus:border-purple-500 focus:outline-none"
          placeholder="Your child's name"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Age *
        </label>
        <select
          value={age}
          onChange={(e) => setAge(Number(e.target.value))}
          className="w-full px-4 py-2 border-2 border-purple-200 rounded-xl focus:border-purple-500 focus:outline-none"
        >
          {Array.from({ length: 10 }, (_, i) => i + 3).map((a) => (
            <option key={a} value={a}>{a} years old</option>
          ))}
        </select>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <p className="text-sm text-gray-500 mb-3">
          Optional details (makes the story more personal)
        </p>
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            value={favoriteAnimal}
            onChange={(e) => setFavoriteAnimal(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
            placeholder="Favorite animal"
          />
          <input
            type="text"
            value={favoriteColor}
            onChange={(e) => setFavoriteColor(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
            placeholder="Favorite color"
          />
          <input
            type="text"
            value={hobby}
            onChange={(e) => setHobby(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
            placeholder="Hobby"
          />
          <input
            type="text"
            value={bestFriend}
            onChange={(e) => setBestFriend(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
            placeholder="Best friend's name"
          />
          <input
            type="text"
            value={petName}
            onChange={(e) => setPetName(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
            placeholder="Pet's name"
          />
          <select
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
          >
            <option value="">Personality</option>
            {PERSONALITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={!name}
        className="w-full py-3 bg-purple-600 text-white font-bold rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Next
      </button>
    </form>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/KidProfileForm.tsx
git commit -m "feat: add KidProfileForm component"
```

---

### Task 14: Frontend Components — StoryTypeSelector, CustomStoryForm, HistoricalEventPicker

**Files:**
- Create: `frontend/src/components/StoryTypeSelector.tsx`
- Create: `frontend/src/components/CustomStoryForm.tsx`
- Create: `frontend/src/components/HistoricalEventPicker.tsx`

**Step 1: StoryTypeSelector**

```typescript
// frontend/src/components/StoryTypeSelector.tsx
import type { StoryType } from "../types";

interface Props {
  onSelect: (type: StoryType) => void;
}

export default function StoryTypeSelector({ onSelect }: Props) {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-3xl font-bold text-center text-purple-700">
        Choose your adventure
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <button
          onClick={() => onSelect("custom")}
          className="p-8 border-3 border-purple-200 rounded-2xl hover:border-purple-500 hover:shadow-lg transition-all text-left group"
        >
          <div className="text-5xl mb-4">✨</div>
          <h3 className="text-xl font-bold text-purple-700 group-hover:text-purple-800">
            Custom Story
          </h3>
          <p className="text-gray-600 mt-2">
            Create your own adventure — pick a genre and describe your story idea.
          </p>
        </button>

        <button
          onClick={() => onSelect("historical")}
          className="p-8 border-3 border-amber-200 rounded-2xl hover:border-amber-500 hover:shadow-lg transition-all text-left group"
        >
          <div className="text-5xl mb-4">🏛️</div>
          <h3 className="text-xl font-bold text-amber-700 group-hover:text-amber-800">
            Historical Adventure
          </h3>
          <p className="text-gray-600 mt-2">
            Travel through time and witness amazing moments in history.
          </p>
        </button>
      </div>
    </div>
  );
}
```

**Step 2: CustomStoryForm**

```typescript
// frontend/src/components/CustomStoryForm.tsx
import { useEffect, useState } from "react";
import type { Genre } from "../types";
import { fetchGenres } from "../api/client";

interface Props {
  onSubmit: (genre: string, description: string) => void;
  onBack: () => void;
}

export default function CustomStoryForm({ onSubmit, onBack }: Props) {
  const [genres, setGenres] = useState<Genre[]>([]);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    fetchGenres().then(setGenres);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(selectedGenre, description);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-3xl font-bold text-center text-purple-700">
        Design your story
      </h2>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Pick a genre
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {genres.map((genre) => (
            <button
              key={genre.id}
              type="button"
              onClick={() => setSelectedGenre(genre.id)}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                selectedGenre === genre.id
                  ? "border-purple-500 bg-purple-50"
                  : "border-gray-200 hover:border-purple-300"
              }`}
            >
              <div className="text-2xl">{genre.icon}</div>
              <div className="font-semibold mt-1">{genre.name}</div>
              <div className="text-xs text-gray-500">{genre.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          What should the story be about?
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={3}
          className="w-full px-4 py-2 border-2 border-purple-200 rounded-xl focus:border-purple-500 focus:outline-none"
          placeholder="A magical paintbrush that brings drawings to life..."
        />
      </div>

      <div className="flex gap-4">
        <button
          type="button"
          onClick={onBack}
          className="px-6 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!selectedGenre || !description}
          className="flex-1 py-3 bg-purple-600 text-white font-bold rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Create Story
        </button>
      </div>
    </form>
  );
}
```

**Step 3: HistoricalEventPicker**

```typescript
// frontend/src/components/HistoricalEventPicker.tsx
import { useEffect, useState } from "react";
import type { HistoricalEvent } from "../types";
import { fetchHistoricalEvents } from "../api/client";

interface Props {
  onSelect: (eventId: string) => void;
  onBack: () => void;
}

export default function HistoricalEventPicker({ onSelect, onBack }: Props) {
  const [events, setEvents] = useState<HistoricalEvent[]>([]);

  useEffect(() => {
    fetchHistoricalEvents().then(setEvents);
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-3xl font-bold text-center text-amber-700">
        Pick a moment in history
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {events.map((event) => (
          <button
            key={event.id}
            onClick={() => onSelect(event.id)}
            className="p-6 border-2 border-amber-200 rounded-xl hover:border-amber-500 hover:shadow-lg transition-all text-left"
          >
            <div className="flex justify-between items-start">
              <h3 className="font-bold text-amber-800">{event.title}</h3>
              <span className="text-sm text-amber-600 font-mono ml-2">
                {event.year > 0 ? event.year : `${Math.abs(event.year)} BC`}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{event.figure}</p>
            <p className="text-sm text-gray-500 mt-2">{event.summary}</p>
          </button>
        ))}
      </div>

      <button
        onClick={onBack}
        className="px-6 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
      >
        Back
      </button>
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/StoryTypeSelector.tsx frontend/src/components/CustomStoryForm.tsx frontend/src/components/HistoricalEventPicker.tsx
git commit -m "feat: add StoryTypeSelector, CustomStoryForm, and HistoricalEventPicker components"
```

---

### Task 15: Frontend Components — GeneratingScreen & AudioPlayer

**Files:**
- Create: `frontend/src/components/GeneratingScreen.tsx`
- Create: `frontend/src/components/AudioPlayer.tsx`

**Step 1: GeneratingScreen**

```typescript
// frontend/src/components/GeneratingScreen.tsx
interface Props {
  currentStage: string;
}

const STAGE_LABELS: Record<string, string> = {
  writing: "Writing your story...",
  splitting: "Preparing character voices...",
  synthesizing: "Recording the narration...",
  stitching: "Finishing up...",
};

export default function GeneratingScreen({ currentStage }: Props) {
  const label = STAGE_LABELS[currentStage] || "Creating your story...";

  return (
    <div className="max-w-md mx-auto text-center space-y-8 py-12">
      <div className="text-6xl animate-bounce">📖</div>
      <h2 className="text-2xl font-bold text-purple-700">{label}</h2>
      <div className="flex justify-center gap-2">
        {Object.keys(STAGE_LABELS).map((stage) => (
          <div
            key={stage}
            className={`h-2 w-16 rounded-full transition-colors ${
              stage === currentStage
                ? "bg-purple-500 animate-pulse"
                : Object.keys(STAGE_LABELS).indexOf(stage) <
                  Object.keys(STAGE_LABELS).indexOf(currentStage)
                ? "bg-purple-300"
                : "bg-gray-200"
            }`}
          />
        ))}
      </div>
      <p className="text-gray-500 text-sm">This usually takes about a minute</p>
    </div>
  );
}
```

**Step 2: AudioPlayer**

```typescript
// frontend/src/components/AudioPlayer.tsx
import { useRef, useState } from "react";

interface Props {
  title: string;
  audioUrl: string;
  durationSeconds: number;
  onCreateAnother: () => void;
}

export default function AudioPlayer({
  title,
  audioUrl,
  durationSeconds,
  onCreateAnother,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="max-w-lg mx-auto text-center space-y-6">
      <div className="text-5xl">🎧</div>
      <h2 className="text-2xl font-bold text-purple-700">{title}</h2>

      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={() =>
          setCurrentTime(audioRef.current?.currentTime || 0)
        }
        onEnded={() => setIsPlaying(false)}
      />

      <div className="bg-purple-50 rounded-2xl p-6 space-y-4">
        <input
          type="range"
          min={0}
          max={durationSeconds}
          value={currentTime}
          onChange={(e) => {
            const t = Number(e.target.value);
            if (audioRef.current) audioRef.current.currentTime = t;
            setCurrentTime(t);
          }}
          className="w-full accent-purple-600"
        />
        <div className="flex justify-between text-sm text-gray-500">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(durationSeconds)}</span>
        </div>
        <button
          onClick={togglePlay}
          className="w-16 h-16 bg-purple-600 text-white rounded-full text-2xl hover:bg-purple-700 transition-colors mx-auto flex items-center justify-center"
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
      </div>

      <div className="flex gap-4 justify-center">
        <a
          href={audioUrl}
          download
          className="px-6 py-3 border-2 border-purple-300 rounded-xl hover:bg-purple-50 transition-colors font-medium"
        >
          Download MP3
        </a>
        <button
          onClick={onCreateAnother}
          className="px-6 py-3 bg-purple-600 text-white font-bold rounded-xl hover:bg-purple-700 transition-colors"
        >
          Create Another Story
        </button>
      </div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/GeneratingScreen.tsx frontend/src/components/AudioPlayer.tsx
git commit -m "feat: add GeneratingScreen and AudioPlayer components"
```

---

### Task 16: App Component — Wizard Flow

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Wire up the wizard**

```typescript
// frontend/src/App.tsx
import { useCallback, useRef, useState } from "react";
import type { KidProfile, WizardStep } from "./types";
import KidProfileForm from "./components/KidProfileForm";
import StoryTypeSelector from "./components/StoryTypeSelector";
import CustomStoryForm from "./components/CustomStoryForm";
import HistoricalEventPicker from "./components/HistoricalEventPicker";
import GeneratingScreen from "./components/GeneratingScreen";
import AudioPlayer from "./components/AudioPlayer";
import {
  createCustomStory,
  createHistoricalStory,
  pollJobStatus,
  getAudioUrl,
} from "./api/client";

export default function App() {
  const [step, setStep] = useState<WizardStep>("profile");
  const [kidProfile, setKidProfile] = useState<KidProfile | null>(null);
  const [currentStage, setCurrentStage] = useState("writing");
  const [storyTitle, setStoryTitle] = useState("");
  const [storyDuration, setStoryDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState("");
  const [error, setError] = useState("");
  const pollingRef = useRef<ReturnType<typeof setInterval>>();

  const startPolling = useCallback((jobId: string) => {
    setStep("generating");
    setCurrentStage("writing");

    pollingRef.current = setInterval(async () => {
      try {
        const status = await pollJobStatus(jobId);
        if (status.status === "complete" && "title" in status) {
          clearInterval(pollingRef.current);
          setStoryTitle(status.title);
          setStoryDuration(status.duration_seconds);
          setAudioUrl(getAudioUrl(jobId));
          setStep("listen");
        } else if (status.status === "failed") {
          clearInterval(pollingRef.current);
          setError("Something went wrong. Please try again.");
          setStep("story-type");
        } else if ("current_stage" in status) {
          setCurrentStage(status.current_stage);
        }
      } catch {
        clearInterval(pollingRef.current);
        setError("Connection lost. Please try again.");
        setStep("story-type");
      }
    }, 2000);
  }, []);

  const handleCustomStory = async (genre: string, description: string) => {
    if (!kidProfile) return;
    setError("");
    const job = await createCustomStory(kidProfile, genre, description);
    startPolling(job.job_id);
  };

  const handleHistoricalStory = async (eventId: string) => {
    if (!kidProfile) return;
    setError("");
    const job = await createHistoricalStory(kidProfile, eventId);
    startPolling(job.job_id);
  };

  const handleCreateAnother = () => {
    setStep("story-type");
    setStoryTitle("");
    setStoryDuration(0);
    setAudioUrl("");
    setError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
      <header className="py-8 text-center">
        <h1 className="text-4xl font-extrabold text-purple-800">
          StoryForge
        </h1>
        <p className="text-gray-500 mt-1">Magical audio stories for kids</p>
      </header>

      <main className="px-4 pb-16">
        {error && (
          <div className="max-w-lg mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center">
            {error}
          </div>
        )}

        {step === "profile" && (
          <KidProfileForm
            onSubmit={(profile) => {
              setKidProfile(profile);
              setStep("story-type");
            }}
          />
        )}

        {step === "story-type" && (
          <StoryTypeSelector
            onSelect={(type) =>
              setStep(type === "custom" ? "custom-form" : "historical-pick")
            }
          />
        )}

        {step === "custom-form" && (
          <CustomStoryForm
            onSubmit={handleCustomStory}
            onBack={() => setStep("story-type")}
          />
        )}

        {step === "historical-pick" && (
          <HistoricalEventPicker
            onSelect={handleHistoricalStory}
            onBack={() => setStep("story-type")}
          />
        )}

        {step === "generating" && (
          <GeneratingScreen currentStage={currentStage} />
        )}

        {step === "listen" && (
          <AudioPlayer
            title={storyTitle}
            audioUrl={audioUrl}
            durationSeconds={storyDuration}
            onCreateAnother={handleCreateAnother}
          />
        )}
      </main>
    </div>
  );
}
```

**Step 2: Clean up default Vite files**

Delete `frontend/src/App.css` and remove its import. Remove default Vite content from `App.tsx` (already replaced above).

**Step 3: Verify frontend compiles**

```bash
cd /path/to/audio-story-creator/frontend
npm run build
# Expected: Build succeeds with no errors
```

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: wire up wizard flow in App component with all steps"
```

---

### Task 17: End-to-End Manual Test

**Files:** None (manual verification)

**Step 1: Ensure ffmpeg is installed**

```bash
which ffmpeg || brew install ffmpeg
```

**Step 2: Set up backend .env**

```bash
cd /path/to/audio-story-creator/backend
cp .env.example .env
# Edit .env with real API keys for GROQ_API_KEY and ELEVENLABS_API_KEY
```

**Step 3: Start backend**

```bash
cd /path/to/audio-story-creator/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Step 4: Start frontend (separate terminal)**

```bash
cd /path/to/audio-story-creator/frontend
npm run dev
```

**Step 5: Test in browser**

1. Open http://localhost:5173
2. Fill in kid profile (name: "Arjun", age: 7)
3. Select "Custom Story"
4. Pick genre "Fantasy", describe "A magical paintbrush that brings drawings to life"
5. Wait for generation (~30-90 seconds)
6. Verify audio plays and downloads

**Step 6: Test historical story**

1. Click "Create Another Story"
2. Select "Historical Adventure"
3. Pick "Shivaji Maharaj's Great Escape from Agra"
4. Wait for generation
5. Verify audio plays

**Step 7: Commit any fixes discovered during testing**

```bash
git add -A
git commit -m "fix: address issues found during end-to-end testing"
```

---

### Task 18: Run All Tests & Final Cleanup

**Step 1: Run all backend tests**

```bash
cd /path/to/audio-story-creator/backend
source venv/bin/activate
python -m pytest tests/ -v
# Expected: All tests PASS
```

**Step 2: Add .gitignore**

```
# .gitignore
__pycache__/
*.pyc
.env
backend/venv/
node_modules/
frontend/dist/
.DS_Store
```

**Step 3: Final commit**

```bash
cd /path/to/audio-story-creator
git add .gitignore
git commit -m "chore: add .gitignore"
```
