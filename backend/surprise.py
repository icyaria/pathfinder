"""
surprise.py
Mood-based trail matching using Claude.

The LLM receives:
  - the user's free-text mood
  - their accumulated preference weights
  - a shortlist of trail candidates (pre-filtered by region if requested)

It returns the single best trail and a human explanation.
"""

import os, json
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


def surprise_trail(mood: str, trails: list, preferences: dict = None) -> dict:
    """
    Given a mood string and a list of candidate trails, ask the LLM to pick
    the single best match and explain why in 2–3 sentences.

    Returns {"trail": {...}, "reason": str} or raises on failure.
    """
    preferences = preferences or {}

    # Build a concise preference summary for the prompt
    def top(d, n=2):
        return sorted(d.items(), key=lambda x: -x[1])[:n] if d else []

    pref_summary = ""
    if preferences.get("swipeCount", 0) > 0:
        ter = top(preferences.get("terrain", {}))
        dif = top(preferences.get("difficulty", {}))
        reg = top(preferences.get("regions", {}))
        parts = []
        if ter: parts.append("likes " + "/".join(t for t, _ in ter if _ > 0) + " terrain")
        if dif: parts.append("prefers " + "/".join(d for d, _ in dif if _ > 0) + " difficulty")
        if reg: parts.append("enjoyed trails near " + ", ".join(r for r, _ in reg if _ > 0))
        pref_summary = " · ".join(parts)

    # Slim trail listing for the prompt (avoid token explosion)
    listing = []
    for i, t in enumerate(trails[:30], 1):
        listing.append(
            f"{i}. {t['name']} | {t.get('region','?')} | {t.get('terrain','?')} | "
            f"{t.get('difficulty','?')} | {t.get('duration_hours','?')}h | "
            f"highlights: {', '.join(t.get('highlights', [])[:2])}"
        )

    prompt = f"""You are a Greek hiking expert matching a traveller to the perfect surprise trail.

Traveller mood: "{mood}"
{f'Known preferences: {pref_summary}' if pref_summary else ''}

Available trails:
{chr(10).join(listing)}

Pick the ONE trail that best matches this mood. Consider terrain, vibe, difficulty, and highlights.
Return ONLY valid JSON — no markdown, no extra text:
{{
  "index": <1-based int>,
  "reason": "<2-3 warm sentences explaining why this trail matches the mood>"
}}"""

    resp = bedrock.converse(
        modelId=MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400},
    )
    raw = resp["output"]["message"]["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])

    parsed = json.loads(raw)
    idx    = int(parsed["index"]) - 1
    if not (0 <= idx < len(trails)):
        raise ValueError(f"LLM returned out-of-range index {idx+1}")

    return {"trail": trails[idx], "reason": parsed["reason"]}
