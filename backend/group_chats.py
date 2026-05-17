"""
group_chats.py
Trail group chat persistence — one group per trail, users auto-join when they save a trail.
Data lives in data/group_chats.json.
"""

import json
import os
import uuid
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "group_chats.json")
MAX_MESSAGES = 200


def _load() -> dict:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _group_key(trail_name: str) -> str:
    return trail_name.strip()


def get_or_create_group(trail_name: str) -> dict:
    data = _load()
    key = _group_key(trail_name)
    if key not in data:
        data[key] = {
            "trail_name": trail_name,
            "group_name": f"{trail_name} Hikers",
            "members": [],
            "messages": [],
            "created_at": _now(),
        }
        _save(data)
    return data[key]


def join_group(trail_name: str, user_id: str, user_name: str) -> dict:
    data = _load()
    key = _group_key(trail_name)
    get_or_create_group(trail_name)
    data = _load()
    group = data[key]

    already = any(m["user_id"] == user_id for m in group["members"])
    if not already:
        group["members"].append({
            "user_id": user_id,
            "user_name": user_name,
            "joined_at": _now(),
        })
        _save(data)
    return data[key]


def leave_group(trail_name: str, user_id: str) -> bool:
    data = _load()
    key = _group_key(trail_name)
    if key not in data:
        return False
    group = data[key]
    before = len(group["members"])
    group["members"] = [m for m in group["members"] if m["user_id"] != user_id]
    if len(group["members"]) == before:
        return False
    _save(data)
    return True


def send_message(trail_name: str, user_id: str, user_name: str, text: str) -> dict:
    data = _load()
    key = _group_key(trail_name)
    if key not in data:
        get_or_create_group(trail_name)
        data = _load()

    msg = {
        "id": f"MSG-{uuid.uuid4().hex[:10].upper()}",
        "user_id": user_id,
        "user_name": user_name,
        "text": text.strip(),
        "sent_at": _now(),
    }
    data[key]["messages"].append(msg)
    # Keep only the most recent MAX_MESSAGES
    if len(data[key]["messages"]) > MAX_MESSAGES:
        data[key]["messages"] = data[key]["messages"][-MAX_MESSAGES:]
    _save(data)
    return msg


def get_messages(trail_name: str, limit: int = 50) -> list:
    data = _load()
    key = _group_key(trail_name)
    if key not in data:
        return []
    return data[key]["messages"][-limit:]


def get_group(trail_name: str) -> dict | None:
    data = _load()
    return data.get(_group_key(trail_name))


def get_user_groups(user_id: str) -> list:
    """Return all groups the user is a member of, newest first."""
    data = _load()
    groups = []
    for key, group in data.items():
        if any(m["user_id"] == user_id for m in group["members"]):
            groups.append({
                "trail_name": group["trail_name"],
                "group_name": group["group_name"],
                "member_count": len(group["members"]),
                "last_message": group["messages"][-1] if group["messages"] else None,
                "created_at": group["created_at"],
            })
    groups.sort(key=lambda g: (g["last_message"] or {}).get("sent_at", g["created_at"]), reverse=True)
    return groups
