"""
weather.py
Fetches current weather from OpenWeatherMap and applies safety rules.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_weather(lat: float, lon: float) -> dict:
    """
    Returns current weather + a list of safety flags for the given coordinates.
    Gracefully skips if API key is missing.
    """
    if not API_KEY:
        return {
            "temp_c": None,
            "conditions": "Unavailable (no OPENWEATHER_API_KEY)",
            "wind_kmh": None,
            "safety_flags": [],
            "safe": True,
            "_skipped": True,
        }

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        )
        data = requests.get(url, timeout=6).json()

        main     = data["weather"][0]["main"]          # e.g. "Rain"
        desc     = data["weather"][0]["description"]   # e.g. "light rain"
        temp     = round(data["main"]["temp"], 1)
        wind_kmh = round(data["wind"]["speed"] * 3.6, 1)

        flags = []
        if main == "Thunderstorm":
            flags.append("⛔ Thunderstorm — do not hike today")
        if main == "Snow":
            flags.append("⛔ Snow — trail may be impassable")
        if main == "Rain":
            flags.append("⚠️ Rain — expect slippery rocks and mud")
        if temp > 35:
            flags.append("🌡️ Extreme heat — start before 7 AM, carry 3L+ water")
        if temp < 2:
            flags.append("🧊 Near-freezing — layer up, watch for ice patches")
        if wind_kmh > 50:
            flags.append("💨 Strong winds — avoid exposed ridgelines")
        elif wind_kmh > 30:
            flags.append("💨 Gusty winds — take care on open sections")

        return {
            "temp_c": temp,
            "conditions": desc,
            "wind_kmh": wind_kmh,
            "safety_flags": flags,
            "safe": not any("⛔" in f for f in flags),
        }

    except Exception as e:
        return {
            "temp_c": None,
            "conditions": f"Error: {e}",
            "wind_kmh": None,
            "safety_flags": [],
            "safe": True,
            "_error": str(e),
        }
