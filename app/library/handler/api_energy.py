#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import json


class ApiEnergy(RequestHandler):

    def get(self):
        # Mock data for energy dashboard demonstration
        mock_data = {
            "pv_battery": {
                "current_power": 2450,  # Current PV power in watts
                "battery_level": 78,       # Battery charge percentage
                "daily_production": 12.4   # Daily production in kWh
            },
            "pv_direct": {
                "current_power": 1800,   # Current PV power in watts
                "daily_production": 8.7,    # Daily production in kWh
                "export_power": 950        # Power exported to grid in watts
            },
            "house_consumption": {
                "current_power": 2200,   # Current house consumption in watts
                "daily_consumption": 15.2   # Daily consumption in kWh
            },
            "battery": {
                "level": 78,             # Battery charge percentage
                "charge_rate": 1200       # Charge/discharge rate in watts (positive = charging)
            },
            "grid": {
                "import_power": 0,        # Power imported from grid in watts
                "export_power": 2000,     # Power exported to grid in watts
                "cost_cents": 32           # Current electricity cost in cents/kWh
            },
            "ev": {
                "model": "Renault Zoe",
                "connected": True,         # EV connected to charger
                "battery": {
                    "level": 65,        # EV battery percentage
                    "range": 180         # Estimated range in km
                },
                "charging": {
                    "active": True,     # Currently charging
                    "power": 7.4,      # Charging power in kW
                    "time_to_full": 85   # Minutes until full charge
                }
            },
            "timestamp": "2025-01-03T14:30:00+01:00"
        }
        
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(mock_data))