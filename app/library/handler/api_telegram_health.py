#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import json
import logging
import asyncio
from library.llama_client import LlamaClient
from library.Configuration import Configuration


class ApiTelegramHealth(RequestHandler):
    def initialize(self, database):
        self.logger = logging.getLogger("API_TELEGRAM_HEALTH")
        self.database = database
        self.llama_client = LlamaClient()
        self.config = Configuration()

    async def get(self):
        """Health check for Telegram bot and Llama service"""
        try:
            # Check if Telegram bot token is configured
            telegram_configured = bool(self.config.telegram_bot_token())

            # Check Llama service health
            llama_healthy = await self.llama_client.health_check()

            health_status = {
                "telegram_bot": {
                    "configured": telegram_configured,
                    "status": "configured" if telegram_configured else "not_configured",
                },
                "llama": {
                    "host": self.config.llama_host_gemma(),
                    "model": self.config.llama_model_gemma(),
                    "healthy": llama_healthy,
                    "status": "healthy" if llama_healthy else "unhealthy",
                },
                "overall_status": "healthy"
                if telegram_configured and llama_healthy
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
