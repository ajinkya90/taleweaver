from typing import Optional


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
