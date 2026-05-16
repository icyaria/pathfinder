"""
frontend/app.py — Pathfinder Streamlit UI
"""

import sys, os, datetime, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import folium
from streamlit_folium import st_folium
from pipeline import run_pathfinder
from backend.trail_details import get_accurate_stats, get_nearby_pois
from backend.trail_chat import chat_about_trail
from backend.saved_trails import save_trail, get_saved_trails, remove_saved_trail

try:
    from backend.user_db import create_user, list_users, authenticate_user
    from backend.chat_history_db import create_history_entry
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Pathfinder — Sustainable Hiking in Greece",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state init ────────────────────────────────────────────────────────
for _k, _v in [("page", "home"), ("current_user_id", None), ("current_user_name", None)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── URL-param routing ─────────────────────────────────────────────────────────
_nav = st.query_params.get("nav", "")
if _nav == "home":
    st.session_state.page = "home"
elif _nav in ("auth", "explore"):
    st.session_state.page = "explore" if st.session_state.current_user_id else "auth"


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

def inject_css(page: str = "home"):
    hide_sidebar = (
        "[data-testid='stSidebar'] { display: none !important; }"
        if page != "explore" else ""
    )
    container_css = (
        "padding: 0 !important; max-width: 100% !important;"
        if page == "home"
        else "padding: 1rem 2rem 2rem !important; max-width: 1280px !important; margin: 0 auto !important;"
    )
    st.markdown(f"""<style>
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}
.block-container {{ {container_css} }}
.stApp {{ background: #f5f3ee; }}
body {{ overflow-x: hidden; }}
{hide_sidebar}

:root {{
  --nav:    #161b14;
  --olive:  #6b7a3f;
  --olivel: #8a9c52;
  --cream:  #f5f3ee;
}}

/* ── Nav ─────────────────────────────────────────────────────────────────── */
.pf-nav {{
  position: sticky; top: 0; z-index: 9999;
  background: var(--nav);
  display: flex; align-items: center;
  padding: 0 52px; height: 62px;
  box-shadow: 0 2px 16px rgba(0,0,0,.4);
}}
.pf-nav-logo {{
  font-size: 1.18rem; font-weight: 800; color: #fff;
  text-decoration: none; letter-spacing: .02em; margin-right: 44px;
  white-space: nowrap;
}}
.pf-nav-logo span {{ color: var(--olivel); }}
.pf-nav-links {{ display: flex; gap: 28px; flex: 1; }}
.pf-nav-links a {{
  color: rgba(255,255,255,.62); font-size: .88rem;
  text-decoration: none; letter-spacing: .03em; transition: color .2s;
}}
.pf-nav-links a:hover, .pf-nav-links a.active {{ color: #fff; }}
.pf-nav-right {{ display: flex; align-items: center; gap: 10px; }}
.pf-btn-ghost {{
  color: rgba(255,255,255,.72); background: transparent;
  border: 1px solid rgba(255,255,255,.28);
  padding: 7px 18px; border-radius: 6px; font-size: .84rem;
  cursor: pointer; text-decoration: none; transition: all .2s;
}}
.pf-btn-ghost:hover {{ border-color: #fff; color: #fff; }}
.pf-btn-olive {{
  background: var(--olive); color: #fff; border: none;
  padding: 8px 20px; border-radius: 22px; font-size: .84rem;
  cursor: pointer; text-decoration: none; font-weight: 700;
  transition: background .2s;
}}
.pf-btn-olive:hover {{ background: var(--olivel); }}

/* ── Hero ────────────────────────────────────────────────────────────────── */
.pf-hero {{
  min-height: 560px;
  background:
    linear-gradient(135deg,rgba(10,21,8,.88) 0%,rgba(22,44,18,.78) 55%,rgba(10,21,8,.65) 100%),
    url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1600&q=80') center/cover no-repeat;
  display: flex; align-items: center;
  padding: 100px 80px 80px;
}}
.pf-hero-content {{ max-width: 590px; animation: fadeUp .7s ease; }}
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(18px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
.pf-hero-badge {{
  display: inline-block;
  background: rgba(107,122,63,.28); border: 1px solid rgba(138,156,82,.55);
  color: #aec86a; font-size: .74rem; font-weight: 800;
  padding: 5px 14px; border-radius: 20px;
  letter-spacing: .11em; text-transform: uppercase; margin-bottom: 22px;
}}
.pf-hero h1 {{
  font-size: 3.4rem; font-weight: 800; color: #fff;
  line-height: 1.08; margin: 0 0 18px; letter-spacing: -.02em;
}}
.pf-hero h1 em {{ font-style: normal; color: #aec86a; }}
.pf-hero-sub {{
  font-size: 1.05rem; color: rgba(255,255,255,.76);
  line-height: 1.68; margin-bottom: 36px;
}}
.pf-hero-ctas {{ display: flex; gap: 14px; flex-wrap: wrap; }}
.pf-cta-p {{
  background: var(--olive); color: #fff;
  padding: 14px 30px; border-radius: 8px; font-weight: 700;
  text-decoration: none; font-size: .96rem; display: inline-block;
  transition: background .2s, transform .15s;
}}
.pf-cta-p:hover {{ background: var(--olivel); transform: translateY(-2px); }}
.pf-cta-s {{
  background: rgba(255,255,255,.1); color: #fff;
  border: 1.5px solid rgba(255,255,255,.32);
  padding: 13px 28px; border-radius: 8px; font-weight: 600;
  text-decoration: none; font-size: .96rem; display: inline-block;
  transition: all .2s;
}}
.pf-cta-s:hover {{ background: rgba(255,255,255,.2); }}

/* ── Content sections ────────────────────────────────────────────────────── */
.pf-sec     {{ padding: 72px 80px; }}
.pf-sec-alt {{ padding: 72px 80px; background: #e8e4db; }}
.pf-sec-eyebrow {{
  font-size: .72rem; font-weight: 800; letter-spacing: .14em;
  color: var(--olive); text-transform: uppercase; margin-bottom: 10px;
}}
.pf-sec h2 {{
  font-size: 1.9rem; font-weight: 800; color: #1a1a1a;
  margin: 0 0 10px; letter-spacing: -.01em;
}}
.pf-sec-lead {{ color: #6b6b6b; font-size: .96rem; margin-bottom: 44px; }}

/* ── Trail cards ─────────────────────────────────────────────────────────── */
.pf-cards {{ display: flex; gap: 20px; flex-wrap: wrap; }}
.pf-card {{
  flex: 1; min-width: 240px; min-height: 310px; border-radius: 16px;
  overflow: hidden; position: relative;
  display: flex; flex-direction: column; justify-content: flex-end;
  padding: 22px; color: #fff; text-decoration: none;
  box-shadow: 0 8px 36px rgba(0,0,0,.22);
  transition: transform .25s, box-shadow .25s;
}}
.pf-card:hover {{ transform: translateY(-5px); box-shadow: 0 20px 56px rgba(0,0,0,.32); }}
.pf-card-mountain {{ background: linear-gradient(160deg,#1a3018 0%,#2d5a1e 50%,#152812 100%); }}
.pf-card-coastal  {{ background: linear-gradient(160deg,#0c2a4a 0%,#174a7a 50%,#0a2240 100%); }}
.pf-card-forest   {{ background: linear-gradient(160deg,#0e220e 0%,#1d4019 50%,#0b1f0b 100%); }}
.pf-card-mixed    {{ background: linear-gradient(160deg,#2a200e 0%,#4a3c1a 50%,#221a08 100%); }}
.pf-card-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(to top,rgba(0,0,0,.78) 0%,transparent 55%);
}}
.pf-card-top {{
  position: absolute; top: 16px; left: 16px; right: 16px;
  display: flex; gap: 6px; flex-wrap: wrap;
}}
.pf-bdg {{
  background: rgba(0,0,0,.45); backdrop-filter: blur(6px);
  color: #fff; font-size: .7rem; font-weight: 700;
  padding: 4px 10px; border-radius: 10px;
  border: 1px solid rgba(255,255,255,.18);
}}
.pf-bdg-green {{ background: rgba(107,122,63,.7); border-color: rgba(138,156,82,.8); }}
.pf-card-body {{ position: relative; z-index: 1; }}
.pf-card-rgn  {{ font-size: .72rem; color: rgba(255,255,255,.55); margin-bottom: 4px; }}
.pf-card h3   {{ font-size: 1.15rem; font-weight: 800; margin: 0 0 7px; }}
.pf-card-det  {{ font-size: .8rem; color: rgba(255,255,255,.65); }}
.pf-stars     {{ color: #f0c040; font-size: .82rem; margin-bottom: 5px; }}

/* ── Feature cards ───────────────────────────────────────────────────────── */
.pf-feats {{ display: flex; gap: 18px; flex-wrap: wrap; }}
.pf-feat {{
  flex: 1; min-width: 240px; border-radius: 16px;
  padding: 28px; background: #fff;
  box-shadow: 0 2px 20px rgba(0,0,0,.06);
}}
.pf-feat-dk  {{ background: #1a2416; }}
.pf-feat-dk2 {{ background: #253318; }}
.pf-feat-ico {{ font-size: 2rem; margin-bottom: 14px; }}
.pf-feat h3  {{ font-size: 1.05rem; font-weight: 800; margin: 0 0 8px; color: #1a1a1a; }}
.pf-feat-dk  h3, .pf-feat-dk2 h3 {{ color: #fff; }}
.pf-feat p   {{ font-size: .86rem; color: #666; line-height: 1.6; margin: 0; }}
.pf-feat-dk  p, .pf-feat-dk2 p {{ color: rgba(255,255,255,.55); }}
.pf-weather-box {{
  background: #eef3e4; border-radius: 10px;
  padding: 14px 16px; margin-top: 16px;
  display: flex; align-items: center; gap: 14px;
}}
.pf-weather-temp {{ font-size: 1.9rem; font-weight: 800; color: #2a4818; }}
.pf-weather-info {{ font-size: .8rem; color: #555; line-height: 1.5; }}
.pf-event-tag {{
  display: inline-block; background: rgba(107,122,63,.2);
  color: #8ab040; font-size: .7rem; font-weight: 800;
  padding: 3px 10px; border-radius: 10px; margin-bottom: 10px;
  letter-spacing: .07em; text-transform: uppercase;
}}
.pf-quote      {{ font-style:italic; color:rgba(255,255,255,.72); font-size:.86rem; margin-top:14px; line-height:1.55; }}
.pf-quote-attr {{ color:rgba(255,255,255,.38); font-size:.76rem; margin-top:5px; }}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.pf-footer {{
  background: #0c1009; color: rgba(255,255,255,.44);
  padding: 44px 80px;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 20px;
}}
.pf-footer-logo {{ font-size: 1.1rem; font-weight: 800; color: #fff; }}
.pf-footer-logo span {{ color: var(--olivel); }}
.pf-footer p  {{ font-size: .78rem; margin: 6px 0 0; }}
.pf-footer-links {{ display: flex; gap: 22px; }}
.pf-footer-links a {{
  color: rgba(255,255,255,.38); font-size: .78rem;
  text-decoration: none; transition: color .2s;
}}
.pf-footer-links a:hover {{ color: rgba(255,255,255,.75); }}

/* ── Explore score badges ─────────────────────────────────────────────────── */
.score-good     {{ background:#d4edda; color:#155724; display:inline-block;
                   padding:4px 12px; border-radius:20px; font-size:.85rem; font-weight:600; margin:2px; }}
.score-moderate {{ background:#fff3cd; color:#856404; display:inline-block;
                   padding:4px 12px; border-radius:20px; font-size:.85rem; font-weight:600; margin:2px; }}
.score-poor     {{ background:#f8d7da; color:#721c24; display:inline-block;
                   padding:4px 12px; border-radius:20px; font-size:.85rem; font-weight:600; margin:2px; }}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════

_TERRAIN_CLS = {"mountain":"pf-card-mountain","coastal":"pf-card-coastal",
                "forest":"pf-card-forest","mixed":"pf-card-mixed"}
_TERRAIN_EMJ = {"mountain":"🏔️","coastal":"🌊","forest":"🌲","mixed":"🗺️"}


def _load_featured(n: int = 3) -> list:
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            all_t = json.load(f)
        out, seen = [], set()
        for t in all_t:
            ter = t.get("terrain", "mixed")
            if ter not in seen:
                out.append(t)
                seen.add(ter)
            if len(out) >= n:
                break
        for t in all_t:
            if len(out) >= n:
                break
            if t not in out:
                out.append(t)
        return out[:n]
    except Exception:
        return []


def _card_html(t: dict) -> str:
    ter  = t.get("terrain", "mixed")
    diff = t.get("difficulty", "moderate").capitalize()
    dur  = t.get("duration_hours", "?")
    sus  = t.get("sustainability_score")
    sus_bdg = f'<span class="pf-bdg pf-bdg-green">♻ {sus}/100</span>' if sus else ""
    return f"""<a href="?nav=explore" class="pf-card {_TERRAIN_CLS.get(ter,'pf-card-mixed')}">
  <div class="pf-card-overlay"></div>
  <div class="pf-card-top">
    <span class="pf-bdg">{_TERRAIN_EMJ.get(ter,'🗺️')} {ter.capitalize()}</span>
    <span class="pf-bdg">{diff}</span>{sus_bdg}
  </div>
  <div class="pf-card-body">
    <div class="pf-stars">★★★★☆</div>
    <div class="pf-card-rgn">{t.get('region','Greece')}</div>
    <h3>{t.get('name','Trail')}</h3>
    <div class="pf-card-det">⏱ {dur}h &nbsp;·&nbsp; {diff}</div>
  </div>
</a>"""


_PLACEHOLDER_CARDS = """
<a href="?nav=explore" class="pf-card pf-card-mountain">
  <div class="pf-card-overlay"></div>
  <div class="pf-card-top"><span class="pf-bdg">🏔️ Mountain</span><span class="pf-bdg">Hard</span></div>
  <div class="pf-card-body">
    <div class="pf-stars">★★★★★</div>
    <div class="pf-card-rgn">Mount Olympus, Pieria</div>
    <h3>Mytikas Summit Trail</h3>
    <div class="pf-card-det">⏱ 8h &nbsp;·&nbsp; Hard</div>
  </div>
</a>
<a href="?nav=explore" class="pf-card pf-card-coastal">
  <div class="pf-card-overlay"></div>
  <div class="pf-card-top"><span class="pf-bdg">🌊 Coastal</span><span class="pf-bdg">Easy</span></div>
  <div class="pf-card-body">
    <div class="pf-stars">★★★★☆</div>
    <div class="pf-card-rgn">Santorini, Cyclades</div>
    <h3>Caldera Rim Walk</h3>
    <div class="pf-card-det">⏱ 3h &nbsp;·&nbsp; Easy</div>
  </div>
</a>
<a href="?nav=explore" class="pf-card pf-card-forest">
  <div class="pf-card-overlay"></div>
  <div class="pf-card-top"><span class="pf-bdg">🌲 Forest</span><span class="pf-bdg">Moderate</span></div>
  <div class="pf-card-body">
    <div class="pf-stars">★★★★☆</div>
    <div class="pf-card-rgn">Zagori, Epirus</div>
    <h3>Vikos Gorge Path</h3>
    <div class="pf-card-det">⏱ 6h &nbsp;·&nbsp; Moderate</div>
  </div>
</a>"""


def render_home():
    inject_css("home")

    uid = st.session_state.current_user_id
    name = st.session_state.current_user_name or ""
    if uid:
        first = name.split()[0] if name else "Explorer"
        nav_right = f'<span style="color:rgba(255,255,255,.6);font-size:.84rem">Hi, {first}!</span> <a href="?nav=explore" class="pf-btn-olive">Open App →</a>'
    else:
        nav_right = '<a href="?nav=auth" class="pf-btn-ghost">Login</a> <a href="?nav=auth" class="pf-btn-olive">Sign Up</a>'

    st.markdown(f"""
<div class="pf-nav">
  <a class="pf-nav-logo" href="?nav=home">Path<span>Finder</span></a>
  <div class="pf-nav-links">
    <a href="?nav=explore" class="active">Explore</a>
    <a href="?nav=home">About Us</a>
  </div>
  <div class="pf-nav-right">{nav_right}</div>
</div>

<div class="pf-hero">
  <div class="pf-hero-content">
    <div class="pf-hero-badge">🌿 Sustainable Trekking v2.0</div>
    <h1>Discover Greece's<br><em>Hidden Trails</em></h1>
    <p class="pf-hero-sub">
      AI-powered trail recommendations that match your pace, protect local ecosystems,
      and connect you with the authentic soul of Greece.
    </p>
    <div class="pf-hero-ctas">
      <a href="?nav=explore" class="pf-cta-p">Start New Trail</a>
      <a href="?nav=explore" class="pf-cta-s">Consult AI Guide</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    featured = _load_featured(3)
    cards_html = "".join(_card_html(t) for t in featured) if featured else _PLACEHOLDER_CARDS

    st.markdown(f"""
<div class="pf-sec">
  <div class="pf-sec-eyebrow">Featured Paths</div>
  <h2>Trails Worth The Journey</h2>
  <p class="pf-sec-lead">Hand-scored for sustainability, biodiversity, and authentic local experience.</p>
  <div class="pf-cards">{cards_html}</div>
</div>

<div class="pf-sec-alt">
  <div class="pf-sec-eyebrow">Engineered for the Wild</div>
  <h2>Every Step, Data-Backed</h2>
  <p class="pf-sec-lead">Live feeds from OpenStreetMap, iNaturalist, and OpenWeatherMap — not guesses.</p>
  <div class="pf-feats">

    <div class="pf-feat">
      <div class="pf-feat-ico">🛰️</div>
      <h3>Real-Time Intelligence</h3>
      <p>Weather forecasts, trail crowd levels, and biodiversity data sourced live from open APIs on every search.</p>
      <div class="pf-weather-box">
        <div class="pf-weather-temp">22°C</div>
        <div class="pf-weather-info">☀️ Clear skies<br><strong>Ideal hiking conditions</strong><br>Wind 12 km/h · Humidity 45%</div>
      </div>
    </div>

    <div class="pf-feat pf-feat-dk">
      <div class="pf-feat-ico">🏛️</div>
      <h3>Cultural Anchors</h3>
      <p>Every trail mapped to nearby historic sites, local villages, and cultural events — so you never hike in a vacuum.</p>
      <div style="margin-top:18px">
        <span class="pf-event-tag">Local Event</span>
        <p style="color:rgba(255,255,255,.8);font-size:.86rem;margin:0;line-height:1.55">
          <strong>Zagori Mountain Festival</strong><br>
          Traditional music &amp; food — every August in Monodendri village
        </p>
      </div>
    </div>

    <div class="pf-feat pf-feat-dk2">
      <div class="pf-feat-ico">🤝</div>
      <h3>Trek Together</h3>
      <p>Solo or group — our AI adapts to your party size, fitness, and shared interests for a tailored experience.</p>
      <div class="pf-quote">
        "Found a trail I'd never have discovered on my own — perfect difficulty, zero crowds."
        <div class="pf-quote-attr">— Nikos K., Athens · 3 trails planned</div>
      </div>
      <div class="pf-quote" style="margin-top:10px">
        "The sustainability score made me reconsider my route. Absolutely worth it."
        <div class="pf-quote-attr">— Marianna T., Thessaloniki</div>
      </div>
    </div>

  </div>
</div>

<div class="pf-footer">
  <div>
    <div class="pf-footer-logo">Path<span>Finder</span></div>
    <p>Deloitte Makeathon 2026 · Sustainable Tourism Initiative</p>
  </div>
  <div class="pf-footer-links">
    <a href="?nav=explore">Explore</a>
    <a href="?nav=home">About</a>
    <a href="?nav=auth">Sign Up</a>
  </div>
  <p>Data: OpenStreetMap · OpenWeatherMap · iNaturalist · NASA SRTM</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════════════════

def render_auth():
    inject_css("auth")

    st.markdown("""
<div class="pf-nav">
  <a class="pf-nav-logo" href="?nav=home">Path<span>Finder</span></a>
  <div class="pf-nav-links">
    <a href="?nav=home">Home</a>
    <a href="?nav=explore">Explore</a>
  </div>
  <div class="pf-nav-right">
    <a href="?nav=home" class="pf-btn-ghost">← Back</a>
  </div>
</div>
""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## Welcome to PathFinder")
        st.markdown("Create an account or sign in to start planning your trail.")

        if not HAS_AUTH:
            st.error("Auth module unavailable. Ensure backend/user_db.py exists.")
            return

        tab1, tab2 = st.tabs(["✨ Sign Up", "🔑 Sign In"])

        with tab1:
            with st.form("signup_form"):
                name        = st.text_input("First Name", placeholder="e.g., Maria")
                surname     = st.text_input("Last Name",  placeholder="e.g., Papadopoulou")
                age         = st.number_input("Age", min_value=1, max_value=120, step=1)
                gender      = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])
                location    = st.text_input("Location", placeholder="e.g., Athens, Greece")
                description = st.text_area("About you (optional)", max_chars=256,
                                           placeholder="e.g., I love remote mountain hikes with wildlife.")
                pw  = st.text_input("Password", type="password")
                pw2 = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if not all([name, surname, gender, location, pw, pw2]):
                        st.error("Please fill in all required fields.")
                    elif pw != pw2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            user = create_user(
                                name=name, surname=surname, age=int(age),
                                gender=gender, location=location,
                                description=description or "", password=pw,
                            )
                            st.session_state.current_user_id   = user["UserUniqieID"]
                            st.session_state.current_user_name = f"{user['Name']} {user['Surname']}"
                            st.session_state.page = "explore"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with tab2:
            users = list_users()
            if not users:
                st.info("No accounts yet. Please sign up first.")
            else:
                opts  = [f"{u['Name']} {u['Surname']} ({u['UserUniqieID']})" for u in users]
                sel   = st.selectbox("Select your account", opts)
                pw_in = st.text_input("Password", type="password", key="signin_pw")
                if st.button("Sign In", type="primary", use_container_width=True):
                    uid_sel   = sel.split("(")[1].rstrip(")")
                    auth_user = authenticate_user(uid_sel, pw_in)
                    if auth_user:
                        st.session_state.current_user_id   = uid_sel
                        st.session_state.current_user_name = f"{auth_user['Name']} {auth_user['Surname']}"
                        st.session_state.page = "explore"
                        st.rerun()
                    else:
                        st.error("❌ Invalid password. Please try again.")


# ══════════════════════════════════════════════════════════════════════════════
# EXPLORE PAGE
# ══════════════════════════════════════════════════════════════════════════════

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
            ("1 day", 1), ("2 days", 2), ("3 days", 3), ("4–7 days", 5),
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
            ("🐢 Easy-going", "low"), ("🚶 Average", "medium"), ("🏃 Fit & active", "high"),
        ],
    },
    {
        "id": "difficulty",
        "question": "How challenging do you want the trail to be?",
        "options": [
            ("Easy", "easy"), ("Moderate", "moderate"), ("Hard", "hard"),
        ],
    },
    {
        "id": "interests",
        "question": "What do you love most on a hike? Pick all that apply.",
        "type": "multi",
        "options": [
            ("🦅 Wildlife", "wildlife"), ("🏛️ History & ruins", "history"),
            ("📸 Photography", "photography"), ("🧘 Solitude", "solitude"),
            ("🏘️ Local villages", "local culture"), ("🌿 Nature & flora", "nature"),
            ("🌅 Scenic views", "views"),
        ],
    },
    {
        "id": "group_size",
        "question": "Who's coming with you?",
        "options": [
            ("Just me 🧍", 1), ("2 people", 2), ("3–5 people", 4), ("6+ people", 7),
        ],
    },
]

