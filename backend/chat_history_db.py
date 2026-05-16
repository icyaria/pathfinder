"""
chat_history_db.py
Simple JSON-based chat history store linked to users by unique ID.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.user_db import get_user_by_unique_id

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chat_history.json")

REQUIRED_FIELDS = [
    "UserUniqueID",
    "HistoryUniqueID",
    "KeyData",
    "UserMessages",
    "QuickSelectPromptsChosen",
    "CreatedAt",
]


def _ensure_db_exists() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_entries() -> List[Dict[str, Any]]:
    _ensure_db_exists()
    with open(DB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    raise ValueError("chat_history.json must contain a JSON array")


def _save_entries(entries: List[Dict[str, Any]]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _generate_history_unique_id(existing_ids: set) -> str:
    while True:
        candidate = f"HIS-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in existing_ids:
            return candidate


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_history_entry(
    user_uniqie_id: str,
    key_data: Any,
    user_messages: Optional[List[str]] = None,
    quick_select_prompts_chosen: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Creates and persists a single chat history record.

    user_uniqie_id: user identifier from users.json field UserUniqieID
        key_data: all data entered/selected in chatbot fields (dict/list/string/etc.)
        user_messages: ordered list of free-text user messages
        quick_select_prompts_chosen: ordered list of selected quick prompts/buttons

    Stored fields:
            UserUniqueID, HistoryUniqueID, KeyData,
            UserMessages, QuickSelectPromptsChosen, CreatedAt
    """
    user_uniqie_id = (user_uniqie_id or "").strip()
    if not user_uniqie_id:
        raise ValueError("user_uniqie_id cannot be empty")

    # Validate ownership against the users DB (which stores UserUniqieID).
    user = get_user_by_unique_id(user_uniqie_id)
    if not user:
        raise ValueError("Unknown user_uniqie_id: user does not exist")

    entries = _load_entries()
    existing_ids = {e.get("HistoryUniqueID") for e in entries}

    normalized_user_messages = [str(m).strip() for m in (user_messages or []) if str(m).strip()]
    normalized_quick_prompts = [
        str(p).strip() for p in (quick_select_prompts_chosen or []) if str(p).strip()
    ]

    entry = {
        "UserUniqueID": user_uniqie_id,
        "HistoryUniqueID": _generate_history_unique_id(existing_ids),
        "KeyData": key_data,
        "UserMessages": normalized_user_messages,
        "QuickSelectPromptsChosen": normalized_quick_prompts,
        "CreatedAt": _utc_now_iso(),
    }

    entries.append(entry)
    _save_entries(entries)
    return entry


def get_history_by_unique_id(history_unique_id: str) -> Optional[Dict[str, Any]]:
    history_unique_id = (history_unique_id or "").strip()
    if not history_unique_id:
        return None

    entries = _load_entries()
    for entry in entries:
        if entry.get("HistoryUniqueID") == history_unique_id:
            return entry
    return None


def list_history_for_user(user_uniqie_id: str) -> List[Dict[str, Any]]:
    user_uniqie_id = (user_uniqie_id or "").strip()
    if not user_uniqie_id:
        return []

    entries = _load_entries()
    return [e for e in entries if e.get("UserUniqueID") == user_uniqie_id]


def list_history_entries() -> List[Dict[str, Any]]:
    return _load_entries()


def append_user_message(history_unique_id: str, message: str) -> Dict[str, Any]:
    """Append a user free-text message to an existing history record."""
    history_unique_id = (history_unique_id or "").strip()
    message = (message or "").strip()
    if not history_unique_id:
        raise ValueError("history_unique_id cannot be empty")
    if not message:
        raise ValueError("message cannot be empty")

    entries = _load_entries()
    for entry in entries:
        if entry.get("HistoryUniqueID") == history_unique_id:
            entry.setdefault("UserMessages", []).append(message)
            _save_entries(entries)
            return entry

    raise ValueError("Unknown history_unique_id")


def append_quick_select_prompt(history_unique_id: str, prompt: str) -> Dict[str, Any]:
    """Append a quick-select prompt choice to an existing history record."""
    history_unique_id = (history_unique_id or "").strip()
    prompt = (prompt or "").strip()
    if not history_unique_id:
        raise ValueError("history_unique_id cannot be empty")
    if not prompt:
        raise ValueError("prompt cannot be empty")

    entries = _load_entries()
    for entry in entries:
        if entry.get("HistoryUniqueID") == history_unique_id:
            entry.setdefault("QuickSelectPromptsChosen", []).append(prompt)
            _save_entries(entries)
            return entry

    raise ValueError("Unknown history_unique_id")


def validate_history_record(entry: Dict[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in entry:
            return False

    if not isinstance(entry.get("UserUniqueID"), str):
        return False
    if not isinstance(entry.get("HistoryUniqueID"), str):
        return False
    if not isinstance(entry.get("UserMessages"), list):
        return False
    if not isinstance(entry.get("QuickSelectPromptsChosen"), list):
        return False
    if not isinstance(entry.get("CreatedAt"), str):
        return False

    return True
