"""
WeatherAgent - fetches a short-term forecast for the farm's coordinates
from Open-Meteo (free, no API key required). Produces a compact summary
that downstream agents (Advisory, Decision) can reason over.
"""

from typing import Any, Dict
import requests
from agents.base_agent import BaseAgent
from config import WEATHER_API_URL


class WeatherAgent(BaseAgent):
    name = "weather_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        lat = context.get("latitude")
        lon = context.get("longitude")
        if lat is None or lon is None:
            return {"weather_error": "latitude/longitude not provided in context"}

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "relative_humidity_2m_mean,wind_speed_10m_max",
            "forecast_days": 5,
            "timezone": "auto",
        }
        response = requests.get(WEATHER_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        forecast = []
        for i, date in enumerate(daily.get("time", [])):
            forecast.append({
                "date": date,
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "humidity_pct": daily["relative_humidity_2m_mean"][i],
                "wind_speed_kmh": daily["wind_speed_10m_max"][i],
            })

        total_rain = sum(day["precipitation_mm"] for day in forecast)
        avg_temp = sum(
            (day["temp_max_c"] + day["temp_min_c"]) / 2 for day in forecast
        ) / max(len(forecast), 1)

        return {
            "weather_forecast": forecast,
            "weather_summary": {
                "5day_total_rain_mm": round(total_rain, 1),
                "avg_temp_c": round(avg_temp, 1),
                "rain_expected": total_rain > 5.0,
            },
        }
