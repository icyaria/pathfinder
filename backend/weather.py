"""
weather.py
Fetches weather from OpenWeatherMap.

- get_weather_for_date(lat, lon, date_str): uses 5-day forecast when the
  planned date is within 5 days; falls back to current conditions otherwise.
- get_weather(lat, lon): current conditions (kept for backward compat).
"""

import os
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")


def _safety_flags(main: str, temp: float, wind_kmh: float) -> list:
    flags = []
    if main == "Thunderstorm":
        flags.append("⛔ Thunderstorm — do not hike today")
    if main == "Snow":
        flags.append("⛔ Snow — trail may be impassable")
    if main == "Rain":
        flags.append("⚠️ Rain — expect slippery rocks and mud")
    if temp is not None:
        if temp > 35:
            flags.append("🌡️ Extreme heat — start before 7 AM, carry 3L+ water")
        if temp < 2:
            flags.append("🧊 Near-freezing — layer up, watch for ice patches")
    if wind_kmh is not None:
        if wind_kmh > 50:
            flags.append("💨 Strong winds — avoid exposed ridgelines")
        elif wind_kmh > 30:
            flags.append("💨 Gusty winds — take care on open sections")
    return flags


def _parse_entry(entry: dict) -> dict:
    """Extract common fields from a current-weather or forecast entry."""
    w        = entry["weather"][0]
    temp     = round(entry["main"]["temp"], 1)
    wind_kmh = round(entry["wind"]["speed"] * 3.6, 1)
    main     = w["main"]
    desc     = w["description"]
    return {
        "temp_c":       temp,
        "conditions":   desc,
        "weather_main": main,
        "wind_kmh":     wind_kmh,
        "safety_flags": _safety_flags(main, temp, wind_kmh),
        "safe":         not any("⛔" in f for f in _safety_flags(main, temp, wind_kmh)),
    }


def _no_key_response() -> dict:
    return {
        "temp_c": None, "conditions": "Unavailable (no OPENWEATHER_API_KEY)",
        "weather_main": None, "wind_kmh": None, "safety_flags": [], "safe": True,
        "_skipped": True,
    }


def _error_response(e) -> dict:
    return {
        "temp_c": None, "conditions": f"Error: {e}", "weather_main": None,
        "wind_kmh": None, "safety_flags": [], "safe": True, "_error": str(e),
    }


def _get_current(lat: float, lon: float) -> dict:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )
    data = requests.get(url, timeout=6).json()
    return _parse_entry(data)


def _get_forecast(lat: float, lon: float, target: datetime.date) -> dict:
    """Find the forecast entry closest to noon on target date."""
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )
    data  = requests.get(url, timeout=8).json()
    items = data.get("list", [])
    if not items:
        return _get_current(lat, lon)

    # Target: noon on the planned day
    target_ts = datetime.datetime(target.year, target.month, target.day, 12, 0).timestamp()
    best = min(items, key=lambda e: abs(e["dt"] - target_ts))
    result = _parse_entry(best)
    result["_forecast_for"] = target.isoformat()
    return result


def get_weather_for_date(lat: float, lon: float, date_str: str = None) -> dict:
    """
    Main entry point. Returns weather dict for the planned hike date.
    Uses 5-day forecast if date is 1–5 days out; current weather otherwise.
    """
    if not API_KEY:
        return _no_key_response()

    target = None
    if date_str:
        try:
            target = datetime.date.fromisoformat(date_str[:10])
        except ValueError:
            pass

    try:
        today = datetime.date.today()
        if target and target > today:
            days_ahead = (target - today).days
            if days_ahead <= 5:
                return _get_forecast(lat, lon, target)
            else:
                result = _get_current(lat, lon)
                result["_forecast_note"] = (
                    f"Date is {days_ahead} days away — forecast unavailable beyond 5 days; "
                    "showing current conditions as a reference."
                )
                return result
        return _get_current(lat, lon)
    except Exception as e:
        return _error_response(e)


def get_weather(lat: float, lon: float) -> dict:
    """Backward-compatible wrapper — returns current conditions."""
    return get_weather_for_date(lat, lon)


_COND_EMOJI = {
    "Clear": "☀️", "Clouds": "⛅", "Rain": "🌧️", "Drizzle": "🌦️",
    "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️",
    "Haze": "🌁", "Dust": "🌪️", "Sand": "🌪️", "Smoke": "🌫️",
    "Squall": "💨", "Tornado": "🌪️",
}


def get_weather_calendar(lat: float, lon: float,
                         center_date_str: str, window: int = 2) -> list:
    """
    Returns weather for center_date ± window days as a list of dicts.

    Each dict:
        date        str  ISO date
        is_planned  bool True only for center_date
        available   bool False when outside 5-day forecast or API key missing
        reason      str  why unavailable: "no_key" | "too_far" | "past" | "error"
        emoji       str  weather emoji (when available)
        temp_c, conditions, weather_main, wind_kmh, safety_flags  (when available)
    """
    if not API_KEY:
        return [{"date": center_date_str, "available": False, "reason": "no_key"}]

    try:
        center = datetime.date.fromisoformat(center_date_str[:10])
    except (ValueError, TypeError, AttributeError):
        return []

    today            = datetime.date.today()
    max_forecast_day = today + datetime.timedelta(days=5)

    # Fetch forecast list once — covers up to 5 days in 3-hour slots
    forecast_items = []
    try:
        url  = (f"https://api.openweathermap.org/data/2.5/forecast"
                f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric")
        data = requests.get(url, timeout=8).json()
        forecast_items = data.get("list", [])
    except Exception:
        pass

    days = []
    for delta in range(-window, window + 1):
        day        = center + datetime.timedelta(days=delta)
        is_planned = delta == 0

        if day < today:
            days.append({"date": day.isoformat(), "is_planned": is_planned,
                         "available": False, "reason": "past"})
            continue

        if day > max_forecast_day:
            days.append({"date": day.isoformat(), "is_planned": is_planned,
                         "available": False, "reason": "too_far"})
            continue

        # Find forecast entry nearest to noon on this day
        target_ts = datetime.datetime(day.year, day.month, day.day, 12, 0).timestamp()
        if forecast_items:
            best   = min(forecast_items, key=lambda e: abs(e["dt"] - target_ts))
            parsed = _parse_entry(best)
            parsed["date"]       = day.isoformat()
            parsed["is_planned"] = is_planned
            parsed["available"]  = True
            parsed["emoji"]      = _COND_EMOJI.get(parsed.get("weather_main", ""), "🌡️")
            days.append(parsed)
        else:
            days.append({"date": day.isoformat(), "is_planned": is_planned,
                         "available": False, "reason": "error"})

    return days
