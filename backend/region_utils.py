"""
region_utils.py
Classifies a trail's Greek administrative region from its lat/lon coordinates.

OSM trails rarely carry region tags, so we derive the region geometrically.
The 13 modern Greek administrative regions are identified by bounding boxes
checked in priority order (islands first, then mainland from south to north).
"""


def region_from_coords(lat: float, lon: float) -> str:
    """Return a region_id string matching the RegionFilter.jsx GREEK_REGIONS list."""

    # ── Islands ──────────────────────────────────────────────────────────────

    # Crete — southernmost, clearly bounded
    if lat < 36.0 and 23.0 <= lon <= 27.5:
        return "crete"

    # Southern Aegean — Cyclades + Dodecanese (east side, lat up to ~38.5)
    if lat < 38.5 and lon >= 25.0:
        return "s-aegean"

    # Northern Aegean — Lesvos, Chios, Samos, Thasos, Limnos
    if 37.5 <= lat <= 41.5 and lon >= 25.0:
        return "n-aegean"

    # Ionian Islands — low longitude, west of the mainland
    if lon < 21.0 and 37.3 <= lat <= 40.2:
        return "ionian"

    # ── Mainland south → north ───────────────────────────────────────────────

    # Attica (greater Athens area — small)
    if 37.6 <= lat <= 38.4 and 23.0 <= lon <= 24.5:
        return "attica"

    # Peloponnese
    if 36.2 <= lat <= 38.3 and 21.3 <= lon <= 23.5:
        return "peloponne"

    # Western Greece (Aitoloakarnania, coastal Achaia, Ilia)
    if 37.5 <= lat <= 39.5 and 20.8 <= lon <= 22.5:
        return "w-greece"

    # Central Greece / Sterea Ellada (incl. Evia) — check before Thessaly
    if 38.0 <= lat <= 39.5 and 21.5 <= lon <= 24.5:
        return "c-greece"

    # Thessaly
    if 39.0 <= lat <= 40.4 and 21.5 <= lon <= 23.8:
        return "thessaly"

    # Epirus (NW mainland — check lon < 21.5)
    if 38.8 <= lat <= 41.2 and 20.0 <= lon <= 21.5:
        return "epirus"

    # Western Macedonia (Kozani, Florina, Kastoria)
    if 39.8 <= lat <= 41.5 and 20.5 <= lon <= 22.5:
        return "w-mac"

    # Eastern Macedonia & Thrace — check before c-mac (higher lon)
    if 40.5 <= lat <= 42.5 and 24.0 <= lon <= 27.5:
        return "e-mac"

    # Central Macedonia (Thessaloniki + surroundings) — widest northern box
    if 39.8 <= lat <= 42.5 and 22.0 <= lon <= 25.5:
        return "c-mac"

    # ── Fallback: nearest cardinal guess ─────────────────────────────────────
    if lat > 40.0:
        return "c-mac"
    if lat < 37.5:
        return "peloponne"
    return "c-greece"


def trail_region_id(trail: dict) -> str:
    return region_from_coords(trail.get("lat", 0), trail.get("lon", 0))


def filter_by_region(trails: list, region_id: str) -> list:
    if not region_id:
        return trails
    return [t for t in trails if trail_region_id(t) == region_id]
