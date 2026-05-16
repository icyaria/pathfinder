"""
profiler.py
Converts the user's natural language message into a structured profile dict.
"""

import json
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"


def extract_profile(user_input: str) -> dict:
    """
    Send the user's message to the LLM and get back structured JSON.

    Returns dict with keys:
        duration_days, difficulty, terrain, interests, group_size, fitness_level
    """
    prompt = f"""Extract hiking preferences from the message below.
Return ONLY valid JSON — no explanation, no markdown fences.

Message: {user_input}

JSON schema (use these exact keys and allowed values):
{{
  "duration_days": <integer 1-7>,
  "difficulty": <"easy" | "moderate" | "hard">,
  "terrain": <"coastal" | "mountain" | "forest" | "mixed">,
  "interests": <list of strings e.g. ["views", "wildlife", "history", "photography"]>,
  "group_size": <integer, default 1>,
  "fitness_level": <"low" | "medium" | "high">
}}

If a field cannot be inferred, use these defaults:
  duration_days=2, difficulty="moderate", terrain="mixed",
  interests=[], group_size=1, fitness_level="medium"
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
