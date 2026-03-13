import pytest
from app.graph.nodes.script_splitter import script_splitter, _assign_voice_type


def test_assign_voice_type_narrator():
    assert _assign_voice_type("narrator", "Arjun") == "narrator"


def test_assign_voice_type_child():
    assert _assign_voice_type("Arjun", "Arjun") == "child"
    assert _assign_voice_type("arjun", "Arjun") == "child"


def test_assign_voice_type_female():
    for name in ["Queen", "princess", "Mother", "fairy", "witch"]:
        assert _assign_voice_type(name, "Arjun") == "female"


def test_assign_voice_type_male_default():
    assert _assign_voice_type("King", "Arjun") == "male"
    assert _assign_voice_type("Wizard", "Arjun") == "male"


@pytest.mark.asyncio
async def test_splitter_empty_text():
    """Empty text should produce one narrator segment with the full text."""
    state = {"story_text": "", "kid_name": "Arjun"}
    result = await script_splitter(state)
    assert len(result["segments"]) == 1
    assert result["segments"][0]["voice_type"] == "narrator"


@pytest.mark.asyncio
async def test_splitter_trailing_narration():
    """Text after the last dialogue should be captured as narrator."""
    text = 'King: "Hello there!"\nThe sun set behind the hills.'
    state = {"story_text": text, "kid_name": "Arjun"}
    result = await script_splitter(state)
    assert len(result["segments"]) == 2
    assert result["segments"][0]["voice_type"] == "male"
    assert result["segments"][1]["voice_type"] == "narrator"
    assert "sun set" in result["segments"][1]["text"]


@pytest.mark.asyncio
async def test_splitter_multiple_characters():
    """Multiple characters get correctly assigned voices."""
    text = '''Once upon a time.
Queen: "Welcome to the kingdom!"
Arjun: "Thank you, your majesty!"
Wizard: "Beware of the dragon!"'''
    state = {"story_text": text, "kid_name": "Arjun"}
    result = await script_splitter(state)
    voice_types = [s["voice_type"] for s in result["segments"]]
    assert "narrator" in voice_types
    assert "female" in voice_types
    assert "child" in voice_types
    assert "male" in voice_types
