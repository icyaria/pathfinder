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
from backend.user_db import create_user, list_users, get_user_by_unique_id, authenticate_user
from backend.chat_history_db import create_history_entry, list_history_for_user
from backend.trail_details import get_accurate_stats, get_nearby_pois
from backend.trail_chat import chat_about_trail
from backend.saved_trails import save_trail, get_saved_trails, remove_saved_trail

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")
if not os.path.exists(DATA_PATH):
    with st.spinner("First launch: building trail database from OpenStreetMap… (this takes ~1 min)"):
        from scripts.fetch_trails import build
        build()
    st.success("Trail database ready!")
    st.rerun()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Pathfinder", page_icon="🧭", layout="wide")

# ── Session state initialization ──────────────────────────────────────────────
if "current_user_id" not in st.session_state:
    st.session_state["current_user_id"] = None
if "current_user_name" not in st.session_state:
    st.session_state["current_user_name"] = None

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


# ── Authentication UI ─────────────────────────────────────────────────────────
def show_auth_page():
    st.markdown("## Welcome to Pathfinder")
    st.markdown("Create an account or sign in to get started.")
    
    tab1, tab2 = st.tabs(["Sign Up", "Sign In"])
    
    with tab1:
        st.subheader("Create Your Account")
        with st.form("signup_form"):
            name = st.text_input("First Name", placeholder="e.g., Maria")
            surname = st.text_input("Last Name", placeholder="e.g., Papadopoulou")
            age = st.number_input("Age", min_value=1, max_value=120, step=1)
            gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])
            location = st.text_input("Location", placeholder="e.g., Athens, Greece")
            description = st.text_area(
                "Tell us about yourself (max 256 chars)",
                placeholder="e.g., I love remote mountain hikes with wildlife.",
                max_chars=256,
            )
            password = st.text_input("Password", type="password", placeholder="Min 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if not all([name, surname, gender, location, password, confirm_password]):
                    st.error("Please fill in all required fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        user = create_user(
                            name=name,
                            surname=surname,
                            age=int(age),
                            gender=gender,
                            location=location,
                            description=description or "",
                            password=password,
                        )
                        st.session_state["current_user_id"] = user["UserUniqieID"]
                        st.session_state["current_user_name"] = f"{user['Name']} {user['Surname']}"
                        st.success(f"✅ Welcome, {user['Name']}! Your ID: {user['UserUniqieID']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating account: {e}")
    
    with tab2:
        st.subheader("Sign In")
        users = list_users()
        if not users:
            st.info("No accounts yet. Please sign up first.")
        else:
            user_options = [f"{u['Name']} {u['Surname']} ({u['UserUniqieID']})" for u in users]
            selected = st.selectbox("Select your account", user_options)
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.button("Sign In", type="primary"):
                user_id = selected.split("(")[1].rstrip(")")
                authenticated_user = authenticate_user(user_id, password_input)
                if authenticated_user:
                    st.session_state["current_user_id"] = user_id
                    st.session_state["current_user_name"] = f"{authenticated_user['Name']} {authenticated_user['Surname']}"
                    st.success(f"✅ Welcome back, {authenticated_user['Name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Please try again.")


# ── Main app (only show if authenticated) ─────────────────────────────────────
if not st.session_state["current_user_id"]:
    show_auth_page()
    st.stop()

# Display user header
st.sidebar.markdown(f"**User:** {st.session_state.get('current_user_name', 'Unknown')}")
if st.sidebar.button("Sign Out"):
    st.session_state["current_user_id"] = None
    st.session_state["current_user_name"] = None
    st.rerun()

uid = st.session_state.get("current_user_id")
saved = get_saved_trails(uid) if uid else []
if saved:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📌 Your planned trails:**")
    for s in saved:
        date_str = f" · {s['planned_date']}" if s.get("planned_date") else ""
        st.sidebar.caption(f"🥾 {s['trail_name']}{date_str}")


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
    if "pf_planned_trail"  not in st.session_state:
        st.session_state.pf_planned_trail  = None  # full enriched trail dict
    if "pf_trail_stats"    not in st.session_state:
        st.session_state.pf_trail_stats    = None
    if "pf_trail_pois"     not in st.session_state:
        st.session_state.pf_trail_pois     = None
    if "pf_trail_chat"     not in st.session_state:
        st.session_state.pf_trail_chat     = []    # list of {role, content}

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


def _extract_user_messages() -> list:
    """Extract free-text user messages from pf_messages."""
    messages = []
    for msg in st.session_state.pf_messages:
        if msg["role"] == "user":
            content = msg.get("content", "").strip()
            if content:
                messages.append(content)
    return messages


def _extract_quick_prompts() -> list:
    """Extract button-selected prompts (quick examples)."""
    prompts = []
    example_prompts = [
        "3-day hard mountain hike far from tourists, I love wildlife and remote landscapes",
        "Easy 1-day coastal walk with great views, small group of 2",
        "Moderate forest hike, interested in history and local villages",
    ]
    messages_text = " ".join(msg.get("content", "") for msg in st.session_state.pf_messages)
    for ex in example_prompts:
        if ex in messages_text and ex not in prompts:
            prompts.append(ex)
    return prompts


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
                
                # Save to chat history
                try:
                    user_id = st.session_state.get("current_user_id")
                    if user_id:
                        user_messages = _extract_user_messages()
                        quick_prompts = _extract_quick_prompts()
                        key_data = {
                            "duration_days": profile.get("duration_days"),
                            "difficulty": profile.get("difficulty"),
                            "terrain": profile.get("terrain"),
                            "interests": profile.get("interests"),
                            "fitness_level": profile.get("fitness_level"),
                            "start_date": profile.get("start_date"),
                            "matched_trail_count": len(result.get("enriched_trails", [])),
                        }
                        history = create_history_entry(
                            user_uniqie_id=user_id,
                            key_data=key_data,
                            user_messages=user_messages,
                            quick_select_prompts_chosen=quick_prompts,
                        )
                        st.session_state["last_history_id"] = history["HistoryUniqueID"]
                except Exception as history_err:
                    st.warning(f"Could not save chat history: {history_err}")
                
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
                # ── Score breakdown ───────────────────────────────────────────
                c1, c2, c3 = st.columns(3)
                c1.metric("Crowd avoidance", f"{breakdown['crowd_avoidance']}/25")
                c2.metric("Remoteness",      f"{breakdown['remoteness']}/15")
                c3.metric("Biodiversity",    f"{breakdown['biodiversity']}/20")
                c1.metric("Local economy",   f"{breakdown['local_economy']}/20")
                c2.metric("Weather score",   f"{breakdown['weather']}/20")

                # ── OSM crowd/economy raw data ────────────────────────────────
                ce = t.get("_crowd_economy", {})
                if ce.get("_crowd_poi_count") is not None:
                    st.caption(
                        f"📍 {ce['_crowd_poi_count']} tourism POIs within 3 km · "
                        f"🏘️ {ce['_economy_poi_count']} local amenities within 10 km"
                    )

                # ── Weather calendar ──────────────────────────────────────────
                cal = t.get("_weather_calendar", [])
                if cal:
                    st.markdown("**Weather forecast around your hike dates:**")
                    day_cols = st.columns(len(cal))
                    for ci, day in enumerate(cal):
                        with day_cols[ci]:
                            d_label = day["date"][5:]  # MM-DD
                            if day.get("is_planned"):
                                st.markdown(f"**{d_label}**\n\n🎯 *your hike*")
                            else:
                                st.markdown(f"**{d_label}**")

                            if not day.get("available"):
                                reason = day.get("reason", "")
                                if reason == "too_far":
                                    st.caption("📅 Beyond\n5-day\nforecast")
                                elif reason == "past":
                                    st.caption("—")
                                else:
                                    st.caption("No data")
                            else:
                                st.markdown(day.get("emoji", "🌡️"))
                                st.caption(
                                    f"{day.get('temp_c', '?')}°C\n"
                                    f"{day.get('conditions', '')}"
                                )

                # ── Safety flags ──────────────────────────────────────────────
                for flag in t["_weather"].get("safety_flags", []):
                    st.warning(flag)

                # ── Biodiversity ──────────────────────────────────────────────
                bio = t["_biodiversity"]
                if bio.get("notable_species"):
                    st.markdown(f"🦎 **Nearby species:** {', '.join(bio['notable_species'])}")

                # ── Route & elevation ─────────────────────────────────────────
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

                st.divider()
                already_planned = (
                    st.session_state.pf_planned_trail is not None
                    and st.session_state.pf_planned_trail.get("name") == t.get("name")
                )
                if already_planned:
                    st.success("📌 Trail planned — see details below")
                elif st.button(f"📌 Plan this trail", key=f"plan_{t['name']}", type="primary"):
                    with st.spinner("Loading trail details & nearby attractions…"):
                        stats = get_accurate_stats(t)
                        pois  = get_nearby_pois(t["lat"], t["lon"])
                    st.session_state.pf_planned_trail = t
                    st.session_state.pf_trail_stats   = stats
                    st.session_state.pf_trail_pois    = pois
                    st.session_state.pf_trail_chat    = []
                    # Save to DB
                    uid = st.session_state.get("current_user_id")
                    if uid:
                        try:
                            save_trail(uid, t, st.session_state.pf_answers)
                        except Exception:
                            pass
                    st.rerun()

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

# ── Planned trail detail page ─────────────────────────────────────────────────

if st.session_state.pf_planned_trail:
    t     = st.session_state.pf_planned_trail
    stats = st.session_state.pf_trail_stats or {}
    pois  = st.session_state.pf_trail_pois  or []

    st.markdown("---")
    st.markdown(f"## 📌 Your Planned Trail: **{t['name']}**")
    st.caption(f"{t.get('region', '')}  ·  Sustainability {t['_sustainability']['score']}/100  {t['_sustainability']['label']}")

    # ── Accurate stats bar ────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Distance",   f"{stats.get('distance_km', '?')} km",
               help=f"Source: {stats.get('source', '?')}")
    sc2.metric("Est. time",  f"{stats.get('duration_h', '?')} h",
               help="Naismith's Rule: 4 km/h + 1 h per 600 m ascent")
    sc3.metric("Difficulty", stats.get("difficulty", "?").capitalize())
    sc4.metric("Ascent",     f"{stats.get('ascent_m', '?')} m")
    sc5.metric("Terrain",    t.get("terrain", "?").capitalize())

    if stats.get("source") == "estimated":
        st.caption("⚠️ Distance estimated — OSM tags and ORS unavailable for this trail.")
    elif stats.get("source") == "osm_tags":
        st.caption("✅ Distance from official OSM trail tags.")

    detail_left, detail_right = st.columns([1, 1])

    # ── Left: info + chat ─────────────────────────────────────────────────────
    with detail_left:
        # Highlights
        if t.get("highlights"):
            st.markdown("**Highlights:** " + " · ".join(t["highlights"]))

        # Weather on planned day
        w = t.get("_weather", {})
        if w.get("temp_c") is not None:
            st.markdown(
                f"🌤 **Weather on your date:** {w['temp_c']}°C, {w['conditions']} · "
                f"💨 {w['wind_kmh']} km/h"
            )
        for flag in w.get("safety_flags", []):
            st.warning(flag)

        # Biodiversity
        bio = t.get("_biodiversity", {})
        if bio.get("notable_species"):
            st.markdown(f"🦎 **Nearby wildlife:** {', '.join(bio['notable_species'])}")

        st.markdown("---")

        # ── Chat ──────────────────────────────────────────────────────────────
        st.markdown("#### 💬 Ask about this trail")
        st.caption("Ask anything — what to pack, safety tips, nearby villages, wildlife, best season…")

        for msg in st.session_state.pf_trail_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_q = st.chat_input("Ask a question about this trail…", key="trail_chat_input")
        if user_q:
            st.session_state.pf_trail_chat.append({"role": "user", "content": user_q})
            with st.spinner("Thinking…"):
                reply = chat_about_trail(
                    trail=t,
                    stats=stats,
                    pois=pois,
                    history=st.session_state.pf_trail_chat[:-1],
                    user_message=user_q,
                )
            st.session_state.pf_trail_chat.append({"role": "assistant", "content": reply})
            st.rerun()

        if st.session_state.pf_trail_chat:
            if st.button("Clear chat", key="clear_trail_chat"):
                st.session_state.pf_trail_chat = []
                st.rerun()

    # ── Right: POI map ────────────────────────────────────────────────────────
    with detail_right:
        st.markdown("#### 🗺️ Trail & Nearby Attractions")

        m2 = folium.Map(location=[t["lat"], t["lon"]], zoom_start=12, tiles="OpenStreetMap")

        # Trail marker (large)
        folium.Marker(
            location=[t["lat"], t["lon"]],
            tooltip=t["name"],
            popup=folium.Popup(f"<b>{t['name']}</b><br>{t.get('region','')}", max_width=200),
            icon=folium.Icon(color="darkgreen", icon="flag", prefix="fa"),
        ).add_to(m2)

        # POI markers
        COLOR_MAP = {
            "blue": "blue", "gray": "gray", "purple": "purple",
            "green": "green", "red": "red", "lightblue": "lightblue",
            "white": "white", "beige": "beige",
        }
        for poi in pois:
            folium.Marker(
                location=[poi["lat"], poi["lon"]],
                tooltip=f"{poi['emoji']} {poi['name']}",
                popup=folium.Popup(
                    f"<b>{poi['name']}</b><br>{poi['category']}", max_width=160
                ),
                icon=folium.Icon(
                    color=COLOR_MAP.get(poi["color"], "beige"),
                    icon="circle", prefix="fa",
                ),
            ).add_to(m2)

        st_folium(m2, width=560, height=460, key="detail_map")

        # POI legend
        if pois:
            st.markdown("**Nearby attractions:**")
            by_cat = {}
            for p in pois:
                by_cat.setdefault(p["category"], []).append(p)
            for cat, items in by_cat.items():
                emoji = items[0]["emoji"]
                names = ", ".join(
                    p["name"] for p in items[:4] if p["name"] != cat
                ) or f"{len(items)} locations"
                st.caption(f"{emoji} **{cat}** ({len(items)}): {names}")

    # ── Unplan button ─────────────────────────────────────────────────────────
    if st.button("✕ Remove from plan", key="unplan_trail"):
        uid = st.session_state.get("current_user_id")
        if uid:
            remove_saved_trail(uid, t.get("name"))
        st.session_state.pf_planned_trail = None
        st.session_state.pf_trail_stats   = None
        st.session_state.pf_trail_pois    = None
        st.session_state.pf_trail_chat    = []
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<hr><p style='text-align:center;color:#aaa;font-size:0.8rem'>"
    "Pathfinder · Deloitte Makeathon 2026 · Data: OpenStreetMap, "
    "OpenRouteService, OpenWeatherMap, iNaturalist, NASA SRTM</p>",
    unsafe_allow_html=True,
)
