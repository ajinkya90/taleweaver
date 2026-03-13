from typing import Optional

from app.prompts.utils import word_count_guide


def _age_directives(age: int) -> str:
    if age <= 5:
        return """AGE GROUP 3-5 — PRESCHOOL LISTENER:
- Use simple words and short sentences. Vocabulary a 4-year-old would understand.
- Single protagonist, single problem, Rule of Three structure (try once, try twice, succeed on third).
- Include a repetitive refrain or catchphrase the listener can anticipate and "say along."
- Complete, happy resolution. No ambiguity. The problem is fully solved.
- Sensory language: describe sounds, textures, smells vividly.
- Keep the emotional stakes gentle and concrete (e.g., "the bunny can't find home").
- Adults can be present but the child/creature protagonist solves the problem."""
    elif age <= 8:
        return """AGE GROUP 6-8 — EARLY READER:
- Use moderate vocabulary appropriate for early readers. Introduce 2-3 interesting new words naturally.
- Make the protagonist 1-2 years older than the target child (aspirational).
- Two parallel problems: one external (the quest/adventure) and one internal (an emotion or character flaw).
- Include 2-3 try/fail cycles — the protagonist must struggle before succeeding.
- Include a friend or ally character — the "buddy" dynamic.
- Humor: physical comedy, silly situations, light wordplay.
- Moral is earned through the story, NEVER stated explicitly. No "and the lesson is..." endings.
- Stakes should feel real to a child: friendship, fairness, belonging, not being believed."""
    else:
        return """AGE GROUP 9-12 — INDEPENDENT LISTENER:
- Use rich, detailed language with complex sentence structures. Don't shy from challenging vocabulary.
- Include an ensemble of 2-3 characters with distinct personalities and voices.
- Main plot + a subplot that mirrors or contrasts the main theme.
- Protagonist makes real mistakes with real consequences. No perfect heroes.
- Moral complexity: not everything is clearly right or wrong. Trust the listener to draw conclusions.
- DO NOT moralize or spell out the lesson — this age group rejects being talked down to.
- Stakes can be significant: loyalty, identity, injustice, real danger (age-appropriate).
- A cliffhanger-style or open-reflection ending is acceptable."""


def _mood_directives(mood: Optional[str]) -> str:
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


def build_custom_story_prompt(
    name: str, age: int, details: str, genre: str, description: str,
    mood: Optional[str] = None, length: Optional[str] = None,
) -> str:
    age_guide = _age_directives(age)
    word_count = word_count_guide(age, length)
    mood_guide = _mood_directives(mood)

    return f"""You are a world-class children's audio storyteller. Your stories captivate, move, and stay with listeners.

STORY REQUEST:
- Protagonist: a child named {name}, age {age}
- Genre: {genre}
- Concept: {description}

CHILD'S DETAILS (weave naturally into the story if provided):
{details if details else "No additional details."}

---

BEFORE YOU WRITE, plan the story skeleton internally (DO NOT output your planning — go straight to the final TITLE/STORY output):

Story Spine to follow:
- Once upon a time... [World + character + what's normal]
- Every day... [The protagonist's routine / status quo]
- Until one day... [The inciting incident that disrupts everything]
- Because of that... [First consequence — things change]
- Because of that... [Second consequence — stakes rise]
- Because of that... [Third consequence — approaching the crisis]
- Until finally... [The climax — the protagonist faces the biggest challenge]
- And ever since then... [The new normal — what changed]

Consider: What does {name} want? What's stopping them? What happens if they fail?

WRITING RULES:

{age_guide}

{word_count}

{mood_guide}

AUDIO STORYTELLING RULES (critical — this will be read aloud):
- Hook in the FIRST PARAGRAPH. Start with action, a sound, or an unresolved question. NEVER open with backstory or description.
- Vary sentence length deliberately: short sentences for urgency and action, longer flowing sentences for calm, wonder, or reflection.
- Build sound into the prose: use onomatopoeia ("CRASH", "whispered", "crackled"), sound-first scene openings, and described silence as a dramatic beat.
- Show emotion through ACTION, not narration. Write "her hands went cold" not "she was afraid." Write "he kicked the dirt" not "he was frustrated."
- Include ONE recurring refrain or catchphrase that appears at least 3 times in the story.
- Include ONE moment where the narrator addresses the listener: "And what do you think happened next?" or "Can you guess what was inside?"
- Leave deliberate gaps in visual descriptions — let the listener's imagination fill in details.
- The protagonist must FAIL at least once before succeeding. Effort is more compelling than effortless success.
- Include an "all is lost" moment — the darkest point before the turn. Scale to age group.
- NO deus ex machina. The protagonist solves their own problem through their own action or growth.
- Coincidences can create problems but NEVER solve them.
- Give {name} at least one authentic flaw a child would recognize (impatience, jealousy, fear of embarrassment, wanting to quit).

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [A creative, evocative title]
STORY:
[Your story text. Use dialogue with character names formatted as: CharacterName: "dialogue text"]"""
