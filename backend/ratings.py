import json, os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ratings.json")


def _load():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_rating(trail_name: str) -> dict:
    entries = _load().get(trail_name, [])
    if not entries:
        return {"avg": None, "count": 0, "ratings": []}
    avg = round(sum(e["rating"] for e in entries) / len(entries), 1)
    return {"avg": avg, "count": len(entries), "ratings": entries}


def submit_rating(user_id: str, trail_name: str, rating: int) -> dict:
    data = _load()
    entries = data.get(trail_name, [])
    for entry in entries:
        if entry["user_id"] == user_id:
            entry["rating"] = rating
            entry["updated_at"] = datetime.utcnow().isoformat()
            data[trail_name] = entries
            _save(data)
            return get_rating(trail_name)
    entries.append({
        "user_id": user_id,
        "rating": rating,
        "created_at": datetime.utcnow().isoformat(),
    })
    data[trail_name] = entries
    _save(data)
    return get_rating(trail_name)


def get_user_rating(user_id: str, trail_name: str) -> int | None:
    entries = _load().get(trail_name, [])
    for e in entries:
        if e["user_id"] == user_id:
            return e["rating"]
    return None
