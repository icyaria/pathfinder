"""
api/main.py — Pathfinder FastAPI backend
Run with: uvicorn api.main:app --reload --port 8001
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json

from pipeline import run_pathfinder
from backend.trail_details import get_accurate_stats, get_nearby_pois
from backend.trail_chat import chat_about_trail
from backend.saved_trails import save_trail, get_saved_trails, remove_saved_trail

try:
    from backend.user_db import create_user, list_users, authenticate_user
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")

app = FastAPI(title="Pathfinder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class Profile(BaseModel):
    duration_days: int = 2
    difficulty: str = "moderate"
    terrain: str = "mixed"
    interests: List[str] = []
    group_size: int = 1
    fitness_level: str = "medium"
    start_date: str = ""


class TrailPayload(BaseModel):
    trail: dict


class POIPayload(BaseModel):
    lat: float
    lon: float


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPayload(BaseModel):
    trail: dict
    stats: dict
    pois: List[Dict]
    history: List[ChatMessage]
    message: str


class SignupPayload(BaseModel):
    name: str
    surname: str
    age: int
    gender: str
    location: str
    description: str = ""
    password: str


class SigninPayload(BaseModel):
    user_id: str
    password: str


class SaveTrailPayload(BaseModel):
    user_id: str
    trail: dict
    profile: dict


class RemoveTrailPayload(BaseModel):
    user_id: str
    trail_name: str


# ── Trails ────────────────────────────────────────────────────────────────────

@app.get("/api/trails/featured")
def get_featured_trails(n: int = 3):
    if not os.path.exists(DATA_PATH):
        return {"trails": []}
    with open(DATA_PATH, encoding="utf-8") as f:
        all_trails = json.load(f)
    out, seen = [], set()
    for t in all_trails:
        ter = t.get("terrain", "mixed")
        if ter not in seen:
            out.append(t)
            seen.add(ter)
        if len(out) >= n:
            break
    for t in all_trails:
        if len(out) >= n:
            break
        if t not in out:
            out.append(t)
    # Strip heavy internal fields for homepage
    slim = []
    for t in out[:n]:
        slim.append({k: v for k, v in t.items() if not k.startswith("_")})
    return {"trails": slim}


@app.post("/api/search")
def search_trails(profile: Profile):
    try:
        result = run_pathfinder(profile=profile.model_dump(), verbose=False)
        # Strip very heavy fields to keep response lean
        trails = []
        for t in result.get("enriched_trails", []):
            slim = {k: v for k, v in t.items() if k != "_weather_calendar" or True}
            trails.append(slim)
        return {
            "trails": trails,
            "itinerary": result.get("itinerary", ""),
            "profile": result.get("profile", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trail/stats")
def trail_stats(payload: TrailPayload):
    try:
        stats = get_accurate_stats(payload.trail)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trail/pois")
def trail_pois(payload: POIPayload):
    try:
        pois = get_nearby_pois(payload.lat, payload.lon)
        return {"pois": pois}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def trail_chat(payload: ChatPayload):
    try:
        reply = chat_about_trail(
            trail=payload.trail,
            stats=payload.stats,
            pois=payload.pois,
            history=[{"role": m.role, "content": m.content} for m in payload.history],
            user_message=payload.message,
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Saved trails ──────────────────────────────────────────────────────────────

@app.post("/api/trails/save")
def api_save_trail(payload: SaveTrailPayload):
    entry = save_trail(payload.user_id, payload.trail, payload.profile)
    return entry


@app.get("/api/trails/saved")
def api_get_saved(user_id: str):
    return {"trails": get_saved_trails(user_id)}


@app.delete("/api/trails/saved")
def api_remove_trail(payload: RemoveTrailPayload):
    ok = remove_saved_trail(payload.user_id, payload.trail_name)
    return {"success": ok}


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/api/auth/users")
def api_list_users():
    if not HAS_AUTH:
        return {"users": []}
    users = list_users()
    return {"users": [{"id": u["UserUniqieID"], "name": u["Name"], "surname": u["Surname"]} for u in users]}


@app.post("/api/auth/signup")
def api_signup(payload: SignupPayload):
    if not HAS_AUTH:
        raise HTTPException(status_code=503, detail="Auth not available")
    try:
        user = create_user(
            name=payload.name, surname=payload.surname, age=payload.age,
            gender=payload.gender, location=payload.location,
            description=payload.description, password=payload.password,
        )
        return {"user_id": user["UserUniqieID"], "name": user["Name"], "surname": user["Surname"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/signin")
def api_signin(payload: SigninPayload):
    if not HAS_AUTH:
        raise HTTPException(status_code=503, detail="Auth not available")
    user = authenticate_user(payload.user_id, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": payload.user_id, "name": user["Name"], "surname": user["Surname"]}


@app.get("/api/health")
def health():
    return {"status": "ok", "trails_db": os.path.exists(DATA_PATH)}
