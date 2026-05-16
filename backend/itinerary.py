"""
itinerary.py
Takes fully enriched trail objects and generates a day-by-day plan via LLM.
"""

import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"


def generate_itinerary(profile: dict, enriched_trails: list) -> str:
    """
    Sends profile + enriched trail data to Claude and gets back a full
    day-by-day itinerary as a formatted string.
    """
    trail_summaries = []
    for i, t in enumerate(enriched_trails, 1):
        w   = t.get("_weather", {})
        s   = t.get("_sustainability", {})
        bio = t.get("_biodiversity", {})

        weather_str = (
            f"{w.get('temp_c')}°C, {w.get('conditions')}"
            if w.get("temp_c") is not None
            else "weather data unavailable"
        )
        flags_str   = "; ".join(w.get("safety_flags", [])) or "no safety concerns"
        species_str = ", ".join(bio.get("notable_species", [])) or "various local species"

        trail_summaries.append(
            f"Trail {i}: {t['name']} ({t['region']})\n"
            f"  Terrain: {t['terrain']} | Difficulty: {t['difficulty']} | "
            f"Duration: {t['duration_hours']}h\n"
            f"  Highlights: {', '.join(t.get('highlights', []))}\n"
            f"  Weather: {weather_str} | Safety: {flags_str}\n"
            f"  Biodiversity: {bio.get('total_observations', 0)} research observations "
            f"({species_str})\n"
            f"  Sustainability: {s.get('score', '?')}/100 — {s.get('label', '')}"
        )

    trails_block = "\n\n".join(trail_summaries)

    prompt = f"""You are Pathfinder, an AI trail companion for sustainable tourism in Greece.
Your mission: inspire travellers to explore hidden, ecologically valuable trails
and redirect tourism away from Greece's overtouristed hotspots.

TRAVELLER PROFILE
-----------------
Trip length      : {profile['duration_days']} day(s)
Difficulty       : {profile['difficulty']}
Preferred terrain: {profile['terrain']}
Interests        : {', '.join(profile['interests']) or 'general hiking'}
Group size       : {profile['group_size']}
Fitness level    : {profile['fitness_level']}

MATCHED TRAILS
--------------
{trails_block}

TASK
----
Write a day-by-day hiking itinerary. Structure:

1. A 2-sentence intro addressing this traveller's specific interests.
2. For each day (up to {profile['duration_days']} days):
   - Trail name + region (bold)
   - Why it suits this traveller personally
   - What to expect: terrain feel, key highlights, atmosphere
   - Safety note (only if flags exist — skip if clear)
   - Wildlife/biodiversity note if notable species present
   - Practical tips: start time, what to pack, nearest village for food/sleep
   - Sustainability score + one sentence on why this trail benefits local communities
3. A 3-sentence sustainability summary: how this itinerary avoids hotspots and
   spreads tourism revenue to underserved regions.

Tone: warm, knowledgeable, like a Greek local guide who loves these places.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
