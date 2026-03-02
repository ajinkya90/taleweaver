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
