"""
saved_trails.py
Persist and retrieve planned trails per user (data/saved_trails.json).
"""

import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "saved_trails.json")


def _load() -> dict:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_trail(user_id: str, trail: dict, profile: dict) -> dict:
    """
    Save a planned trail for user_id. Returns the saved entry.
    Strips heavy internal fields (_weather_calendar, _biodiversity raw)
    to keep the file lean.
    """
    data   = _load()
    trails = data.get(user_id, [])

    # Avoid exact duplicate by trail name
    existing_names = {t["trail_name"] for t in trails}
    if trail.get("name") in existing_names:
        return next(t for t in trails if t["trail_name"] == trail["name"])

    slim_trail = {k: v for k, v in trail.items() if not k.startswith("_")}
    entry = {
        "trail_name":  trail.get("name"),
        "region":      trail.get("region"),
        "trail_data":  slim_trail,
        "profile":     {k: v for k, v in profile.items() if k != "start_date"},
        "planned_date": profile.get("start_date", ""),
        "saved_at":    datetime.utcnow().isoformat(),
    }
    trails.append(entry)
    data[user_id] = trails
    _save(data)
    return entry


def get_saved_trails(user_id: str) -> list:
    return _load().get(user_id, [])


def remove_saved_trail(user_id: str, trail_name: str) -> bool:
    data   = _load()
    trails = data.get(user_id, [])
    new    = [t for t in trails if t["trail_name"] != trail_name]
    if len(new) == len(trails):
        return False
    data[user_id] = new
    _save(data)
    return True
