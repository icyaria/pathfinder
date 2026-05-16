"""
trail_chat.py
Multi-turn AI chat about a specific trail, powered by AWS Bedrock.
Injects full trail context (stats, weather, biodiversity, POIs) so the
model can answer questions without hallucinating unknown details.
"""

import os
import boto3
from dotenv import load_dotenv

load_dotenv(override=False)
MODEL = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def _build_system(trail: dict, stats: dict, pois: list) -> str:
    w   = trail.get("_weather", {})
    bio = trail.get("_biodiversity", {})
    s   = trail.get("_sustainability", {})

    weather_line = (
        f"{w.get('temp_c')}°C, {w.get('conditions')}, wind {w.get('wind_kmh')} km/h"
        if w.get("temp_c") is not None else "weather data unavailable"
    )
    flags_line   = "; ".join(w.get("safety_flags", [])) or "none"
    species_line = ", ".join(bio.get("notable_species", [])) or "none recorded nearby"

    poi_summary = ""
    if pois:
        by_cat = {}
        for p in pois:
            by_cat.setdefault(p["category"], []).append(p["name"] or p["category"])
        poi_summary = "\n".join(
            f"  {cat}: {', '.join(names[:5])}" for cat, names in by_cat.items()
        )
    else:
        poi_summary = "  No POI data available."

    return f"""You are Pathfinder, an expert AI trail guide for sustainable hiking in Greece.
You are answering questions specifically about ONE trail. Use the data below.
Never invent distances, times, names or facts not in the data.
If you don't know something, say so and suggest where to look.

TRAIL: {trail.get('name')} ({trail.get('region')})
Terrain : {trail.get('terrain')} | Sustainability: {s.get('score', '?')}/100
Highlights: {', '.join(trail.get('highlights', [])) or 'not available'}

ACCURATE STATS (source: {stats.get('source', '?')}):
  Distance  : {stats.get('distance_km', '?')} km
  Duration  : {stats.get('duration_h', '?')} h  (Naismith's Rule)
  Ascent    : {stats.get('ascent_m', '?')} m
  Difficulty: {stats.get('difficulty', '?')}
  SAC scale : {stats.get('sac_scale', 'not tagged')}

WEATHER (on planned hike date):
  Conditions: {weather_line}
  Safety flags: {flags_line}

BIODIVERSITY (iNaturalist within 5 km):
  {bio.get('total_observations', 0)} research-grade observations
  Notable species: {species_line}

NEARBY POINTS OF INTEREST:
{poi_summary}

Answer in a warm, knowledgeable tone — like a local guide who loves this trail.
Keep answers concise unless the user asks for detail.
Always remind hikers of Leave No Trace principles when relevant."""


def chat_about_trail(trail: dict, stats: dict, pois: list,
                     history: list, user_message: str) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}
    Returns the assistant's reply as a string.
    """
    system = _build_system(trail, stats, pois)

    messages = []
    for msg in history:
        messages.append({
            "role":    msg["role"],
            "content": [{"text": msg["content"]}],
        })
    messages.append({"role": "user", "content": [{"text": user_message}]})

    response = bedrock.converse(
        modelId=MODEL,
        system=[{"text": system}],
        messages=messages,
        inferenceConfig={"maxTokens": 800},
    )
    return response["output"]["message"]["content"][0]["text"]
