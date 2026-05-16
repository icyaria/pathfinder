"""
trail_details.py
Accurate trail stats and nearby POI discovery for the trail detail page.

Stats: re-fetches OSM tags by osm_id to get official distance & ascent,
       then applies Naismith's Rule (4 km/h + 1h per 600m ascent).

POIs: Overpass query within 8 km for viewpoints, historic sites, peaks,
      food, water sources and parking.
"""

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "Pathfinder/1.0 (Deloitte Makeathon 2026)"}

POI_TYPES = [
    # (category, color, emoji, overpass_filter)
    ("Viewpoint",    "blue",      "🔭", '["tourism"="viewpoint"]'),
    ("Peak",         "gray",      "⛰️", '["natural"="peak"]'),
    ("Historic",     "purple",    "🏛️", '["historic"]'),
    ("Attraction",   "green",     "🎯", '["tourism"~"attraction|museum"]'),
    ("Food & drink", "red",       "🍽️", '["amenity"~"restaurant|cafe|bar|taverna"]'),
    ("Water",        "lightblue", "💧", '["amenity"="drinking_water"]'),
    ("Parking",      "white",     "🅿️", '["amenity"="parking"]'),
]


def _parse_distance(val: str):
    """Parse OSM distance tag (e.g. '12', '12km', '12000m') → km float."""
    if not val:
        return None
    try:
        s = str(val).lower().replace(" ", "")
        if s.endswith("km"):
            return float(s[:-2])
        if s.endswith("m"):
            v = float(s[:-1])
            return v / 1000 if v > 500 else v
        v = float(s)
        return v / 1000 if v > 500 else v
    except ValueError:
        return None


def _parse_meters(val: str):
    """Parse an elevation tag (e.g. '450', '450m') → int."""
    if not val:
        return None
    try:
        return int(float(str(val).lower().replace("m", "").strip()))
    except ValueError:
        return None


def get_osm_trail_tags(osm_id: int, osm_source: str = "relation") -> dict:
    """
    Fetch raw OSM tags for a trail by its OSM id.
    Returns a dict of tag key→value (empty dict on failure).
    """
    entity = "relation" if osm_source == "relation" else "way"
    query  = f"[out:json][timeout:12];\n{entity}({osm_id});\nout tags;"
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=15)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        if elements:
            return elements[0].get("tags", {})
    except Exception:
        pass
    return {}


def compute_stats(distance_km: float, ascent_m: int) -> dict:
    """
    Naismith's Rule: 4 km/h base pace + 1 h per 600 m ascent.
    Difficulty derived from weighted effort score.
    """
    duration_h = round(distance_km / 4.0 + (ascent_m or 0) / 600, 1)

    effort = distance_km + (ascent_m or 0) / 100
    if effort < 10:
        difficulty = "easy"
    elif effort < 25:
        difficulty = "moderate"
    else:
        difficulty = "hard"

    return {
        "distance_km": round(distance_km, 1),
        "duration_h":  duration_h,
        "ascent_m":    ascent_m,
        "difficulty":  difficulty,
        "method":      "naismith",
    }


def get_accurate_stats(trail: dict) -> dict:
    """
    Priority:
      1. OSM tags re-fetched by osm_id  (distance=, ascent=, sac_scale)
      2. _route.distance_km + _elevation.gain_m already in trail dict
      3. Original trail fields (least accurate)

    Returns a stats dict with distance_km, duration_h, ascent_m, difficulty, source.
    """
    osm_id     = trail.get("osm_id")
    osm_source = trail.get("osm_source", "relation")

    distance_km = ascent_m = sac = None
    source = "fallback"

    # ── 1. OSM tags ──────────────────────────────────────────────────────────
    if osm_id:
        tags = get_osm_trail_tags(int(osm_id), osm_source)
        distance_km = _parse_distance(tags.get("distance") or tags.get("length"))
        ascent_m    = _parse_meters(tags.get("ascent") or tags.get("ele:gain"))
        sac         = tags.get("sac_scale")
        if distance_km:
            source = "osm_tags"

    # ── 2. Already-enriched route / elevation ─────────────────────────────────
    if not distance_km:
        route = trail.get("_route", {})
        if route.get("distance_km"):
            distance_km = route["distance_km"]
            source      = route.get("source", "route_estimate")
    if not ascent_m:
        elev = trail.get("_elevation", {})
        if elev.get("gain_m"):
            ascent_m = int(elev["gain_m"])

    # ── 3. Hard fallback ──────────────────────────────────────────────────────
    if not distance_km:
        distance_km = trail.get("duration_hours", 4.0) * 4.0  # reverse old estimate
        source      = "estimated"

    stats = compute_stats(distance_km, ascent_m or 0)

    # Override difficulty from SAC scale if available (it's authoritative)
    if sac:
        from backend.sustainability import _label  # avoid circular; just map string
        sac_map = {
            "hiking":                "easy",
            "mountain_hiking":       "moderate",
            "demanding_mountain_hiking": "hard",
            "alpine_hiking":         "hard",
            "demanding_alpine_hiking": "hard",
            "difficult_alpine_hiking": "hard",
        }
        stats["difficulty"] = sac_map.get(sac, stats["difficulty"])
        stats["sac_scale"]  = sac

    stats["source"] = source
    return stats


def get_nearby_pois(lat: float, lon: float, radius_m: int = 8000) -> list:
    """
    Returns a list of POI dicts: {name, lat, lon, category, emoji, color}
    """
    filters = "\n  ".join(
        f'node{f}(around:{radius_m},{lat},{lon});'
        for _, _, _, f in POI_TYPES
    )
    query = f"[out:json][timeout:20];\n(\n  {filters}\n);\nout body;"

    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=25)
        r.raise_for_status()
        elements = r.json().get("elements", [])
    except Exception:
        return []

    pois = []
    seen = set()
    for el in elements:
        tags     = el.get("tags", {})
        name     = (tags.get("name:en") or tags.get("name") or "").strip()
        node_lat = el.get("lat")
        node_lon = el.get("lon")
        if not node_lat or not node_lon:
            continue

        # Classify by first matching POI type
        cat, color, emoji = "Other", "beige", "📍"
        for category, col, emj, filt in POI_TYPES:
            key = filt.strip('[]"').split('"')[0].strip("~=")
            val_pattern = filt.split('"')[-2] if '"' in filt else ""
            if tags.get(key) and (not val_pattern or val_pattern in tags.get(key, "")):
                cat, color, emoji = category, col, emj
                break

        key = f"{node_lat:.4f},{node_lon:.4f}"
        if key in seen:
            continue
        seen.add(key)

        pois.append({
            "name":     name or cat,
            "lat":      node_lat,
            "lon":      node_lon,
            "category": cat,
            "emoji":    emoji,
            "color":    color,
        })

    return pois[:60]  # cap to avoid overwhelming the map