GREETING = (
    "👋 Hey! I'm **Pathfinder**, your AI trail companion for Greece. "
    "Let's find the perfect hike for you — I'll ask a few quick questions.\n\n"
    + STEPS[0]["question"]
)


def _pf_init():
    if "pf_messages" not in st.session_state:
        st.session_state.pf_messages = [{"role": "assistant", "content": GREETING}]
        st.session_state.pf_step    = 0
        st.session_state.pf_answers = {}
        st.session_state.pf_done    = False
        st.session_state.pf_result  = None
    for k, v in [("pf_planned_trail", None), ("pf_trail_stats", None),
                 ("pf_trail_pois", None), ("pf_trail_chat", [])]:
        if k not in st.session_state:
            st.session_state[k] = v


def _record(display: str, value, step_id: str):
    st.session_state.pf_messages.append({"role": "user", "content": display})
    st.session_state.pf_answers[step_id] = value
    nxt = st.session_state.pf_step + 1
    st.session_state.pf_step = nxt
    if nxt < len(STEPS):
        st.session_state.pf_messages.append({"role": "assistant", "content": STEPS[nxt]["question"]})
    else:
        st.session_state.pf_done = True
        st.session_state.pf_messages.append({
            "role": "assistant",
            "content": "✅ Perfect! I've got everything I need.\n\nPress **Find my trails** below to get your personalised itinerary!",
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


def render_explore():
    inject_css("explore")

    if not os.path.exists(DATA_PATH):
        with st.spinner("First launch: building trail database from OpenStreetMap… (~1 min)"):
            from scripts.fetch_trails import build
            build()
        st.success("Trail database ready!")
        st.rerun()

    uid   = st.session_state.current_user_id
    uname = st.session_state.current_user_name or ""
    first = uname.split()[0] if uname else "Explorer"

    st.markdown(f"""<div class="pf-nav" style="margin:-1rem -2rem 1.5rem">
  <a class="pf-nav-logo" href="?nav=home">Path<span>Finder</span></a>
  <div class="pf-nav-links">
    <a href="?nav=explore" class="active">Explore</a>
    <a href="?nav=home">Home</a>
  </div>
  <div class="pf-nav-right">
    <span style="color:rgba(255,255,255,.6);font-size:.84rem">Hi, {first}!</span>
  </div>
</div>""", unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown(f"**User:** {uname}")
    if st.sidebar.button("Sign Out"):
        st.session_state.current_user_id   = None
        st.session_state.current_user_name = None
        st.session_state.page = "home"
        st.rerun()

    saved = get_saved_trails(uid) if uid else []
    if saved:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📌 Your planned trails:**")
        for s in saved:
            date_str = f" · {s['planned_date']}" if s.get("planned_date") else ""
            st.sidebar.caption(f"🥾 {s['trail_name']}{date_str}")

    _pf_init()

    st.subheader("Plan your hike")
    for msg in st.session_state.pf_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.pf_done:
        step_def = STEPS[st.session_state.pf_step]
        step_id  = step_def["id"]
        kind     = step_def.get("type", "buttons")
        st.write("")

        if kind == "multi":
            selected = st.multiselect(
                "Your interests:", label_visibility="collapsed",
                options=[lbl for lbl, _ in step_def["options"]],
                key="pf_multi", placeholder="Choose one or more…",
            )
            if st.button("Confirm ✓", key="pf_multi_confirm"):
                vals    = [v for lbl, v in step_def["options"] if lbl in selected]
                display = ", ".join(selected) if selected else "No preference"
                _record(display, vals, step_id)
                st.rerun()

        elif kind == "date":
            qcols = st.columns(len(step_def["options"]))
            for i, (lbl, iso) in enumerate(step_def["options"]):
                if qcols[i].button(lbl, key=f"pf_date_quick_{i}", use_container_width=True):
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
            bcols = st.columns(len(step_def["options"]))
            for i, (lbl, val) in enumerate(step_def["options"]):
                if bcols[i].button(lbl, key=f"pf_btn_{step_id}_{i}", use_container_width=True):
                    _record(lbl, val, step_id)
                    st.rerun()

        with st.expander("✏️ Type your own answer instead"):
            with st.form(f"pf_free_{step_id}"):
                free = st.text_input("Your answer:", label_visibility="collapsed")
                if st.form_submit_button("Submit →") and free.strip():
                    _record(free.strip(), free.strip(), step_id)
                    st.rerun()

    st.write("")
    al, ar = st.columns([4, 1])

    if st.session_state.pf_done and st.session_state.pf_result is None:
        if al.button("🔍 Find my trails", type="primary", use_container_width=True):
            profile = _build_profile()
            with st.spinner("Searching trails, checking weather, scoring sustainability…"):
                try:
                    result = run_pathfinder(profile=profile, verbose=False)
                    st.session_state.pf_result = result
                    try:
                        if uid and HAS_AUTH:
                            msgs = [m["content"] for m in st.session_state.pf_messages if m["role"] == "user"]
                            create_history_entry(
                                user_uniqie_id=uid,
                                key_data={
                                    "duration_days": profile.get("duration_days"),
                                    "difficulty":    profile.get("difficulty"),
                                    "terrain":       profile.get("terrain"),
                                    "interests":     profile.get("interests"),
                                    "fitness_level": profile.get("fitness_level"),
                                    "start_date":    profile.get("start_date"),
                                    "matched_trail_count": len(result.get("enriched_trails", [])),
                                },
                                user_messages=msgs,
                                quick_select_prompts_chosen=[],
                            )
                    except Exception:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    if ar.button("🔄 Start over", use_container_width=True):
        for k in ["pf_messages", "pf_step", "pf_answers", "pf_done", "pf_result"]:
            st.session_state.pop(k, None)
        st.rerun()

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Crowd avoidance", f"{breakdown['crowd_avoidance']}/25")
                    c2.metric("Remoteness",      f"{breakdown['remoteness']}/15")
                    c3.metric("Biodiversity",    f"{breakdown['biodiversity']}/20")
                    c1.metric("Local economy",   f"{breakdown['local_economy']}/20")
                    c2.metric("Weather score",   f"{breakdown['weather']}/20")

                    ce = t.get("_crowd_economy", {})
                    if ce.get("_crowd_poi_count") is not None:
                        st.caption(
                            f"📍 {ce['_crowd_poi_count']} tourism POIs within 3 km · "
                            f"🏘️ {ce['_economy_poi_count']} local amenities within 10 km"
                        )

                    cal = t.get("_weather_calendar", [])
                    if cal:
                        st.markdown("**Weather forecast around your hike dates:**")
                        day_cols = st.columns(len(cal))
                        for ci, day in enumerate(cal):
                            with day_cols[ci]:
                                d_label = day["date"][5:]
                                st.markdown(f"**{d_label}**" + ("\n\n🎯 *your hike*" if day.get("is_planned") else ""))
                                if not day.get("available"):
                                    reason = day.get("reason", "")
                                    st.caption("📅 Beyond\n5-day\nforecast" if reason == "too_far" else ("—" if reason == "past" else "No data"))
                                else:
                                    st.markdown(day.get("emoji", "🌡️"))
                                    st.caption(f"{day.get('temp_c','?')}°C\n{day.get('conditions','')}")

                    for flag in t["_weather"].get("safety_flags", []):
                        st.warning(flag)

                    bio = t["_biodiversity"]
                    if bio.get("notable_species"):
                        st.markdown(f"🦎 **Nearby species:** {', '.join(bio['notable_species'])}")

                    route = t.get("_route", {})
                    if route.get("distance_km") is not None:
                        st.markdown(f"🥾 **Route estimate:** {route['distance_km']} km · {route['duration_h']} h (source: {route.get('source','n/a')})")

                    elev = t.get("_elevation", {})
                    if elev.get("min_m") is not None:
                        st.markdown(f"⛰️ **Elevation (SRTM):** {elev['min_m']}–{elev['max_m']} m · gain {elev['gain_m']} m")

                    st.divider()
                    already = (
                        st.session_state.pf_planned_trail is not None
                        and st.session_state.pf_planned_trail.get("name") == t.get("name")
                    )
                    if already:
                        st.success("📌 Trail planned — see details below")
                    elif st.button(f"📌 Plan this trail", key=f"plan_{t['name']}", type="primary"):
                        with st.spinner("Loading trail details & nearby attractions…"):
                            stats = get_accurate_stats(t)
                            pois  = get_nearby_pois(t["lat"], t["lon"])
                        st.session_state.pf_planned_trail = t
                        st.session_state.pf_trail_stats   = stats
                        st.session_state.pf_trail_pois    = pois
                        st.session_state.pf_trail_chat    = []
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
            trails_r = result["enriched_trails"]
            if trails_r:
                avg_lat = sum(t["lat"] for t in trails_r) / len(trails_r)
                avg_lon = sum(t["lon"] for t in trails_r) / len(trails_r)
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, tiles="OpenStreetMap")
                for i, t in enumerate(trails_r, 1):
                    score = t["_sustainability"]["score"]
                    color = "green" if score >= 60 else "orange" if score >= 40 else "red"
                    popup_html = (
                        f"<b>{t['name']}</b><br>{t['region']}<br>"
                        f"Difficulty: {t['difficulty']}<br>Duration: {t['duration_hours']}h<br>"
                        f"Route: {t.get('_route',{}).get('distance_km','?')} km<br>"
                        f"Elev gain: {t.get('_elevation',{}).get('gain_m','?')} m<br>"
                        f"Sustainability: {score}/100"
                    )
                    folium.Marker(
                        location=[t["lat"], t["lon"]],
                        popup=folium.Popup(popup_html, max_width=200),
                        tooltip=f"{i}. {t['name']}",
                        icon=folium.Icon(color=color, icon="leaf", prefix="fa"),
                    ).add_to(m)
                st_folium(m, width=600, height=500)

    if st.session_state.pf_planned_trail:
        t     = st.session_state.pf_planned_trail
        stats = st.session_state.pf_trail_stats or {}
        pois  = st.session_state.pf_trail_pois  or []

        st.markdown("---")
        st.markdown(f"## 📌 Your Planned Trail: **{t['name']}**")
        st.caption(f"{t.get('region','')}  ·  Sustainability {t['_sustainability']['score']}/100  {t['_sustainability']['label']}")

        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        sc1.metric("Distance",   f"{stats.get('distance_km','?')} km", help=f"Source: {stats.get('source','?')}")
        sc2.metric("Est. time",  f"{stats.get('duration_h','?')} h",   help="Naismith's Rule: 4 km/h + 1 h per 600 m ascent")
        sc3.metric("Difficulty", stats.get("difficulty","?").capitalize())
        sc4.metric("Ascent",     f"{stats.get('ascent_m','?')} m")
        sc5.metric("Terrain",    t.get("terrain","?").capitalize())

        if stats.get("source") == "estimated":
            st.caption("⚠️ Distance estimated — OSM tags unavailable for this trail.")
        elif stats.get("source") == "osm_tags":
            st.caption("✅ Distance from official OSM trail tags.")

        dl, dr = st.columns(2)

        with dl:
            if t.get("highlights"):
                st.markdown("**Highlights:** " + " · ".join(t["highlights"]))

            w = t.get("_weather", {})
            if w.get("temp_c") is not None:
                st.markdown(f"🌤 **Weather on your date:** {w['temp_c']}°C, {w['conditions']} · 💨 {w['wind_kmh']} km/h")
            for flag in w.get("safety_flags", []):
                st.warning(flag)

            bio = t.get("_biodiversity", {})
            if bio.get("notable_species"):
                st.markdown(f"🦎 **Nearby wildlife:** {', '.join(bio['notable_species'])}")

            st.markdown("---")
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
                        trail=t, stats=stats, pois=pois,
                        history=st.session_state.pf_trail_chat[:-1],
                        user_message=user_q,
                    )
                st.session_state.pf_trail_chat.append({"role": "assistant", "content": reply})
                st.rerun()

            if st.session_state.pf_trail_chat:
                if st.button("Clear chat", key="clear_trail_chat"):
                    st.session_state.pf_trail_chat = []
                    st.rerun()

        with dr:
            st.markdown("#### 🗺️ Trail & Nearby Attractions")
            m2 = folium.Map(location=[t["lat"], t["lon"]], zoom_start=12, tiles="OpenStreetMap")
            folium.Marker(
                location=[t["lat"], t["lon"]],
                tooltip=t["name"],
                popup=folium.Popup(f"<b>{t['name']}</b><br>{t.get('region','')}", max_width=200),
                icon=folium.Icon(color="darkgreen", icon="flag", prefix="fa"),
            ).add_to(m2)

            COLOR_MAP = {
                "blue": "blue", "gray": "gray", "purple": "purple", "green": "green",
                "red": "red", "lightblue": "lightblue", "white": "white", "beige": "beige",
            }
            for poi in pois:
                folium.Marker(
                    location=[poi["lat"], poi["lon"]],
                    tooltip=f"{poi['emoji']} {poi['name']}",
                    popup=folium.Popup(f"<b>{poi['name']}</b><br>{poi['category']}", max_width=160),
                    icon=folium.Icon(color=COLOR_MAP.get(poi["color"], "beige"), icon="circle", prefix="fa"),
                ).add_to(m2)

            st_folium(m2, width=560, height=460, key="detail_map")

            if pois:
                st.markdown("**Nearby attractions:**")
                by_cat = {}
                for p in pois:
                    by_cat.setdefault(p["category"], []).append(p)
                for cat, items in by_cat.items():
                    emoji = items[0]["emoji"]
                    names = ", ".join(p["name"] for p in items[:4] if p["name"] != cat) or f"{len(items)} locations"
                    st.caption(f"{emoji} **{cat}** ({len(items)}): {names}")

        if st.button("✕ Remove from plan", key="unplan_trail"):
            if uid:
                remove_saved_trail(uid, t.get("name"))
            st.session_state.pf_planned_trail = None
            st.session_state.pf_trail_stats   = None
            st.session_state.pf_trail_pois    = None
            st.session_state.pf_trail_chat    = []
            st.rerun()

    st.markdown(
        "<hr><p style='text-align:center;color:#aaa;font-size:.8rem'>"
        "Pathfinder · Deloitte Makeathon 2026 · Data: OpenStreetMap, "
        "OpenWeatherMap, iNaturalist, NASA SRTM</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

_page = st.session_state.page
if _page == "home":
    render_home()
elif _page == "auth":
    render_auth()
else:
    render_explore()
