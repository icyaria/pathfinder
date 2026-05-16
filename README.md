# 🧭 Pathfinder — AI Trail Companion

> *Find your trail. Leave no trace.*  
> AI-powered sustainable outdoor discovery for Greece — Deloitte Makeathon 2026.

---

## What it does

Pathfinder is a conversational AI that:
1. **Profiles** the traveller through natural language
2. **Matches** them to real Greek trails (difficulty, terrain, duration)
3. **Checks** live weather and flags safety concerns
4. **Builds route + terrain context** using OpenRouteService and NASA SRTM elevation
5. **Scores** each trail for sustainability (crowd avoidance, biodiversity, local economy)
6. **Generates** a personalised day-by-day itinerary

This implementation is aligned to the Makeathon challenge:
- Conversational AI intake for traveller profiling
- Open data trail intelligence and route generation
- Real-time weather and safety checks
- Sustainability-first ranking to avoid overtouristed hotspots

---

## Quickstart (5 steps)

### 1. Clone & enter the project
```bash
cd pathfinder
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
```bash
cp .env.example .env
# Edit .env and add your keys:
#   ANTHROPIC_API_KEY   — get at console.anthropic.com
#   OPENWEATHER_API_KEY — get at openweathermap.org/api (free tier)
#   OPENROUTESERVICE_API_KEY — get at openrouteservice.org/dev
```

### 5. Fetch real trail data from OpenStreetMap
```bash
python scripts/fetch_trails.py
# Takes ~1-2 min. Saves 20-50 real Greek trails to data/trails.json
```

### 6. Run the app
```bash
streamlit run frontend/app.py
```

Or test the pipeline directly in the terminal:
```bash
python pipeline.py
```

---

## Project structure

```
pathfinder/
│
├── pipeline.py              # Main entry point — chains all modules
│
├── backend/
│   ├── user_db.py           # JSON user accounts (UserUniqieID generation)
│   ├── chat_history_db.py   # JSON chat history linked by user ID
│   ├── profiler.py          # LLM extracts structured profile from user text
│   ├── trail_engine.py      # Filters and ranks trails against profile
│   ├── routing.py           # OpenRouteService route estimate/fallback
│   ├── elevation.py         # NASA SRTM elevation profile
│   ├── weather.py           # OpenWeatherMap real-time conditions
│   ├── biodiversity.py      # iNaturalist species observations
│   └── sustainability.py    # Composite 0-100 sustainability score
│
├── frontend/
│   └── app.py               # Streamlit UI with map
│
├── scripts/
│   └── fetch_trails.py      # One-time: fetches trails from OSM → data/trails.json
│
├── data/
│   ├── trails.json          # Trail database from OSM
│   ├── users.json           # User account records
│   └── chat_history.json    # Per-user chatbot history snapshots
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## API keys needed

| Key | Where to get | Free tier |
|-----|-------------|-----------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Yes (limited) |
| `OPENWEATHER_API_KEY` | openweathermap.org/api | Yes (1000 calls/day) |
| `OPENROUTESERVICE_API_KEY` | openrouteservice.org/dev | Yes |

iNaturalist, OpenStreetMap (Overpass), and NASA SRTM (via OpenTopodata) require **no API key**.

---

## Data sources

| Source | What it provides |
|--------|-----------------|
| OpenStreetMap / Overpass API | Trail names, coordinates, distance |
| OpenRouteService | Hiking route distance and time estimates |
| OpenWeatherMap | Real-time weather per trail location |
| iNaturalist API | Biodiversity observations near each trail |
| NASA SRTM (OpenTopodata) | Elevation baseline and trail gain |
| Claude (Anthropic) | Profile extraction, trail enrichment, itinerary generation |

---

## Expected deliverables checklist

- Codebase: this repository (or ZIP export) with setup README
- Presentation/report: use [docs/presentation_outline.md](docs/presentation_outline.md) as a 10-slide template
- Demo: Streamlit app with real Greek trail data from OSM
- Optional comparison: sustainability score per trail is shown side-by-side in the UI

---

## Database logic

Pathfinder uses two lightweight JSON databases in the [data](data) folder.

### 1) User database

File: [data/users.json](data/users.json)

Managed by: [backend/user_db.py](backend/user_db.py)

Each user record stores:
- Name
- Surname
- Age
- Gender
- Location
- UserUniqieID
- Description

Core logic:
- On account creation, the backend generates a unique UserUniqieID in format USR-XXXXXXXXXXXX.
- UserUniqieID is the stable key used everywhere else in the app.
- Validation enforces Age range and Description length.

### 2) Chat history database

File: [data/chat_history.json](data/chat_history.json)

Managed by: [backend/chat_history_db.py](backend/chat_history_db.py)

Each history record stores:
- UserUniqueID
- HistoryUniqueID
- KeyData
- UserMessages
- QuickSelectPromptsChosen
- CreatedAt

Core logic:
- Every chat/session snapshot gets a HistoryUniqueID in format HIS-XXXXXXXXXXXX.
- UserUniqueID links each history row back to one user account.
- KeyData stores the form/chatbot values needed to restore app state.
- UserMessages keeps free-text user turns.
- QuickSelectPromptsChosen keeps selected quick prompt buttons.
- CreatedAt supports log/audit ordering and replay.

---

## Frontend-to-backend integration

The frontend should follow this sequence when a user interacts with the chatbot:

1. Create or load user account
- Call create_user(...) once on signup.
- Persist UserUniqieID in session state after login/signup.

2. Start a history record for a new chat
- Call create_history_entry(user_uniqie_id, key_data, user_messages, quick_select_prompts_chosen).
- Keep returned HistoryUniqueID in session state for this chat.

3. Update during conversation
- Append each typed user message with append_user_message(...).
- Append each quick-prompt click with append_quick_select_prompt(...).
- Refresh KeyData snapshots when form selections change.

4. Restore previous state
- Use list_history_for_user(user_uniqie_id) to show chat history.
- Load a selected record by HistoryUniqueID and hydrate UI fields from KeyData.
- Rebuild conversation panel from UserMessages and QuickSelectPromptsChosen.

Minimal usage example:

```python
from backend.user_db import create_user
from backend.chat_history_db import create_history_entry

user = create_user(
	name="Eleni",
	surname="Papadaki",
	age=25,
	gender="Female",
	location="Athens",
	description="Student"
)

history = create_history_entry(
	user_uniqie_id=user["UserUniqieID"],
	key_data={"duration_days": 2, "terrain": "forest"},
	user_messages=["I want a quiet 2-day hike"],
	quick_select_prompts_chosen=["Moderate forest hike, interested in history and local villages"],
)
```

---

## Team roles

| Person | File(s) | Focus |
|--------|---------|-------|
| Person 1 | `frontend/app.py` | Streamlit UI + Folium map |
| Person 2 | `backend/profiler.py`, `backend/itinerary.py` | LLM prompts |
| Person 3 | `backend/trail_engine.py`, `scripts/fetch_trails.py` | Trail data |
| Person 4 | `backend/weather.py`, `backend/sustainability.py`, `backend/biodiversity.py` | APIs + scoring |
