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

    def llama_host_gemma(self):
        return os.getenv("LLAMA_HOST_GEMMA", "http://localhost:11434")

    def llama_model_gemma(self):
        return os.getenv("LLAMA_MODEL_GEMMA", "gemma-4-e2b-it-q4_k_m.gguf")

    def tavily_api_key(self):
        return os.getenv("TAVILY_API_KEY")

    def telegram_allowed_chat_ids(self):
        raw = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
        return [int(x.strip()) for x in raw.split(",") if x.strip()] if raw else []

    def telegram_allowed_user_ids(self):
        raw = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
        return [int(x.strip()) for x in raw.split(",") if x.strip()] if raw else []
