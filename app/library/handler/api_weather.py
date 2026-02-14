#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import requests
import json
from datetime import datetime
import pytz
from fastapi.responses import JSONResponse


class ApiWeather:
    def __init__(self):
        self.logger = logging.getLogger("API_WEATHER")
        self.FORECAST_URL = (
            "https://hop.maschinenring.de/api/weather/7days/49.9829487/12.0663612/0"
        )
        self.CONDITIONS = {
            1: "wolkenlos",
            2: "sonnig und heiß",
            3: "gering bewölkt, meist sonnig",
            4: "wechselnd bewölkt, teils sonnig",
            5: "wechselnd bewölkt mit Regenschauern",
            6: "wechselnd bewölkt mit Schneeregen",
            7: "wechselnd bewölkt mit Schneeschauern",
            8: "stark bewölkt",
            9: "dicht bewölkt mit Regen",
            10: "Regen",
            11: "dicht bewölkt mit Schneefall",
            12: "dicht bewölkt mit Schneeregen",
            13: "Gewitter",
            14: "Nebel",
            15: "Hochnebel",
            16: "meist sonnig",
        }
        self.ICONS = {
            1: "clear-day.svg",
            2: "clear-day.svg",
            3: "partly-cloudy-day.svg",
            4: "partly-cloudy-day.svg",
            5: "rain.svg",
            6: "rain-snow-showers-day.svg",
            7: "snow-showers-day.svg",
            8: "cloudy.svg",
            9: "rain.svg",
            10: "rain.svg",
            11: "snow-showers-day.svg",
            12: "rain-snow-showers-day.svg",
            13: "thunder-showers-day.svg",
            14: "fog.svg",
            15: "fog.svg",
            16: "partly-cloudy-day.svg",
        }
        self.MOON_PHASES = {
            "new": 0,
            "waxing_crescent": 1,
            "first_quarter": 2,
            "waxing_gibbous": 3,
            "full": 4,
            "waning_gibbous": 5,
            "last_quarter": 6,
            "waning_crescent": 7,
        }

    def fetch(self):
        try:
            forecast = []
            headers = {"User-Agent": "Mozilla/5.0"}
            page = requests.get(self.FORECAST_URL, headers=headers)
            json_obj = json.loads(page.content.decode("utf-8"))
            for day in json_obj["result"]["daily"]:
                moon_phase_index = 0
                moon_phase_name = "Neumond"
                if "moon" in day and "phase" in day["moon"]:
                    moon_phase_index = self.MOON_PHASES.get(day["moon"]["phase"], 0)
                    moon_phase_names = [
                        "Neumond",
                        "Zunehmende Sichel",
                        "Viertelmond",
                        "Zunehmender Mond",
                        "Vollmond",
                        "Abnehmender Mond",
                        "Letztes Viertel",
                        "Abnehmende Sichel",
                    ]
                    moon_phase_name = moon_phase_names[moon_phase_index]

                day_condition = {
                    "day": day["timestamp"],
                    "condition": self.CONDITIONS.get(day["weatherTypeID"]),
                    "min_temp": day["tmin"],
                    "max_temp": day["tmax"],
                    "prec_amount": day["precSum"],
                    "prec_text": self.get_precipitation_text(day["weatherTypeID"]),
                    "prec_prob": self.get_precipitation_probability(
                        json_obj["result"]["hourly"], day
                    ),
                    "icon": self.ICONS.get(day["weatherTypeID"]),
                    "sunrise": self.convert_to_local_timestamp(day["sunrise"]),
                    "sunset": self.convert_to_local_timestamp(day["sunset"]),
                    "moon_phase_index": moon_phase_index,
                    "moon_phase_name": moon_phase_name,
                }
                forecast.append(day_condition)
            return forecast
        except Exception as e:
            return str(e)

    def get_precipitation_probability(self, hourly_forecast, day):
        prec_prob = 0
        for hour in hourly_forecast:
            if (
                datetime.fromtimestamp(hour["timestamp"]).date()
                == datetime.fromtimestamp(day["timestamp"]).date()
            ):
                if hour["precRisk"] > prec_prob:
                    prec_prob = hour["precRisk"]
        return prec_prob

    def convert_to_local_timestamp(self, utc_timestamp):
        berlin_tz = pytz.timezone("Europe/Berlin")
        utc_dt = datetime.fromtimestamp(utc_timestamp, pytz.UTC)
        berlin_dt = utc_dt.astimezone(berlin_tz)
        return int(berlin_dt.timestamp() * 1000)

    def get_precipitation_text(self, type_id):
        prec_text = ""
        if type_id in [6, 7, 11, 12]:
            prec_text = " cm Neuschnee"
        else:
            prec_text = " mm Regen"
        return prec_text

    async def get(self):
        return {"weather": self.fetch()}
