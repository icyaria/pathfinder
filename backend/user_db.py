"""
user_db.py
Simple JSON-based user database for Pathfinder.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")
MAX_DESCRIPTION_LENGTH = 256

REQUIRED_FIELDS = [
    "Name",
    "Surname",
    "Age",
    "Gender",
    "Location",
    "UserUniqieID",
    "Description",
]


def _ensure_db_exists() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_users() -> List[Dict]:
    _ensure_db_exists()
    with open(DB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    raise ValueError("users.json must contain a JSON array")


def _save_users(users: List[Dict]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _normalize_text(value: str, field_name: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def _generate_unique_id(existing_ids: set) -> str:
    while True:
        candidate = f"USR-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in existing_ids:
            return candidate


def create_user(
    name: str,
    surname: str,
    age: int,
    gender: str,
    location: str,
    description: str,
) -> Dict:
    """
    Create a user and persist it to data/users.json.

    Stored fields:
      Name, Surname, Age, Gender, Location, UserUniqieID, Description
    """
    name = _normalize_text(name, "Name")
    surname = _normalize_text(surname, "Surname")
    gender = _normalize_text(gender, "Gender")
    location = _normalize_text(location, "Location")
    description = (description or "").strip()

    if not isinstance(age, int):
        raise ValueError("Age must be an integer")
    if age < 0 or age > 120:
        raise ValueError("Age must be between 0 and 120")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError("Description must be at most 256 characters")

    users = _load_users()
    existing_ids = {u.get("UserUniqieID") for u in users}
    user_unique_id = _generate_unique_id(existing_ids)

    user = {
        "Name": name,
        "Surname": surname,
        "Age": age,
        "Gender": gender,
        "Location": location,
        "UserUniqieID": user_unique_id,
        "Description": description,
    }

    users.append(user)
    _save_users(users)
    return user


def get_user_by_unique_id(user_unique_id: str) -> Optional[Dict]:
    user_unique_id = (user_unique_id or "").strip()
    if not user_unique_id:
        return None

    users = _load_users()
    for user in users:
        if user.get("UserUniqieID") == user_unique_id:
            return user
    return None


def list_users() -> List[Dict]:
    return _load_users()


def validate_user_record(user: Dict) -> bool:
    if not isinstance(user, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in user:
            return False

    if not isinstance(user.get("Age"), int):
        return False

    description = user.get("Description", "")
    if not isinstance(description, str) or len(description) > MAX_DESCRIPTION_LENGTH:
        return False

    return True
