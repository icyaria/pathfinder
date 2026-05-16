"""
crowd_economy.py
Real crowd level and local economy data from OpenStreetMap via Overpass API.

Crowd level (1–5, 1=very quiet, 5=packed):
  Counts tourism-tagged POIs within 3 km.
  More tourism infrastructure → more visited area → higher crowd level.

Local economy score (0–10):
  Counts economic amenities (restaurants, shops, accommodation) within 10 km.
  More local businesses visitors can spend at → higher score.
"""

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "Pathfinder/1.0 (Deloitte Makeathon 2026)"}


def _count(query: str) -> int:
    """Run an Overpass `out count` query and return the total. Returns -1 on failure."""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=12)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        if elements and elements[0].get("type") == "count":
            return int(elements[0]["tags"].get("total", 0))
        return 0
    except Exception:
        return -1


def get_crowd_and_economy(lat: float, lon: float) -> dict:
    """
    Returns:
        crowd_level           int 1–5   (1=very quiet, 5=packed)
        local_economy_score   int 0–10
        _crowd_poi_count      raw OSM tourism POI count within 3 km
        _economy_poi_count    raw OSM amenity count within 10 km
    """
    crowd_n = _count(f"""
[out:json][timeout:12];
(
  node["tourism"](around:3000,{lat},{lon});
  way["tourism"](around:3000,{lat},{lon});
);
out count;
""")

    economy_n = _count(f"""
[out:json][timeout:12];
(
  node["amenity"~"restaurant|cafe|bar|pub|fast_food|bakery|supermarket|convenience|marketplace"](around:10000,{lat},{lon});
  node["tourism"~"hotel|hostel|guest_house|motel|camp_site|apartment"](around:10000,{lat},{lon});
  node["shop"](around:10000,{lat},{lon});
);
out count;
""")

    # crowd_level: 1=very quiet … 5=packed
    if crowd_n < 0:       crowd_level = 2        # Overpass failed — mild default
    elif crowd_n == 0:    crowd_level = 1
    elif crowd_n <= 5:    crowd_level = 2
    elif crowd_n <= 20:   crowd_level = 3
    elif crowd_n <= 60:   crowd_level = 4
    else:                 crowd_level = 5

    # local_economy_score: 0–10
    if economy_n < 0:      economy_score = 5     # Overpass failed — neutral default
    elif economy_n == 0:   economy_score = 0
    elif economy_n <= 10:  economy_score = 2
    elif economy_n <= 30:  economy_score = 4
    elif economy_n <= 80:  economy_score = 6
    elif economy_n <= 200: economy_score = 8
    else:                  economy_score = 10

    return {
        "crowd_level":         crowd_level,
        "local_economy_score": economy_score,
        "_crowd_poi_count":    max(0, crowd_n),
        "_economy_poi_count":  max(0, economy_n),
    }
