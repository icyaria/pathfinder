"""
scripts/fetch_trails.py
Fetches real Greek hiking trails from OpenStreetMap (Overpass API),
then enriches them with Claude, and saves to data/trails.json.

Run once before starting the app:
  python scripts/fetch_trails.py
"""

import os
import sys
import json
import time
import requests
import boto3
from dotenv import load_dotenv

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "trails.json")

MODEL = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# Greece bounding box
GREECE_BBOX = "34.8, 19.3, 41.8, 29.6"

# ── Overpass queries ────────────────────────────────────────────────────────

RELATION_QUERY = f"""
[out:json][timeout:60];
(
  relation["route"="hiking"]["name"]({GREECE_BBOX});
  relation["route"="foot"]["name"]({GREECE_BBOX});
);
out center tags;
"""

WAY_QUERY = f"""
[out:json][timeout:60];
(
  way["highway"~"path|footway|track"]["name"]["foot"!="no"]({GREECE_BBOX});
);
out center tags;
"""


def fetch(query: str, label: str) -> list:
    print(f"  Querying Overpass for {label}…")
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        print(f"  → {len(elements)} {label} found")
        return elements
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return []


# ── Parsers ─────────────────────────────────────────────────────────────────

def osm_dist_to_hours(s):
    if not s:
        return None
    try:
        v = float(s.lower().replace("km", "").replace("m", "").replace(" ", ""))
        if v > 500:
            v /= 1000
        return round(v / 3.0, 1)
    except ValueError:
        return None

def sac_to_difficulty(sac):
    return {"hiking": "easy", "mountain_hiking": "moderate"}.get(
        sac or "", "hard" if "demanding" in (sac or "") else "moderate"
    )

def infer_terrain(tags):
    text = (tags.get("name", "") + " " + tags.get("description", "")).lower()
    if any(w in text for w in ["coast", "beach", "sea", "παραλ"]):
        return "coastal"
    if any(w in text for w in ["forest", "δάσ", "wood"]):
        return "forest"
    return "mountain"

def infer_crowd(tags):
    name = tags.get("name", "").lower()
    if any(f in name for f in ["samaria", "olympus", "meteora", "rhodes", "santorini"]):
        return 4
    if tags.get("wikidata") or tags.get("tourism"):
        return 3
    if tags.get("network") in ("iwn", "nwn"):
        return 3
    return 2

def parse_elements(elements, source):
    trails, seen = [], set()
    for el in elements:
        tags   = el.get("tags", {})
        name   = tags.get("name") or tags.get("name:en")
        center = el.get("center", {})
        lat, lon = center.get("lat"), center.get("lon")
        if not name or not lat or not lon or name in seen:
            continue
        seen.add(name)
        trails.append({
            "name":                name,
            "region":              tags.get("region") or tags.get("addr:state") or "Greece",
            "terrain":             infer_terrain(tags),
            "difficulty":          sac_to_difficulty(tags.get("sac_scale")),
            "duration_hours":      osm_dist_to_hours(tags.get("distance") or tags.get("length")) or 4.0,
            "lat":                 lat,
            "lon":                 lon,
            "crowd_level":         infer_crowd(tags),
            "local_economy_score": 5,
            "highlights":          [],
            "osm_id":              el.get("id"),
            "osm_source":          source,
            "_desc":               (tags.get("description") or "")[:300],
        })
    return trails


# ── LLM enrichment ──────────────────────────────────────────────────────────

def enrich(trails, batch_size=10):
    enriched = []
    batches  = [trails[i:i+batch_size] for i in range(0, len(trails), batch_size)]
    for idx, batch in enumerate(batches):
        print(f"  LLM enriching batch {idx+1}/{len(batches)}…")
        listing = "\n".join(
            f"{i+1}. {t['name']} | region: {t['region']} | desc: {t['_desc'][:150]}"
            for i, t in enumerate(batch)
        )
        prompt = f"""Greek hiking expert. Fill in metadata for each trail.
Return ONLY a JSON array, no markdown.

Each object:
  "index"               : int (1-based)
  "highlights"          : list of 3 short strings
  "local_economy_score" : int 0-10
  "difficulty"          : "easy"|"moderate"|"hard"
  "terrain"             : "coastal"|"mountain"|"forest"|"mixed"
  "crowd_level"         : int 1-5

Trails:
{listing}
"""
        try:
            resp = bedrock.converse(
                modelId=MODEL,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 2000},
            )
            raw = resp["output"]["message"]["content"][0]["text"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            for item in json.loads(raw.strip()):
                i = item["index"] - 1
                if 0 <= i < len(batch):
                    batch[i].update({
                        "highlights":          item.get("highlights", []),
                        "local_economy_score": item.get("local_economy_score", 5),
                        "difficulty":          item.get("difficulty", batch[i]["difficulty"]),
                        "terrain":             item.get("terrain", batch[i]["terrain"]),
                        "crowd_level":         item.get("crowd_level", batch[i]["crowd_level"]),
                    })
        except Exception as e:
            print(f"  ✗ Batch {idx+1} enrichment failed: {e}")
        enriched.extend(batch)
        time.sleep(1)
    return enriched


# ── Main ─────────────────────────────────────────────────────────────────────

def build(use_llm=True, min_trails=20, max_trails=50):
    print("\n🗺️  Building trail database from OpenStreetMap\n" + "="*45)

    elements = fetch(RELATION_QUERY, "hiking relations")
    time.sleep(2)
    trails = parse_elements(elements, "relation")

    if len(trails) < min_trails:
        print(f"\n  Only {len(trails)} relations — supplementing with ways…")
        way_els  = fetch(WAY_QUERY, "hiking ways")
        existing = {t["name"] for t in trails}
        extras   = [t for t in parse_elements(way_els, "way") if t["name"] not in existing]
        trails  += extras
        print(f"  Added {len(extras)} ways → total {len(trails)}")

    trails = trails[:max_trails]

    if use_llm and os.getenv("AWS_ACCESS_KEY_ID"):
        print(f"\n  Enriching {len(trails)} trails with LLM…")
        trails = enrich(trails)
    else:
        print("  Skipping LLM enrichment (no AWS credentials)")

    # Strip internal fields
    clean = [{k: v for k, v in t.items() if not k.startswith("_")} for t in trails]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(clean)} trails → {OUTPUT_PATH}")
    if clean:
        print("\nSample:\n" + json.dumps(clean[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    build()
