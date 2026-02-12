#!/usr/bin/python3
# -*- coding: utf-8 -*-

import threading
import logging
from library.telegram_bot import TelegramBot


class TelegramJob:
    def __init__(self, database):
        self.logger = logging.getLogger("TELEGRAM_JOB")
        self.database = database
        self.bot = None
        self.bot_thread = None

    def start_bot_service(self):
        """Start Telegram bot in a separate thread"""
        try:
            self.bot = TelegramBot(self.database)
            self.bot_thread = threading.Thread(target=self.bot.start, daemon=True)
            self.bot_thread.start()
            self.logger.info("Telegram bot service started in background thread")
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot service: {e}")

    @staticmethod
    def start(database):
        """Entry point for scheduler"""
        job = TelegramJob(database)
        job.start_bot_service()
