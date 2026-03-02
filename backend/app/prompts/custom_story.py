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
