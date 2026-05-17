"""
sustainability.py
Scores each trail 0–100 across five components.

  Component         Max    Source
  ────────────────────────────────────────────────────────────────
  Crowd avoidance    25    OSM tourism POI count within 3 km      [REAL]
  Remoteness         15    Haversine km to nearest major city      [REAL]
  Biodiversity       20    iNaturalist research-grade obs count    [REAL]
  Local economy      20    OSM amenity count within 10 km         [REAL]
  Weather            20    OpenWeatherMap current / 5-day forecast [REAL]
  ────────────────────────────────────────────────────────────────
  Total             100
"""

import math

MAJOR_CITIES = [
    (37.9838, 23.7275),  # Athens
    (40.6401, 22.9444),  # Thessaloniki
    (35.3387, 25.1442),  # Heraklion
    (38.2466, 21.7346),  # Patras
    (39.6650, 20.8537),  # Ioannina
]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _weather_score(weather: dict, profile: dict) -> int:
    """
    0–20 pts based on conditions and temperature, weighted by user preferences.

    Default ideal: 15–25 °C, clear or partly cloudy.
    Adjusts when interests or planned month suggest cold / winter hiking.
    """
    if not weather or weather.get("_skipped") or weather.get("_error"):
        return 10  # neutral when data is unavailable

    temp      = weather.get("temp_c")
    main      = weather.get("weather_main") or ""
    interests = [i.lower() for i in (profile or {}).get("interests", [])]

    # Infer preference from planned month
    start_date  = (profile or {}).get("start_date", "")
    winter_hike = False
    if start_date:
        try:
            winter_hike = int(start_date[5:7]) in (11, 12, 1, 2, 3)
        except (ValueError, IndexError):
            pass

    wants_cold = winter_hike or any(w in interests for w in ["snow", "winter", "cold", "skiing"])
    wants_warm = any(w in interests for w in ["sun", "beach", "hot", "summer", "swimming"])

    # ── Temperature score 0–10 ────────────────────────────────────────────────
    if temp is None:
        temp_pts = 5
    elif wants_cold:
        if temp <= 0:         temp_pts = 10
        elif temp <= 5:       temp_pts = 9
        elif temp <= 10:      temp_pts = 7
        elif temp <= 15:      temp_pts = 5
        else:                 temp_pts = 2
    elif wants_warm:
        if 22 <= temp <= 30:  temp_pts = 10
        elif 18 <= temp < 22: temp_pts = 8
        elif 15 <= temp < 18: temp_pts = 6
        elif 30 < temp <= 35: temp_pts = 6
        elif temp > 35:       temp_pts = 3
        else:                 temp_pts = 3
    else:
        if 15 <= temp <= 25:  temp_pts = 10
        elif 25 < temp <= 30: temp_pts = 7
        elif 10 <= temp < 15: temp_pts = 7
        elif 30 < temp <= 35: temp_pts = 4
        elif 5 <= temp < 10:  temp_pts = 4
        else:                 temp_pts = 1

    # ── Conditions score 0–10 ─────────────────────────────────────────────────
    BASE_COND = {
        "Clear": 10, "Clouds": 8, "Haze": 7, "Mist": 6,
        "Drizzle": 4, "Rain": 2, "Snow": 2, "Fog": 4,
        "Dust": 2, "Sand": 2, "Smoke": 1, "Squall": 1,
        "Thunderstorm": 0, "Tornado": 0,
    }
    cond_pts = BASE_COND.get(main, 7)

    if wants_cold and main == "Snow":   cond_pts = 10  # perfect for winter hikers
    if wants_cold and main == "Clear":  cond_pts = 7
    if main == "Thunderstorm":          cond_pts = 0   # always dangerous

    return max(0, min(20, temp_pts + cond_pts))


def sustainability_score(trail: dict, bio_count: int = 0,
                         weather: dict = None, profile: dict = None,
                         crowd_level: int = None,
                         local_economy_score: int = None,
                         live_interest_count: int = 0) -> dict:
    """
    Returns {"score": int 0–100, "breakdown": dict, "label": str}

    crowd_level and local_economy_score come from crowd_economy.py (real OSM data).
    live_interest_count comes from live_interest.py (collaborative rerouting pressure).
    """
    profile = profile or {}
    breakdown = {}

    # 1. Crowd avoidance (0–25) — lower crowd = better.
    # live_interest_count adds rerouting pressure: every 3 users → +1 crowd level (max +3).
    crowd = crowd_level if crowd_level is not None else trail.get("crowd_level", 3)
    live_bump = min(3, live_interest_count // 3)
    effective_crowd = min(5, crowd + live_bump)
    breakdown["crowd_avoidance"] = round((5 - effective_crowd) / 4 * 25)
    breakdown["_live_interest"]  = live_interest_count

    # 2. Remoteness (0–15)
    # Divisor of 10 means 150 km from nearest city = full 15 pts,
    # which is achievable for remote mainland areas and islands.
    min_dist = min(
        _haversine_km(trail["lat"], trail["lon"], clat, clon)
        for clat, clon in MAJOR_CITIES
    )
    breakdown["remoteness"] = min(15, round(min_dist / 10))

    # 3. Biodiversity (0–20)
    if bio_count >= 50:   breakdown["biodiversity"] = 20
    elif bio_count >= 20: breakdown["biodiversity"] = 14
    elif bio_count >= 5:  breakdown["biodiversity"] = 8
    else:                 breakdown["biodiversity"] = 2

    # 4. Local economy (0–20) — real OSM amenity count scaled 0–10 → 0–20
    economy_raw = local_economy_score if local_economy_score is not None else trail.get("local_economy_score", 5)
    breakdown["local_economy"] = round(economy_raw / 10 * 20)

    # 5. Weather (0–20)
    breakdown["weather"] = _weather_score(weather or {}, profile)

    total = min(100, sum(breakdown.values()))
    return {
        "score":     total,
        "breakdown": breakdown,
        "label":     _label(total),
    }


def _label(score: int) -> str:
    if score >= 80: return "🌿 Excellent"
    if score >= 60: return "✅ Good"
    if score >= 40: return "⚠️ Moderate"
    return "🔴 Poor"
