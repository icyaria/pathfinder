# Pathfinder - Makeathon 2026 

> *Explore Greece's Hidden Trails*  
> AI-Powered Sustainable Outdoor Discovery for Greece.
> Built for the Deloitte Makeathon 2026 - Sustainable Tourism Challenge.

---

Click [here](https://canva.link/pathfinder-ghostbusters) to view our presentation!

<div>
  <img width="127" height="127" src="https://github.com/user-attachments/assets/d2852585-fd1e-43a7-8e4b-a3e131eafc62" />
  <img width="384" height="127" src="https://github.com/user-attachments/assets/43430d25-9cbd-4748-aedf-5d25ad5cef1d" />
</div>

## What it does

Pathfinder is a full-stack AI application that:
1. **Profiles** the traveller through a conversational chat interface
2. **Matches** them to real Greek trails from OpenStreetMap (difficulty, terrain, duration)
3. **Checks** live weather and flags safety concerns (OpenWeatherMap, 5-day forecast)
4. **Scores** each trail for sustainability using real OSM crowd data, remoteness, biodiversity (iNaturalist), local economy, and weather
5. **Generates** a personalised day-by-day itinerary (AWS Bedrock / Claude)
6. **Discovers** trails via a Tinder-style swipe interface with adaptive preference learning
7. **Surprises** users with mood-based trail matching via LLM
8. **Connects** hikers headed to the same trail through auto-joined group chats
9. **Shows** accurate trail stats (distance, ascent via Naismith's Rule, nearby POIs)

---

## Team

| Person | Files |
|--------|-------|
| Kyriaki Kalamari | Frontend - React pages, UI/UX |
| Despoina Kampiwti | Frontend - React pages, UI/UX |
| Konstantinos Katrakis | Backend - pipeline, APIs, sustainability |
| Maria Kapaki | Backend - pipeline, APIs, sustainability |

---

## Architecture

```
pathfinder/
│
├── api/
│   └── main.py              # FastAPI backend - all REST endpoints
│
├── backend/
│   ├── profiler.py          # LLM extracts structured profile from user text
│   ├── trail_engine.py      # Filters and ranks trails against profile
│   ├── weather.py           # OpenWeatherMap - current + 5-day forecast
│   ├── biodiversity.py      # iNaturalist species observations
│   ├── sustainability.py    # Composite 0–100 sustainability score
│   ├── crowd_economy.py     # Real OSM crowd + local economy data
│   ├── elevation.py         # NASA SRTM elevation profiles (OpenTopodata)
│   ├── routing.py           # OpenRouteService hiking route estimates
│   ├── trail_details.py     # Accurate OSM stats + nearby POIs
│   ├── trail_chat.py        # Multi-turn AI chat about a specific trail
│   ├── surprise.py          # Mood-based trail matching via LLM
│   ├── live_interest.py     # Real-time trail interest tracking
│   ├── saved_trails.py      # Per-user saved trail persistence
│   ├── group_chats.py       # Trail group chat persistence
│   ├── ratings.py           # 1–5 star trail ratings
│   ├── region_utils.py      # Classifies trails into Greek regions by coords
│   ├── user_db.py           # JSON user accounts
│   └── chat_history_db.py   # JSON chat history per user
│
├── react/                   # React + Vite frontend
│   └── src/
│       ├── pages/
│       │   ├── HomePage.jsx
│       │   ├── AuthPage.jsx
│       │   ├── DashboardPage.jsx   # Overview, My Trails, Discover, Community
│       │   ├── ExplorePage.jsx     # Conversational trail finder
│       │   ├── ResultsPage.jsx     # Sustainability scores + itinerary
│       │   ├── TrailDetailPage.jsx # Full trail detail + AI chat
│       │   ├── SurprisePage.jsx    # Mood-based trail discovery
│       │   └── AboutPage.jsx
│       └── components/
│           ├── Nav.jsx
│           ├── TrailMap.jsx        # Leaflet map (trails + POIs)
│           ├── TrailModal.jsx      # Trail detail modal with chat + ratings
│           └── RegionFilter.jsx    # Filter by Greek administrative region
│
├── pipeline.py              # Chains all backend modules end-to-end
├── scripts/
│   └── fetch_trails.py      # One-time: fetch real trails from OSM → data/trails.json
├── data/                    # JSON databases (generated, not committed)
├── start.sh                 # Starts both FastAPI + React dev servers
├── requirements.txt
└── .env.example
```

---

## Quickstart

### 1. Clone & set up Python environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up API keys
```bash
cp .env.example .env
# Fill in .env:
#   AWS_ACCESS_KEY_ID       - AWS credentials for Bedrock (Claude)
#   AWS_SECRET_ACCESS_KEY
#   AWS_REGION              - e.g. us-east-1
#   BEDROCK_MODEL_ID        - e.g. us.anthropic.claude-sonnet-4-5-20250929-v1:0
#   OPENWEATHER_API_KEY     - openweathermap.org/api (free tier)
#   OPENROUTESERVICE_API_KEY - openrouteservice.org/dev (free tier, optional)
```

### 3. Fetch real trail data from OpenStreetMap
```bash
python scripts/fetch_trails.py
# Takes ~1–2 min. Saves up to 200 real Greek trails to data/trails.json
```

### 4. Install frontend dependencies
```bash
cd react
npm install
cd ..
```

### 5. Start both servers
```bash
bash start.sh
# FastAPI → http://localhost:8001
# React   → http://localhost:5173
```

Or start them separately:
```bash
# Terminal 1
uvicorn api.main:app --reload --port 8001

# Terminal 2
cd react && npm run dev
```

---

## API Keys

| Key | Source |
|-----|-------------|
| `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | aws.amazon.com |
| `OPENWEATHER_API_KEY` | openweathermap.org |
| `OPENROUTESERVICE_API_KEY` | openrouteservice.org |

---

## Data Sources

| Source | What it provides |
|--------|-----------------|
| OpenStreetMap / Overpass API | Trail names, coordinates, distance, difficulty |
| OpenWeatherMap | Real-time weather + 5-day forecast per trail |
| iNaturalist API | Biodiversity observations near each trail |
| NASA SRTM (OpenTopodata) | Elevation profiles and ascent data |
| OpenRouteService | Hiking route distance and duration estimates |
| AWS Bedrock (Claude) | Profile extraction, trail enrichment, itinerary generation, surprise matching, trail chat |

---

## Features

### Conversational trail finder
Chat-based profiling across 7 steps (terrain, duration, date, difficulty, fitness, interests, group size). Saves chat history per user.

### Sustainability scoring (0–100)
- **Crowd avoidance** (25 pts) - live OSM tourism POI count within 3 km
- **Remoteness** (15 pts) - Haversine distance to nearest major Greek city
- **Biodiversity** (20 pts) - iNaturalist research-grade observations
- **Local economy** (20 pts) - OSM amenity count within 10 km
- **Weather** (20 pts) - current/forecast conditions weighted by user preferences

### Discover (swipe)
Tinder-style trail cards. Swipe right to save, left to skip. Each swipe updates a local preference vector (terrain, difficulty, region weights) used to improve Surprise Me recommendations.

### Surprise Me
Mood chips + free text -> LLM picks the single best trail match from the database with a personalised explanation.

### Group chats
Saving a trail auto-joins you to that trail's group chat. Real-time polling (5s interval). Leave at any time.

### Live interest tracking
Every trail save registers interest. High-interest trails get a crowd bump in the sustainability score, steering subsequent users to quieter alternatives.

### Trail detail modal
Accurate stats via Naismith's Rule, 5-day weather calendar, iNaturalist species, nearby POIs on Leaflet map, 1–5 star ratings, and a multi-turn AI chat with full trail context injected.

