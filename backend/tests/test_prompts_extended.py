from app.prompts.custom_story import build_custom_story_prompt, _mood_directives
from app.prompts.historical_story import build_historical_story_prompt, _age_directives
from app.prompts.utils import word_count_guide


def test_historical_age_directives_mid():
    """Cover the 6-8 age group branch."""
    result = _age_directives(7)
    assert "6-8" in result
    assert "emotional" in result.lower()


def test_historical_age_directives_young():
    result = _age_directives(4)
    assert "3-5" in result
    assert "simple" in result.lower()


def test_historical_age_directives_older():
    result = _age_directives(10)
    assert "9-12" in result
    assert "complex" in result.lower()


def test_word_count_guide_young_short():
    result = word_count_guide(4, "short")
    assert "300-400" in result


def test_word_count_guide_mid_medium():
    result = word_count_guide(7, "medium")
    assert "900-1200" in result


def test_word_count_guide_older_long():
    result = word_count_guide(11, "long")
    assert "1800-2500" in result


def test_word_count_guide_invalid_length_defaults_to_medium():
    result = word_count_guide(7, "extra-long")
    assert "900-1200" in result


def test_word_count_guide_none_length_defaults_to_medium():
    result = word_count_guide(7, None)
    assert "900-1200" in result


def test_mood_directives_all_moods():
    for mood in ["exciting", "heartwarming", "funny", "mysterious"]:
        result = _mood_directives(mood)
        assert len(result) > 0
        assert mood.upper() in result.upper()


def test_mood_directives_none():
    result = _mood_directives(None)
    assert result == ""


def test_mood_directives_invalid():
    result = _mood_directives("scary")
    assert result == ""


def test_historical_prompt_mid_age():
    """Cover mid-age group for historical prompts."""
    event_data = {
        "title": "Moon Landing",
        "figure": "Neil Armstrong",
        "year": 1969,
        "key_facts": ["First human on the Moon", "Apollo 11 mission"],
    }
    prompt = build_historical_story_prompt(
        name="Arjun", age=7, details="Loves space",
        event_data=event_data, mood="exciting", length="medium",
    )
    assert "Arjun" in prompt
    assert "Moon Landing" in prompt
    assert "First human on the Moon" in prompt
    assert "6-8" in prompt


def test_custom_prompt_with_no_details():
    prompt = build_custom_story_prompt(
        name="Arjun", age=7, details="",
        genre="fantasy", description="Magic adventure",
    )
    assert "No additional details" in prompt


def test_custom_prompt_heartwarming_mood():
    prompt = build_custom_story_prompt(
        name="Ava", age=5, details="",
        genre="bedtime", description="Sleepy story",
        mood="heartwarming", length="short",
    )
    assert "HEARTWARMING" in prompt
    assert "300-400" in prompt
