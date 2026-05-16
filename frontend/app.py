"""
frontend/app.py — Pathfinder Streamlit UI

Run with:
  streamlit run frontend/app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import folium
from streamlit_folium import st_folium
from pipeline import run_pathfinder

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")
if not os.path.exists(DATA_PATH):
    with st.spinner("First launch: building trail database from OpenStreetMap… (this takes ~1 min)"):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.fetch_trails import build
        build()
    st.success("Trail database ready!")
    st.rerun()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pathfinder",
    page_icon="🧭",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 700; color: #1a1a1a; }
    .subtitle   { font-size: 1.1rem; color: #555; margin-top: -10px; }
    .score-pill {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.85rem; font-weight: 600; margin: 2px;
    }
    .score-good     { background: #d4edda; color: #155724; }
    .score-moderate { background: #fff3cd; color: #856404; }
    .score-poor     { background: #f8d7da; color: #721c24; }
</style>
<div class="main-title">🧭 Pathfinder</div>
<div class="subtitle">Find your trail. Leave no trace. — AI-powered sustainable hiking in Greece.</div>
<hr/>
""", unsafe_allow_html=True)

# ── Input ────────────────────────────────────────────────────────────────────
st.subheader("Tell us about your ideal hike")

if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
if "latest_result" not in st.session_state:
    st.session_state["latest_result"] = None

example_prompts = [
    "3-day hard mountain hike far from tourists, I love wildlife and remote landscapes",
    "Easy 1-day coastal walk with great views, small group of 2",
    "Moderate forest hike, interested in history and local villages",
]

col1, col2 = st.columns([3, 1])
with col1:
    st.text_area(
        label="Describe your hike",
        placeholder=example_prompts[0],
        height=100,
        label_visibility="collapsed",
        key="user_input",
    )
with col2:
    st.markdown("**Quick examples:**")
    for p in example_prompts:
        if st.button(p[:55] + "…", use_container_width=True):
            st.session_state["user_input"] = p

run_btn = st.button("🔍 Find my trails", type="primary", use_container_width=True)

# ── Run pipeline ─────────────────────────────────────────────────────────────
if run_btn and st.session_state["user_input"].strip():
    with st.spinner("Searching trails, checking weather, scoring sustainability…"):
        try:
            result = run_pathfinder(st.session_state["user_input"], verbose=False)
            st.session_state["latest_result"] = result
        except FileNotFoundError:
            st.error(
                "⚠️ Trail database not found. "
                "Run `python scripts/fetch_trails.py` first."
            )
            st.stop()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

if st.session_state["latest_result"]:
    result = st.session_state["latest_result"]

    # ── Layout: left = results, right = map ──────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        # Profile pill summary
        p = result["profile"]
        st.markdown(f"""
**Your profile:** &nbsp;
`{p['duration_days']} day(s)` &nbsp;·&nbsp;
`{p['difficulty']}` &nbsp;·&nbsp;
`{p['terrain']}` &nbsp;·&nbsp;
`{p['fitness_level']} fitness`
""")

        # Sustainability scores table
        st.markdown("#### Sustainability Scores")
        for t in result["enriched_trails"]:
            s     = t["_sustainability"]
            score = s["score"]
            label = s["label"]
            css   = (
                "score-good" if score >= 60
                else "score-moderate" if score >= 40
                else "score-poor"
            )
            breakdown = s["breakdown"]
            with st.expander(f"{label} &nbsp; **{t['name']}** — {score}/100", expanded=False):
                c1, c2 = st.columns(2)
                c1.metric("Crowd avoidance", f"{breakdown['crowd_avoidance']}/30")
                c2.metric("Remoteness",       f"{breakdown['remoteness']}/20")
                c1.metric("Biodiversity",     f"{breakdown['biodiversity']}/20")
                c2.metric("Local economy",    f"{breakdown['local_economy']}/20")

                w = t["_weather"]
                if w.get("temp_c") is not None:
                    st.markdown(
                        f"🌤 **Weather:** {w['temp_c']}°C, {w['conditions']} | "
                        f"💨 {w['wind_kmh']} km/h"
                    )
                if w.get("safety_flags"):
                    for flag in w["safety_flags"]:
                        st.warning(flag)

                bio = t["_biodiversity"]
                if bio.get("notable_species"):
                    st.markdown(
                        f"🦎 **Nearby species:** {', '.join(bio['notable_species'])}"
                    )

                route = t.get("_route", {})
                if route.get("distance_km") is not None:
                    st.markdown(
                        f"🥾 **Route estimate:** {route['distance_km']} km · "
                        f"{route['duration_h']} h (source: {route.get('source', 'n/a')})"
                    )

                elev = t.get("_elevation", {})
                if elev.get("min_m") is not None:
                    st.markdown(
                        f"⛰️ **Elevation (SRTM):** {elev['min_m']}-{elev['max_m']} m · "
                        f"gain {elev['gain_m']} m"
                    )

        # Itinerary
        st.markdown("---")
        st.markdown("#### Your Itinerary")
        st.markdown(result["itinerary"])

    with right:
        st.markdown("#### Trail Map")
        trails = result["enriched_trails"]
        if trails:
            # Centre map on the mean position of matched trails
            avg_lat = sum(t["lat"] for t in trails) / len(trails)
            avg_lon = sum(t["lon"] for t in trails) / len(trails)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, tiles="OpenStreetMap")

            for i, t in enumerate(trails, 1):
                score = t["_sustainability"]["score"]
                color = (
                    "green"  if score >= 60
                    else "orange" if score >= 40
                    else "red"
                )
                popup_html = f"""
                    <b>{t['name']}</b><br>
                    {t['region']}<br>
                    Difficulty: {t['difficulty']}<br>
                    Duration: {t['duration_hours']}h<br>
                    Route: {t.get('_route', {}).get('distance_km', '?')} km<br>
                    Elev gain: {t.get('_elevation', {}).get('gain_m', '?')} m<br>
                    Sustainability: {score}/100
                """
                folium.Marker(
                    location=[t["lat"], t["lon"]],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{i}. {t['name']}",
                    icon=folium.Icon(color=color, icon="leaf", prefix="fa"),
                ).add_to(m)

            st_folium(m, width=600, height=500)

elif run_btn:
    st.warning("Please enter a description of your hike first.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    "<hr><p style='text-align:center;color:#aaa;font-size:0.8rem'>"
    "Pathfinder · Deloitte Makeathon 2026 · Data: OpenStreetMap, "
    "OpenRouteService, OpenWeatherMap, iNaturalist, NASA SRTM</p>",
    unsafe_allow_html=True,
)
