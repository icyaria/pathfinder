"""
sustainability.py
Scores each trail 0–100 across four real signals:
  - Crowd avoidance  (from crowd_level field)
  - Remoteness       (Haversine distance to nearest major Greek city)
  - Biodiversity     (iNaturalist observation count)
  - Local economy    (manually/LLM-set field per trail)
"""

import math

# Regions that are already severely overtouristed — lose region bonus
OVERTOURIST_REGIONS = {
    "Santorini", "Mykonos", "Athens", "Rhodes Town",
    "Zakynthos", "Corfu Town", "Heraklion",
}

# Approximate lat/lon of Greece's 5 biggest cities
MAJOR_CITIES = [
    (37.9838, 23.7275),   # Athens
    (40.6401, 22.9444),   # Thessaloniki
    (35.3387, 25.1442),   # Heraklion
    (38.2466, 21.7346),   # Patras
    (39.6650, 20.8537),   # Ioannina
]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sustainability_score(trail: dict, bio_count: int = 0) -> dict:
    """
    Returns {"score": int, "breakdown": dict, "label": str}

    Breakdown components (each contributes up to a max):
        crowd_avoidance  : 0–30 pts
        remoteness       : 0–20 pts
        biodiversity     : 0–20 pts
        local_economy    : 0–20 pts
        region_bonus     : 0–10 pts
    """
    breakdown = {}

    # 1. Crowd avoidance — crowd_level 1 (empty) to 5 (packed)
    crowd = trail.get("crowd_level", 3)
    breakdown["crowd_avoidance"] = round((5 - crowd) / 4 * 30)

    # 2. Remoteness — distance to nearest major city (up to ~300 km → 20 pts)
    min_dist = min(
        _haversine_km(trail["lat"], trail["lon"], clat, clon)
        for clat, clon in MAJOR_CITIES
    )
    breakdown["remoteness"] = min(20, round(min_dist / 15))

    # 3. Biodiversity from iNaturalist
    if bio_count >= 50:
        breakdown["biodiversity"] = 20
    elif bio_count >= 20:
        breakdown["biodiversity"] = 14
    elif bio_count >= 5:
        breakdown["biodiversity"] = 8
    else:
        breakdown["biodiversity"] = 3

    # 4. Local economy (0–10 in trails.json → scaled to 0–20)
    economy_raw = trail.get("local_economy_score", 5)
    breakdown["local_economy"] = round(economy_raw * 2)

    # 5. Region bonus — not in overtourist list
    breakdown["region_bonus"] = (
        0 if trail.get("region") in OVERTOURIST_REGIONS else 10
    )

    total = min(100, sum(breakdown.values()))
    return {
        "score": total,
        "breakdown": breakdown,
        "label": _label(total),
    }


def _label(score: int) -> str:
    if score >= 80:
        return "🌿 Excellent"
    if score >= 60:
        return "✅ Good"
    if score >= 40:
        return "⚠️ Moderate"
    return "🔴 Poor"
