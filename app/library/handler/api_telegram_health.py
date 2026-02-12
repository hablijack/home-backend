#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import json
import logging
import asyncio
from library.ollama_client import OllamaClient
from library.Configuration import Configuration


class ApiTelegramHealth(RequestHandler):
    def initialize(self, database):
        self.logger = logging.getLogger("API_TELEGRAM_HEALTH")
        self.database = database
        self.ollama_client = OllamaClient()
        self.config = Configuration()

    async def get(self):
        """Health check for Telegram bot and Ollama service"""
        try:
            # Check if Telegram bot token is configured
            telegram_configured = bool(self.config.telegram_bot_token())

            # Check Ollama service health
            ollama_healthy = await self.ollama_client.health_check()

            health_status = {
                "telegram_bot": {
                    "configured": telegram_configured,
                    "status": "configured" if telegram_configured else "not_configured",
                },
                "ollama": {
                    "host": self.config.ollama_host(),
                    "model": self.config.ollama_model(),
                    "healthy": ollama_healthy,
                    "status": "healthy" if ollama_healthy else "unhealthy",
                },
                "overall_status": "healthy"
                if telegram_configured and ollama_healthy
                else "unhealthy",
            }

            status_code = 200 if health_status["overall_status"] == "healthy" else 503

            self.set_status(status_code)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(health_status, indent=2))

        except Exception as e:
            self.logger.error(f"Error in Telegram health check: {e}")
            self.set_status(500)
            self.write(
                json.dumps({"error": "Health check failed", "overall_status": "error"})
            )
