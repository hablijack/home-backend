#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from library.ollama_client import OllamaClient
from library.Configuration import Configuration


class TelegramBot:
    def __init__(self, database):
        self.config = Configuration()
        self.database = database
        self.logger = logging.getLogger("TELEGRAM_BOT")
        self.ollama_client = OllamaClient()
        self.bot_token = self.config.telegram_bot_token()

        if not self.bot_token:
            self.logger.error("TELEGRAM_BOT_TOKEN not configured")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

    async def message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incoming Telegram messages"""
        try:
            user_message = update.message.text
            user_name = update.effective_user.full_name or "User"

            self.logger.info(f"Received message from {user_name}: {user_message}")

            # Generate response using Ollama
            response = await self.ollama_client.generate_response(user_message)

            # Send response back to user
            await update.message.reply_text(response)

            self.logger.info(f"Sent response to {user_name}: {response[:50]}...")

        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text(
                    "Sorry, I encountered an error processing your message."
                )
            except:
                pass  # If we can't even send an error message, just log it

    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            # Check Ollama health before starting
            if not await self.ollama_client.health_check():
                self.logger.warning(
                    "Ollama service is not available, bot responses may fail"
                )

            # Create the Application
            application = Application.builder().token(self.bot_token).build()

            # Add message handler
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
            )

            self.logger.info("Starting Telegram bot...")

            # Start the bot (this will run until stopped)
            await application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            self.logger.error(f"Error starting Telegram bot: {e}")
            raise

    def start(self):
        """Start the bot in a way that's compatible with existing sync code"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_bot())
        except KeyboardInterrupt:
            self.logger.info("Telegram bot stopped by user")
        except Exception as e:
            self.logger.error(f"Telegram bot crashed: {e}")

    async def stop(self):
        """Stop the bot gracefully"""
        self.logger.info("Stopping Telegram bot...")
        # Additional cleanup can be added here if needed
