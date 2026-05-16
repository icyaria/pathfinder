"""
frontend/app.py — Pathfinder Streamlit UI

Run with:
  streamlit run frontend/app.py
"""

import sys
import os
import datetime
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import folium
from streamlit_folium import st_folium
from pipeline import run_pathfinder

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")
if not os.path.exists(DATA_PATH):
    with st.spinner("First launch: building trail database from OpenStreetMap… (this takes ~1 min)"):
        from scripts.fetch_trails import build
        build()
    st.success("Trail database ready!")
    st.rerun()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Pathfinder", page_icon="🧭", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 700; color: #1a1a1a; }
    .subtitle   { font-size: 1.1rem; color: #555; margin-top: -10px; }
    .score-good     { background: #d4edda; color: #155724; display:inline-block;
                      padding: 4px 12px; border-radius: 20px; font-size:.85rem; font-weight:600; margin:2px; }
    .score-moderate { background: #fff3cd; color: #856404; display:inline-block;
                      padding: 4px 12px; border-radius: 20px; font-size:.85rem; font-weight:600; margin:2px; }
    .score-poor     { background: #f8d7da; color: #721c24; display:inline-block;
                      padding: 4px 12px; border-radius: 20px; font-size:.85rem; font-weight:600; margin:2px; }
</style>
<div class="main-title">🧭 Pathfinder</div>
<div class="subtitle">Find your trail. Leave no trace. — AI-powered sustainable hiking in Greece.</div>
<hr/>
""", unsafe_allow_html=True)


# ── Conversation definition ───────────────────────────────────────────────────

STEPS = [
    {
        "id": "terrain",
        "question": "What kind of landscape are you dreaming of?",
        "options": [
            ("🏔️ Mountain", "mountain"),
            ("🌊 Coastal",   "coastal"),
            ("🌲 Forest",    "forest"),
            ("🗺️ Mixed — surprise me", "mixed"),
        ],
    },
    {
        "id": "duration_days",
        "question": "How many days are you planning for?",
        "options": [
            ("1 day",    1),
            ("2 days",   2),
            ("3 days",   3),
            ("4–7 days", 5),
        ],
    },
    {
        "id": "start_date",
        "question": "When are you planning to go? (Helps us pull real-time weather for your exact dates.)",
        "type": "date",
        "options": [
            ("This weekend", (datetime.date.today() + datetime.timedelta(days=(5 - datetime.date.today().weekday()) % 7 or 7)).isoformat()),
            ("Next week",    (datetime.date.today() + datetime.timedelta(days=7)).isoformat()),
            ("In 2 weeks",   (datetime.date.today() + datetime.timedelta(days=14)).isoformat()),
        ],
    },
    {
        "id": "fitness_level",
        "question": "What's your fitness level?",
        "options": [
            ("🐢 Easy-going", "low"),
            ("🚶 Average",    "medium"),
            ("🏃 Fit & active", "high"),
        ],
    },
    {
        "id": "difficulty",
        "question": "How challenging do you want the trail to be?",
        "options": [
            ("Easy",     "easy"),
            ("Moderate", "moderate"),
            ("Hard",     "hard"),
        ],
    },
    {
        "id": "interests",
        "question": "What do you love most on a hike? Pick all that apply.",
        "type": "multi",
        "options": [
            ("🦅 Wildlife",         "wildlife"),
            ("🏛️ History & ruins",  "history"),
            ("📸 Photography",      "photography"),
            ("🧘 Solitude",         "solitude"),
            ("🏘️ Local villages",  "local culture"),
            ("🌿 Nature & flora",   "nature"),
            ("🌅 Scenic views",     "views"),
        ],
    },
    {
        "id": "group_size",
        "question": "Who's coming with you?",
        "options": [
            ("Just me 🧍", 1),
            ("2 people",   2),
            ("3–5 people", 4),
            ("6+ people",  7),
        ],
    },
]

GREETING = (
    "👋 Hey! I'm **Pathfinder**, your AI trail companion for Greece. "
    "Let's find the perfect hike for you — I'll ask a few quick questions.\n\n"
    + STEPS[0]["question"]
)


# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    if "pf_messages" not in st.session_state:
        st.session_state.pf_messages = [{"role": "assistant", "content": GREETING}]
        st.session_state.pf_step     = 0
        st.session_state.pf_answers  = {}
        st.session_state.pf_done     = False
        st.session_state.pf_result   = None

_init()


def _record(display: str, value, step_id: str):
    """Add user answer to chat, save value, advance to the next question."""
    st.session_state.pf_messages.append({"role": "user", "content": display})
    st.session_state.pf_answers[step_id] = value
    nxt = st.session_state.pf_step + 1
    st.session_state.pf_step = nxt
    if nxt < len(STEPS):
        st.session_state.pf_messages.append({
            "role": "assistant",
            "content": STEPS[nxt]["question"],
        })
    else:
        st.session_state.pf_done = True
        st.session_state.pf_messages.append({
            "role": "assistant",
            "content": (
                "✅ Perfect! I've got everything I need.\n\n"
                "Press **Find my trails** below to get your personalised itinerary!"
            ),
        })


def _build_profile() -> dict:
    a = st.session_state.pf_answers

    def to_int(v, default):
        if isinstance(v, int):
            return v
        nums = re.findall(r"\d+", str(v))
        return int(nums[0]) if nums else default

    return {
        "duration_days": to_int(a.get("duration_days"), 2),
        "difficulty":    a.get("difficulty", "moderate") if a.get("difficulty") in ("easy", "moderate", "hard") else "moderate",
        "terrain":       a.get("terrain", "mixed") if a.get("terrain") in ("coastal", "mountain", "forest", "mixed") else "mixed",
        "interests":     a.get("interests", []) if isinstance(a.get("interests"), list) else [],
        "group_size":    to_int(a.get("group_size"), 1),
        "fitness_level": a.get("fitness_level", "medium") if a.get("fitness_level") in ("low", "medium", "high") else "medium",
        "start_date":    a.get("start_date", ""),
    }


# ── Chat display ──────────────────────────────────────────────────────────────

st.subheader("Plan your hike")

for msg in st.session_state.pf_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Current step input (shown below the chat history) ────────────────────────

if not st.session_state.pf_done:
    step     = st.session_state.pf_step
    step_def = STEPS[step]
    step_id  = step_def["id"]
    kind     = step_def.get("type", "buttons")

    st.write("")  # small gap

    if kind == "multi":
        selected = st.multiselect(
            "Your interests:",
            options=[lbl for lbl, _ in step_def["options"]],
            key="pf_multi",
            label_visibility="collapsed",
            placeholder="Choose one or more…",
        )
        if st.button("Confirm ✓", key="pf_multi_confirm"):
            vals    = [v for lbl, v in step_def["options"] if lbl in selected]
            display = ", ".join(selected) if selected else "No preference"
            _record(display, vals, step_id)
            st.rerun()

    elif kind == "date":
        quick_cols = st.columns(len(step_def["options"]))
        for i, (lbl, iso) in enumerate(step_def["options"]):
            if quick_cols[i].button(lbl, key=f"pf_date_quick_{i}", use_container_width=True):
                _record(lbl, iso, step_id)
                st.rerun()

        with st.form("pf_date_form"):
            picked = st.date_input(
                "Or pick an exact date:",
                min_value=datetime.date.today(),
                value=datetime.date.today() + datetime.timedelta(days=7),
            )
            if st.form_submit_button("Use this date →"):
                _record(picked.strftime("%B %d, %Y"), picked.isoformat(), step_id)
                st.rerun()

    else:
        btn_cols = st.columns(len(step_def["options"]))
        for i, (lbl, val) in enumerate(step_def["options"]):
            if btn_cols[i].button(lbl, key=f"pf_btn_{step_id}_{i}", use_container_width=True):
                _record(lbl, val, step_id)
                st.rerun()

    with st.expander("✏️ Type your own answer instead"):
        with st.form(f"pf_free_{step_id}"):
            free = st.text_input("Your answer:", label_visibility="collapsed")
            if st.form_submit_button("Submit →") and free.strip():
                _record(free.strip(), free.strip(), step_id)
                st.rerun()

# ── Action buttons ────────────────────────────────────────────────────────────

st.write("")
action_l, action_r = st.columns([4, 1])

if st.session_state.pf_done and st.session_state.pf_result is None:
    if action_l.button("🔍 Find my trails", type="primary", use_container_width=True):
        profile = _build_profile()
        with st.spinner("Searching trails, checking weather, scoring sustainability…"):
            try:
                result = run_pathfinder(profile=profile, verbose=False)
                st.session_state.pf_result = result
                st.rerun()
            except Exception as e:
                st.error(f"Something went wrong: {e}")

if action_r.button("🔄 Start over", use_container_width=True):
    for k in ["pf_messages", "pf_step", "pf_answers", "pf_done", "pf_result"]:
        st.session_state.pop(k, None)
    st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.pf_result:
    result = st.session_state.pf_result
    st.markdown("---")

    left, right = st.columns([3, 2])

    with left:
        p = result["profile"]
        date_str = f" · `{p['start_date']}`" if p.get("start_date") else ""
        st.markdown(f"""
**Your profile:** &nbsp;
`{p['duration_days']} day(s)` &nbsp;·&nbsp;
`{p['difficulty']}` &nbsp;·&nbsp;
`{p['terrain']}` &nbsp;·&nbsp;
`{p['fitness_level']} fitness`{date_str}
""")

        st.markdown("#### Sustainability Scores")
        for t in result["enriched_trails"]:
            s         = t["_sustainability"]
            score     = s["score"]
            label     = s["label"]
            breakdown = s["breakdown"]
            with st.expander(f"{label} &nbsp; **{t['name']}** — {score}/100", expanded=False):
                c1, c2 = st.columns(2)
                c1.metric("Crowd avoidance", f"{breakdown['crowd_avoidance']}/30")
                c2.metric("Remoteness",      f"{breakdown['remoteness']}/20")
                c1.metric("Biodiversity",    f"{breakdown['biodiversity']}/20")
                c2.metric("Local economy",   f"{breakdown['local_economy']}/20")

                w = t["_weather"]
                if w.get("temp_c") is not None:
                    st.markdown(
                        f"🌤 **Weather:** {w['temp_c']}°C, {w['conditions']} | "
                        f"💨 {w['wind_kmh']} km/h"
                    )
                for flag in w.get("safety_flags", []):
                    st.warning(flag)

                bio = t["_biodiversity"]
                if bio.get("notable_species"):
                    st.markdown(f"🦎 **Nearby species:** {', '.join(bio['notable_species'])}")

                route = t.get("_route", {})
                if route.get("distance_km") is not None:
                    st.markdown(
                        f"🥾 **Route estimate:** {route['distance_km']} km · "
                        f"{route['duration_h']} h (source: {route.get('source', 'n/a')})"
                    )

                elev = t.get("_elevation", {})
                if elev.get("min_m") is not None:
                    st.markdown(
                        f"⛰️ **Elevation (SRTM):** {elev['min_m']}–{elev['max_m']} m · "
                        f"gain {elev['gain_m']} m"
                    )

        st.markdown("---")
        st.markdown("#### Your Itinerary")
        st.markdown(result["itinerary"])

    with right:
        st.markdown("#### Trail Map")
        trails = result["enriched_trails"]
        if trails:
            avg_lat = sum(t["lat"] for t in trails) / len(trails)
            avg_lon = sum(t["lon"] for t in trails) / len(trails)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, tiles="OpenStreetMap")
            for i, t in enumerate(trails, 1):
                score = t["_sustainability"]["score"]
                color = "green" if score >= 60 else "orange" if score >= 40 else "red"
                popup_html = (
                    f"<b>{t['name']}</b><br>{t['region']}<br>"
                    f"Difficulty: {t['difficulty']}<br>Duration: {t['duration_hours']}h<br>"
                    f"Route: {t.get('_route', {}).get('distance_km', '?')} km<br>"
                    f"Elev gain: {t.get('_elevation', {}).get('gain_m', '?')} m<br>"
                    f"Sustainability: {score}/100"
                )
                folium.Marker(
                    location=[t["lat"], t["lon"]],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{i}. {t['name']}",
                    icon=folium.Icon(color=color, icon="leaf", prefix="fa"),
                ).add_to(m)
            st_folium(m, width=600, height=500)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<hr><p style='text-align:center;color:#aaa;font-size:0.8rem'>"
    "Pathfinder · Deloitte Makeathon 2026 · Data: OpenStreetMap, "
    "OpenRouteService, OpenWeatherMap, iNaturalist, NASA SRTM</p>",
    unsafe_allow_html=True,
)
