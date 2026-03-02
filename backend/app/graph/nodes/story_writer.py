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
