#!/usr/bin/python3
# -*- coding: utf-8 -*-

from fastapi.responses import JSONResponse
import json


class ApiEnergy:
    async def get(self):
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
            "grid": {"import_power": 0, "export_power": 2000, "cost_cents": 32},
            "ev": {
                "model": "Renault Zoe",
                "connected": True,
                "battery": {"level": 65, "range": 180},
                "charging": {"active": True, "power": 7.4, "time_to_full": 85},
            },
            "timestamp": "2025-01-03T14:30:00+01:00",
        }
        return JSONResponse(content=mock_data)
