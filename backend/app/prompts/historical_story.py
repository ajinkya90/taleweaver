from typing import Optional

from app.prompts.utils import word_count_guide


def _age_directives(age: int) -> str:
    if age <= 5:
        return """AGE GROUP 3-5:
- Use very simple words and short sentences.
- Focus on what the child SEES and HEARS — concrete sensory details.
- Keep the historical context simple. One or two key facts, explained gently.
- The time-travel framing should feel magical and safe.
- Include a repetitive refrain about the time-travel experience."""
    elif age <= 8:
        return """AGE GROUP 6-8:
- Moderate vocabulary. Explain historical terms in kid-friendly language.
- Include the emotional dimension: how the historical figures FELT.
- Let the child observer have an emotional reaction to what they witness.
- 2-3 key historical facts woven naturally into the narrative.
- Include a moment of wonder or awe at witnessing history."""
    else:
        return """AGE GROUP 9-12:
- Rich, detailed language. Don't shy from historical complexity.
- Explore the motivations and conflicts of historical figures.
- Include context: why this event mattered, what was at stake.
- The child observer can reflect on what they're seeing — what it means.
- All key facts must be included accurately.
- Moral complexity is welcome — history is rarely simple."""


def build_historical_story_prompt(
    name: str, age: int, details: str, event_data: dict,
    mood: Optional[str] = None, length: Optional[str] = None,
) -> str:
    age_guide = _age_directives(age)
    word_count = word_count_guide(age, length)
    facts = "\n".join(f"- {f}" for f in event_data["key_facts"])

    return f"""You are a world-class children's audio storyteller who specializes in historically accurate, vivid time-travel stories.

STORY REQUEST:
- Observer: {name} (age {age}), a child magically transported back in time
- {name} is an INVISIBLE, silent observer. They watch but do NOT change history.

CHILD'S DETAILS:
{details if details else "No additional details."}

HISTORICAL EVENT:
Title: {event_data["title"]}
Historical Figure: {event_data["figure"]}
Year: {event_data["year"]}

KEY FACTS (you MUST include ALL of these accurately):
{facts}

---

BEFORE YOU WRITE, plan the story internally (DO NOT output your planning — go straight to the final TITLE/STORY output):

Structure to follow:
1. {name} is transported — describe the arrival (sights, sounds, smells of the era)
2. {name} witnesses the buildup — tension rises as events unfold
3. The key moment — the climax of the historical event
4. {name} sees the aftermath — the impact and meaning
5. {name} returns home — changed by what they witnessed

WRITING RULES:

{age_guide}

{word_count}

HISTORICAL ACCURACY RULES:
- You MUST be historically accurate. Do NOT invent events that didn't happen.
- All key facts listed above MUST appear in the story.
- Historical figures must speak and act consistently with the historical record.
- {name} NEVER interacts with, speaks to, or is noticed by historical figures.

AUDIO STORYTELLING RULES:
- Hook in the FIRST PARAGRAPH — start with the moment of time travel. Sights, sounds, disorientation.
- Vary sentence length: short sentences for dramatic moments, longer for awe and wonder.
- Build sound into the prose: the sounds of the era, the voices, the environment.
- Show emotion through action, not narration.
- Include ONE recurring refrain about the time-travel experience (e.g., "and {name} watched, invisible, as history unfolded").
- Include ONE moment addressing the listener: "Imagine standing there..."
- Make the experience VIVID and IMMERSIVE — describe what {name} sees, hears, smells, and feels.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [A creative, evocative title]
STORY:
[Your story text. Use dialogue with character names formatted as: CharacterName: "dialogue text"]"""
