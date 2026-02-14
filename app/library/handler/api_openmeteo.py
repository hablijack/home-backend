#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import requests
import json
from fastapi.responses import JSONResponse


class ApiOpenMeteo:
    def __init__(self):
        self.logger = logging.getLogger("API_OPENMETEO")
        self.lat = 49.9083
        self.lon = 12.0083

    def fetch(self):
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current_weather": "true",
            "daily": "uv_index_max,apparent_temperature_max,apparent_temperature_min",
            "hourly": "apparent_temperature,uv_index,relativehumidity_2m",
            "timezone": "Europe/Berlin",
            "forecast_days": 1,
        }

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            weather_data = {
                "current": self.process_current(
                    data.get("current_weather", {}), data.get("hourly", {})
                ),
                "daily": self.process_daily(data.get("daily", {})),
                "timezone": data.get("timezone", "Europe/Berlin"),
            }
            return weather_data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching OpenMeteo data: {e}")
            return {"error": f"Failed to fetch weather data: {str(e)}"}

    def process_current(self, current, hourly):
        current_time = current.get("time", "")
        current_temp = current.get("temperature", 0)
        current_hour = current_time[:13] + ":00"

        apparent_temp = current_temp
        uv_index = 0
        humidity = 0

        if "time" in hourly:
            for i, hour_time in enumerate(hourly["time"]):
                if hour_time == current_hour:
                    if i < len(hourly.get("apparent_temperature", [])):
                        apparent_temp = hourly["apparent_temperature"][i]
                    if i < len(hourly.get("uv_index", [])):
                        uv_index = hourly["uv_index"][i]
                    if i < len(hourly.get("relativehumidity_2m", [])):
                        humidity = hourly["relativehumidity_2m"][i]
                    break

        return {
            "timestamp": current_time,
            "temperature": current_temp,
            "humidity": humidity,
            "feels_like": apparent_temp,
            "uv_index": uv_index,
            "wind_speed": current.get("windspeed", 0),
            "wind_direction": current.get("winddirection", 0),
            "weather_code": current.get("weathercode", 0),
        }

    def process_daily(self, daily):
        if not daily or "time" not in daily:
            return {}
        today_data = {}
        for key, values in daily.items():
            if isinstance(values, list) and len(values) > 0:
                today_data[key] = values[0]

        return {
            "timestamp": today_data.get("time", ""),
            "uv_index_max": today_data.get("uv_index_max", 0),
            "apparent_temperature_max": today_data.get("apparent_temperature_max", 0),
            "apparent_temperature_min": today_data.get("apparent_temperature_min", 0),
        }

    async def get(self):
        weather_data = self.fetch()
        return {"weather": weather_data}
