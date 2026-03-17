#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Tool functions that the LLM can call.
Each function should have:
- Clear docstring describing what it does
- Type hints for parameters
- A return value that can be converted to string for the LLM
"""

import logging
import requests
import json
from datetime import datetime
import pytz
from typing import Optional
from library.Configuration import Configuration


class WeatherTool:
    """Tool to get weather forecast."""

    FORECAST_URL = (
        "https://hop.maschinenring.de/api/weather/7days/49.9829487/12.0663612/0"
    )
    CONDITIONS = {
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

    def get_current_weather(self) -> str:
        """
        Get current weather conditions.

        Returns:
            str: Current weather with temperature and condition.
        """
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            page = requests.get(self.FORECAST_URL, headers=headers)
            json_obj = json.loads(page.content.decode("utf-8"))

            today = json_obj["result"]["daily"][0]
            condition = self.CONDITIONS.get(today["weatherTypeID"], "unbekannt")
            min_temp = today["tmin"]
            max_temp = today["tmax"]

            return f"Aktuelles Wetter: {condition}, Temperatur: {min_temp}°C bis {max_temp}°C"
        except Exception as e:
            return f"Wetterdaten nicht verfügbar: {e}"

    def get_forecast(self, days: int = 3) -> str:
        """
        Get weather forecast for the next few days.

        Args:
            days: Number of days to forecast (max 7)

        Returns:
            str: Weather forecast summary.
        """
        try:
            days = min(days, 7)
            headers = {"User-Agent": "Mozilla/5.0"}
            page = requests.get(self.FORECAST_URL, headers=headers)
            json_obj = json.loads(page.content.decode("utf-8"))

            forecast_text = "Wettervorhersage:\n"
            for i, day in enumerate(json_obj["result"]["daily"][:days]):
                date = datetime.fromtimestamp(day["timestamp"]).strftime("%A, %d.%m.")
                condition = self.CONDITIONS.get(day["weatherTypeID"], "unbekannt")
                min_temp = day["tmin"]
                max_temp = day["tmax"]
                prec = day.get("precSum", 0)

                forecast_text += f"- {date}: {condition}, {min_temp}°C bis {max_temp}°C, Niederschlag: {prec}mm\n"

            return forecast_text
        except Exception as e:
            return f"Wetterdaten nicht verfügbar: {e}"


class EnergyTool:
    """Tool to get energy/battery data."""

    def get_energy_status(self) -> str:
        """
        Get current energy production and consumption status.

        Returns:
            str: Current energy status including solar, battery, grid, and EV.
        """
        mock_data = {
            "pv_battery": {
                "current_power": 2450,
                "battery_level": 78,
                "daily_production": 12.4,
            },
            "pv_direct": {
                "current_power": 1800,
                "daily_production": 8.7,
                "export_power": 950,
            },
            "house_consumption": {"current_power": 2200, "daily_consumption": 15.2},
            "battery": {"level": 78, "charge_rate": 1200},
            "grid": {"import_power": 0, "export_power": 2000},
            "ev": {
                "model": "Renault Zoe",
                "connected": True,
                "battery_level": 65,
                "charging": True,
            },
        }

        try:
            from library.handler.api_energy import ApiEnergy
            import asyncio

            handler = ApiEnergy()
            result = asyncio.run(handler.get())
            if isinstance(result, dict):
                mock_data = result
        except Exception:
            pass

        pv = mock_data.get("pv_direct", {})
        battery = mock_data.get("battery", {})
        grid = mock_data.get("grid", {})
        house = mock_data.get("house_consumption", {})
        ev = mock_data.get("ev", {})

        return (
            f"PV-Anlage: {pv.get('current_power', 0)}W Ertrag, "
            f"Batterie: {battery.get('level', 0)}% ({battery.get('charge_rate', 0)}W), "
            f"Hausverbrauch: {house.get('current_power', 0)}W, "
            f"Netz: {grid.get('import_power', 0)}W Bezug / {grid.get('export_power', 0)}W Einspeisung, "
            f"EV: {ev.get('battery_level', 0)}% {'(lädt)' if ev.get('charging') else ''}"
        )


class WebResearchTool:
    """Tool to research information from the web."""

    def __init__(self):
        self.logger = logging.getLogger("WEB_RESEARCH")
        self.config = Configuration()
        self.max_results = 5

    def search_web(self, query: str, num_results: int = 5) -> str:
        """
        Search the web for information on a topic.

        Args:
            query: The search query to research
            num_results: Number of results to return (default 5, max 10)

        Returns:
            str: Search results with titles, URLs and summaries
        """
        try:
            num_results = min(num_results, 10)

            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.tavily_api_key())
            response = client.search(query, max_results=num_results)

            if not response.get("results"):
                return f"Keine Ergebnisse für: {query}"

            output = f"Suchergebnisse für '{query}':\n\n"
            for r in response["results"]:
                output += f"1. {r['title']}\n"
                output += f"   {r['content'][:300]}...\n"
                output += f"   URL: {r['url']}\n\n"

            return output

        except Exception as e:
            self.logger.error(f"Web search error: {e}")
            return f"Suche fehlgeschlagen: {e}"

    def fetch_url(self, url: str) -> str:
        """
        Fetch and summarize the content of a specific URL.

        Args:
            url: The URL to fetch content from

        Returns:
            str: The main content of the page
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                return f"Fehler beim Abrufen: HTTP {response.status_code}"

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Get main content
            text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            content = "\n".join(lines[:50])  # Limit to first 50 lines

            return content if content else "Kein Inhalt gefunden"

        except Exception as e:
            self.logger.error(f"URL fetch error: {e}")
            return f"Fehler beim Abrufen: {e}"


# Initialize tool instances
weather_tool = WeatherTool()
energy_tool = EnergyTool()
web_tool = WebResearchTool()

# Tool registry - maps function names to actual functions
AVAILABLE_TOOLS = {
    "get_current_weather": weather_tool.get_current_weather,
    "get_weather_forecast": weather_tool.get_forecast,
    "get_energy_status": energy_tool.get_energy_status,
    "search_web": web_tool.search_web,
    "fetch_url": web_tool.fetch_url,
}


def get_tool_schemas():
    """
    Generate tool schemas for Ollama.

    Returns:
        list: List of tool definitions in JSON schema format.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather conditions including temperature and condition.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_forecast",
                "description": "Get the weather forecast for the next few days.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to forecast (1-7)",
                            "default": 3,
                        }
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_energy_status",
                "description": "Get current energy status including solar panels, battery, house consumption, grid, and electric vehicle charging status.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for current information, facts, or details. PFLICHT: Du MUSST dieses Tool verwenden bei Fragen zu: aktuellen Ereignissen, Fakten, Personen, Orten, Zahlen, Daten, oder alles was dein Wissen übersteigen könnte. NIE selbst ausdenken - immer zuerst suchen!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to research",
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-10, default 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_url",
                "description": "Fetch and read the content of a specific URL to get more detailed information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch content from",
                        }
                    },
                    "required": ["url"],
                },
            },
        },
    ]
