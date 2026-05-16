"""
biodiversity.py
Queries iNaturalist for research-grade species observations near a trail.
"""

import requests


def get_biodiversity(lat: float, lon: float, radius_km: int = 5) -> dict:
    """
    Returns total observation count and up to 5 notable species names
    found within radius_km of the trail coordinates.
    """
    try:
        url = (
            f"https://api.inaturalist.org/v1/observations"
            f"?lat={lat}&lng={lon}&radius={radius_km}"
            f"&quality_grade=research&per_page=10&order_by=votes"
        )
        data = requests.get(url, timeout=7).json()
        total = data.get("total_results", 0)

        species = []
        for obs in data.get("results", []):
            name = (
                obs.get("taxon", {}).get("preferred_common_name")
                or obs.get("taxon", {}).get("name")
            )
            if name and name not in species:
                species.append(name)

        return {
            "total_observations": total,
            "notable_species": species[:5],
        }
    except Exception as e:
        return {
            "total_observations": 0,
            "notable_species": [],
            "_error": str(e),
        }
