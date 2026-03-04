import logging
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.llm import get_llm
from app.graph.state import StoryState
from app.prompts.custom_story import build_custom_story_prompt
from app.prompts.historical_story import build_historical_story_prompt

logger = logging.getLogger(__name__)

LOGS_DIR = Path(__file__).parent.parent.parent / "logs" / "stories"


def _save_transcript(state: StoryState, title: str, story_text: str):
    """Save story transcript to file for evaluation."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{state['kid_name'].lower().replace(' ', '_')}.txt"
        filepath = LOGS_DIR / filename

        word_count = len(story_text.split())
        content = f"""=== STORY TRANSCRIPT ===
Title: {title}
Generated: {datetime.now().isoformat()}
Kid: {state['kid_name']}, age {state['kid_age']}
Story Type: {state['story_type']}
Genre: {state.get('genre', 'N/A')}
Mood: {state.get('mood', 'N/A')}
Length: {state.get('length', 'N/A')}
Word Count: {word_count}
========================

{story_text}
"""
        filepath.write_text(content)
        logger.info(f"Transcript saved to {filepath}")
    except Exception as e:
        logger.warning(f"Failed to save transcript: {e}")


async def story_writer(state: StoryState) -> dict:
    llm = get_llm()

    if state["story_type"] == "custom":
        prompt = build_custom_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            genre=state["genre"],
            description=state["description"],
            mood=state.get("mood"),
            length=state.get("length"),
        )
    else:
        prompt = build_historical_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            event_data=state["event_data"],
            mood=state.get("mood"),
            length=state.get("length"),
        )

    logger.info(f"Generating {state['story_type']} story for {state['kid_name']} (age {state['kid_age']}), mood={state.get('mood')}, length={state.get('length')}")

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
    else:
        logger.warning("LLM response missing TITLE:/STORY: markers, using raw text")

    word_count = len(story_text.split())
    logger.info(f"Story generated: title='{title}', word_count={word_count}")
    logger.info(f"--- FULL TRANSCRIPT ---\n{story_text}\n--- END TRANSCRIPT ---")

    _save_transcript(state, title, story_text)

    return {"story_text": story_text, "title": title}
