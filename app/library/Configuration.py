#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

""""
Read configuration from environment variables
"""


class Configuration:
    def scheduler_active(self):
        return os.getenv("SCHEDULER_ACTIVE") == "true"

    def postgres_password(self):
        return os.getenv("POSTGRES_PASSWORD")

    def postgres_user(self):
        return os.getenv("POSTGRES_USER")

    def postgres_db(self):
        return os.getenv("POSTGRES_DB")

    def postgres_host(self):
        return os.getenv("POSTGRES_HOST")

    def fritz_api_ip(self):
        return os.getenv("FRITZ_API_IP")

    def fritz_api_pass(self):
        return os.getenv("FRITZ_API_PASS")

    def fritz_api_user(self):
        return os.getenv("FRITZ_API_USER")

    def fritz_garage_solar_ain(self):
        return os.getenv("FRITZ_GARAGE_SOLAR_AIN")

    def zoe_username(self):
        return os.getenv("ZOE_USERNAME")

    def zoe_password(self):
        return os.getenv("ZOE_PASSWORD")

    def zoe_account_id(self):
        return os.getenv("ZOE_ACCOUNT_ID")

    def zoe_vehicle_id(self):
        return os.getenv("ZOE_VEHICLE_ID")

    def openweathermap_api_key(self):
        return os.getenv("OPENWEATHERMAP_API_KEY")

    def telegram_bot_token(self):
        return os.getenv("TELEGRAM_BOT_TOKEN")

    def ollama_host(self):
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def ollama_model(self):
        return os.getenv("OLLAMA_MODEL", "llama3.2")
