# Pathfinder Makeathon Presentation Outline (Max 10 Slides)

## Slide 1 - Problem & Vision
- Challenge: overtourism and fragmented trail planning in Greece
- Vision: AI trail companion for sustainable route discovery
- Tagline: find your trail, leave no trace

## Slide 2 - Objectives
- Profile traveler via natural conversation
- Recommend trails by difficulty, duration, terrain
- Apply weather and safety checks
- Score sustainability and redirect demand away from hotspots

## Slide 3 - System Architecture
- Conversational intake: Anthropic profile extraction
- Data pipeline: OSM + ORS + weather + biodiversity + elevation
- Ranking + itinerary generation

## Slide 4 - Data Sources (Open Data Focus)
- OpenStreetMap/Overpass: trail candidates and metadata
- OpenRouteService: hiking route distances and durations
- OpenWeatherMap: real-time conditions and risk flags
- iNaturalist: biodiversity indicators
- NASA SRTM via OpenTopodata: elevation context

## Slide 5 - Personalization Logic
- Profile schema: duration, terrain, difficulty, interests, fitness
- Matching strategy: weighted relevance + safety penalties
- Why this improves recommendation quality

## Slide 6 - Sustainability Scoring
- Components: crowd avoidance, remoteness, biodiversity, local economy, region bonus
- 0-100 score and interpretation labels
- Optional side-by-side comparison of top trails

## Slide 7 - Demo Walkthrough
- User prompt example
- Top trail cards with weather, biodiversity, route, elevation
- Generated itinerary and map visualization

## Slide 8 - Findings
- Better fit with profile and safety context than static trail lists
- Transparent tradeoffs between convenience and sustainability
- Real open-data stack is viable on free tiers

## Slide 9 - Limitations & Risks
- API quota constraints and occasional latency
- OSM metadata quality variability by region
- Biodiversity and route signals are proxies, not full ground truth

## Slide 10 - Next Steps
- Add conversational follow-up loop in UI
- Integrate trail reports/crowd events
- Expand to multimodal route evidence and offline mode
