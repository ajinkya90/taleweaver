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
