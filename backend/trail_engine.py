"""
trail_engine.py
Loads trails from data/trails.json and filters/ranks them against a profile.
"""

import json
import os

# Absolute path so this works regardless of where you call it from
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")

DIFFICULTY_ORDER = {"easy": 1, "moderate": 2, "hard": 3}
FITNESS_TO_DIFFICULTY = {"low": "easy", "medium": "moderate", "high": "hard"}


def load_trails() -> list:
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(
        "data/trails.json not found. Run: python scripts/fetch_trails.py"
    )


def match_trails(profile: dict, trails: list = None, top_n: int = 5) -> list:
    """
    Score every trail against the profile and return the top_n matches.

    Scoring (max ~10 pts):
        +3  terrain matches
        +2  difficulty matches (or one step easier)
        -2  difficulty exceeds user fitness (safety penalty)
        +2  duration fits within the trip budget
        +1  per interest keyword found in highlights
    """
    if trails is None:
        trails = load_trails()

    max_daily_hours = {"high": 8, "medium": 6, "low": 4}[profile["fitness_level"]]
    max_total_hours = profile["duration_days"] * max_daily_hours

    scored = []
    for trail in trails:
        score = 0

        # Terrain
        if trail["terrain"] == profile["terrain"]:
            score += 3
        elif profile["terrain"] == "mixed":
            score += 1

        # Difficulty
        trail_d = DIFFICULTY_ORDER.get(trail["difficulty"], 2)
        target_d = DIFFICULTY_ORDER.get(profile["difficulty"], 2)
        if trail_d == target_d:
            score += 2
        elif trail_d == target_d - 1:
            score += 1        # one step easier — fine
        elif trail_d > target_d:
            score -= 2        # harder than fitness allows — penalise

        # Duration fits
        if trail["duration_hours"] <= max_total_hours:
            score += 2

        # Interest alignment
        highlights_text = " ".join(trail.get("highlights", [])).lower()
        for interest in profile.get("interests", []):
            if interest.lower() in highlights_text:
                score += 1

        if score > 0:
            scored.append({**trail, "_match_score": score})

    # Primary sort: match score DESC; secondary: crowd level ASC (quieter = better)
    scored.sort(key=lambda t: (-t["_match_score"], t.get("crowd_level", 3)))
    return scored[:top_n]
