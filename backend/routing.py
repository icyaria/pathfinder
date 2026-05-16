"""
routing.py
Route generation helpers using OpenRouteService (free tier).
"""

import os
import math
import requests
from dotenv import load_dotenv

load_dotenv()

ORS_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")
ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-hiking"


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _fallback_route(lat: float, lon: float) -> dict:
    # Estimate a practical short route when ORS key is unavailable.
    end_lat = lat + 0.015
    end_lon = lon + 0.01
    dist = _haversine_km(lat, lon, end_lat, end_lon) * 1.25
    return {
        "distance_km": round(dist, 2),
        "duration_h": round(dist / 4.0, 2),
        "source": "fallback",
        "segment": [[lon, lat], [end_lon, end_lat]],
    }


def _route_between(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    payload = {
        "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
        "instructions": False,
    }
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(ORS_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    route = resp.json()["routes"][0]["summary"]
    dist_km = route["distance"] / 1000
    dur_h = route["duration"] / 3600
    return {
        "distance_km": round(dist_km, 2),
        "duration_h": round(dur_h, 2),
        "source": "openrouteservice",
        "segment": [[start_lon, start_lat], [end_lon, end_lat]],
    }


def get_route_summary(lat: float, lon: float) -> dict:
    """
    Returns a route estimate around the trail point.
    Uses OpenRouteService if API key is configured, otherwise fallback math estimate.
    """
    if not ORS_API_KEY:
        return _fallback_route(lat, lon)

    offsets = [
        (0.015, 0.01),
        (0.01, -0.015),
        (-0.015, -0.01),
        (-0.01, 0.015),
    ]
    for dlat, dlon in offsets:
        try:
            return _route_between(lat, lon, lat + dlat, lon + dlon)
        except Exception:
            continue

    return _fallback_route(lat, lon)
