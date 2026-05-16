"""
pipeline.py — Pathfinder main pipeline

Chains all backend modules in order:
  1. profiler       → extract structured profile from user text
  2. trail_engine   → filter + rank trails
  3. weather        → real-time conditions + safety flags
  4. biodiversity   → iNaturalist species count
  5. sustainability → composite 0-100 score
  6. itinerary      → LLM-generated day-by-day plan

Usage (CLI):
  python pipeline.py

Usage (import):
  from pipeline import run_pathfinder
  result = run_pathfinder("3-day hard mountain hike, I love wildlife")
"""

import time
from backend.profiler       import extract_profile
from backend.trail_engine   import load_trails, match_trails
from backend.weather        import get_weather
from backend.biodiversity   import get_biodiversity
from backend.routing        import get_route_summary
from backend.elevation      import get_elevation_profile
from backend.sustainability import sustainability_score
from backend.itinerary      import generate_itinerary


def run_pathfinder(user_input: str, verbose: bool = True) -> dict:
    """
    Full pipeline. Returns:
        profile         — extracted preferences
        matched_trails  — filtered trail list
        enriched_trails — trails with weather + bio + sustainability attached
        itinerary       — final markdown-formatted plan (string)
    """

    def log(msg):
        if verbose:
            print(f"  {msg}")

    print("\n🧭 Pathfinder starting…\n")

    # ── 1. Profile ─────────────────────────────────────────────────────────
    log("1/5  Extracting traveller profile…")
    profile = extract_profile(user_input)
    log(
        f"     → {profile['duration_days']}d | {profile['difficulty']} | "
        f"{profile['terrain']} | interests: {profile['interests']}"
    )

    # ── 2. Trail matching ──────────────────────────────────────────────────
    log("2/5  Loading and filtering trails…")
    trails  = load_trails()
    matched = match_trails(profile, trails)
    log(f"     → {len(matched)} trails matched from {len(trails)} total")

    if not matched:
        return {
            "profile": profile,
            "matched_trails": [],
            "enriched_trails": [],
            "itinerary": (
                "No trails matched your preferences. "
                "Try broadening difficulty or terrain settings."
            ),
        }

    # ── 3–6. Enrich each matched trail ────────────────────────────────────
    log("3/6  Fetching weather, biodiversity, route & elevation…")
    enriched = []
    for i, trail in enumerate(matched, 1):
        log(f"     [{i}/{len(matched)}] {trail['name']}…")

        weather = get_weather(trail["lat"], trail["lon"])
        time.sleep(0.2)

        bio  = get_biodiversity(trail["lat"], trail["lon"])
        time.sleep(0.2)

        route = get_route_summary(trail["lat"], trail["lon"])
        time.sleep(0.2)

        elevation = get_elevation_profile(trail["lat"], trail["lon"])
        time.sleep(0.2)

        sust = sustainability_score(trail, bio_count=bio["total_observations"])

        enriched.append(
            {
                **trail,
                "_weather": weather,
                "_biodiversity": bio,
                "_route": route,
                "_elevation": elevation,
                "_sustainability": sust,
            }
        )

    # ── 6. Itinerary ───────────────────────────────────────────────────────
    log("5/6  Generating itinerary with LLM…")
    itinerary = generate_itinerary(profile, enriched)

    log("6/6  Done ✓\n")

    return {
        "profile":         profile,
        "matched_trails":  matched,
        "enriched_trails": enriched,
        "itinerary":       itinerary,
    }


# ── CLI demo ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os, json

    query = (
        input("Describe your ideal hike in Greece:\n> ")
        if os.isatty(0)
        else "I want a hard 3-day mountain hike away from tourists, I love wildlife"
    )

    result = run_pathfinder(query)

    print("\n" + "─" * 60)
    print("PROFILE")
    print("─" * 60)
    print(json.dumps(result["profile"], indent=2))

    print("\n" + "─" * 60)
    print("SUSTAINABILITY SCORES")
    print("─" * 60)
    for t in result["enriched_trails"]:
        s = t["_sustainability"]
        print(f"  {t['name']:42s}  {s['score']:3d}/100  {s['label']}")

    print("\n" + "─" * 60)
    print("ITINERARY")
    print("─" * 60)
    print(result["itinerary"])
