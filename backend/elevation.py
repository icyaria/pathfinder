"""
elevation.py
Elevation profile helpers using NASA SRTM data via OpenTopodata.
"""

import math
import requests

SRTM_URL = "https://api.opentopodata.org/v1/nasa_srtm90m"


def _sample_points(lat: float, lon: float, radius_deg: float = 0.02, samples: int = 8) -> list:
    points = []
    for i in range(samples):
        angle = (2 * math.pi * i) / samples
        dlat = radius_deg * math.sin(angle)
        dlon = radius_deg * math.cos(angle)
        points.append((lat + dlat, lon + dlon))
    points.insert(0, (lat, lon))
    return points


def get_elevation_profile(lat: float, lon: float) -> dict:
    """
    Returns elevation summary around a trail point:
      - min_m, max_m, gain_m, sample_count
    """
    try:
        points = _sample_points(lat, lon)
        locations = "|".join(f"{p[0]:.6f},{p[1]:.6f}" for p in points)
        resp = requests.get(SRTM_URL, params={"locations": locations}, timeout=10)
        resp.raise_for_status()

        values = [r.get("elevation") for r in resp.json().get("results", [])]
        elevations = [v for v in values if isinstance(v, (int, float))]
        if not elevations:
            raise ValueError("No elevation values returned")

        gain = 0
        for prev, curr in zip(elevations, elevations[1:]):
            gain += max(0, curr - prev)

        return {
            "min_m": round(min(elevations), 1),
            "max_m": round(max(elevations), 1),
            "gain_m": round(gain, 1),
            "sample_count": len(elevations),
            "source": "nasa_srtm90m",
        }
    except Exception as e:
        return {
            "min_m": None,
            "max_m": None,
            "gain_m": None,
            "sample_count": 0,
            "source": "nasa_srtm90m",
            "_error": str(e),
        }
