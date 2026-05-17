"""
live_interest.py
Tracks real-time user interest in trails for collaborative rerouting.

When multiple users signal interest in the same trail, its effective crowd
level rises, pushing the sustainability score down and steering subsequent
users toward quieter alternatives.

Interest counts decay after DECAY_HOURS so old data doesn't accumulate.
"""

import json
import os
from datetime import datetime, timedelta

INTEREST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "live_interest.json")
DECAY_HOURS = 48


def _load() -> dict:
    if not os.path.exists(INTEREST_PATH):
        return {}
    try:
        with open(INTEREST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(INTEREST_PATH), exist_ok=True)
    with open(INTEREST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _purge_expired(data: dict) -> dict:
    cutoff = datetime.utcnow() - timedelta(hours=DECAY_HOURS)
    return {
        name: entry for name, entry in data.items()
        if datetime.fromisoformat(entry["last_updated"]) > cutoff
    }


def register_interest(trail_name: str) -> int:
    """Increment interest count for a trail. Returns the new count."""
    data = _purge_expired(_load())
    entry = data.get(trail_name, {"count": 0, "last_updated": datetime.utcnow().isoformat()})
    entry["count"] += 1
    entry["last_updated"] = datetime.utcnow().isoformat()
    data[trail_name] = entry
    _save(data)
    return entry["count"]


def get_interest_count(trail_name: str) -> int:
    """Return the current live interest count for a trail (0 if none)."""
    data = _purge_expired(_load())
    return data.get(trail_name, {}).get("count", 0)


def get_all_interests() -> dict:
    """Return {trail_name: count} for all non-expired entries."""
    data = _purge_expired(_load())
    return {name: entry["count"] for name, entry in data.items()}


def crowd_adjustment(trail_name: str) -> int:
    """
    Extra crowd_level points to add based on live interest.
    Every 3 users headed to the same trail bumps the crowd level by 1 (max +3).
    """
    count = get_interest_count(trail_name)
    return min(3, count // 3)
