from typing import Optional


def mood_directives(mood: Optional[str]) -> str:
    """Return mood-specific writing directives for the LLM prompt."""
    moods = {
        "exciting": """MOOD — EXCITING:
- Fast pacing with short, punchy sentences during action scenes.
- Physical action: running, climbing, dodging, racing against time.
- Higher stakes and more urgent problems.
- Frequent scene changes to maintain momentum.""",
        "heartwarming": """MOOD — HEARTWARMING:
- Focus on relationships: friendship, family bonds, acts of kindness.
- Include quiet, tender moments between characters.
- Emotional connection is the core of the story.
- The resolution should feel earned through empathy and understanding.""",
        "funny": """MOOD — FUNNY:
- Absurdist logic: "what if" scenarios taken to ridiculous extremes.
- Physical comedy and silly situations for younger kids.
- Wordplay, puns, and ironic situations for older kids.
- Characters can be lovably ridiculous.""",
        "mysterious": """MOOD — MYSTERIOUS:
- Rich sensory descriptions: shadows, echoes, strange silences.
- Unanswered questions that pull the listener forward.
- Atmospheric tension — something feels slightly off.
- Delayed reveals: describe sounds before showing what caused them.""",
    }
    if mood and mood in moods:
        return moods[mood]
    return ""


def word_count_guide(age: int, length: Optional[str]) -> str:
    """Return word count and duration target based on age and requested length."""
    ranges = {
        "young": {"short": (300, 400, 3, 4), "medium": (500, 700, 5, 7), "long": (700, 900, 7, 9)},
        "mid": {"short": (500, 700, 5, 7), "medium": (900, 1200, 9, 12), "long": (1200, 1500, 12, 15)},
        "older": {"short": (700, 1000, 7, 10), "medium": (1200, 1800, 12, 18), "long": (1800, 2500, 18, 25)},
    }
    age_key = "young" if age <= 5 else "mid" if age <= 8 else "older"
    length_key = length if length in ("short", "medium", "long") else "medium"
    lo, hi, min_dur, max_dur = ranges[age_key][length_key]
    return f"The story should be {lo}-{hi} words ({min_dur}-{max_dur} minutes when read aloud)."
