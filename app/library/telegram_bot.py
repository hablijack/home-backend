#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram import Update
from telegram.ext import Updater, MessageHandler, filters
from library.ollama_client import OllamaClient
from library.Configuration import Configuration


class TelegramBot:
    def __init__(self, database):
        self.config = Configuration()
        self.database = database
        self.logger = logging.getLogger("TELEGRAM_BOT")
        self.ollama_client = OllamaClient()
        self.bot_token = self.config.telegram_bot_token()
        self.updater = None

        if not self.bot_token:
            self.logger.error("TELEGRAM_BOT_TOKEN not configured")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")


def message_handler(self, update: Update, context):
    """Handle incoming Telegram messages with context and mention checks"""
    try:
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
        user_name = update.effective_user.full_name or "User"
        bot_username = context.bot.username.lower() if context.bot.username else None
        if not bot_username:
            return

        chat_type = update.effective_chat.type
        mentioned = False

        # Private Chat → immer antworten
        if chat_type == "private":
            mentioned = True
        else:
            # Gruppen → nur antworten, wenn Bot erwähnt wurde
            for entity in update.message.entities or []:
                if entity.type == "mention":
                    mention_text = user_message[
                        entity.offset : entity.offset + entity.length
                    ]
                    if mention_text[1:].lower() == bot_username:
                        mentioned = True
                        break

        if not mentioned:
            return

        # @BotName aus der Nachricht entfernen
        clean_text = user_message
        for entity in update.message.entities or []:
            if entity.type == "mention":
                mention_text = user_message[
                    entity.offset : entity.offset + entity.length
                ]
                if mention_text[1:].lower() == bot_username:
                    clean_text = clean_text.replace(mention_text, "")

        user_message = clean_text.strip()

        self.logger.info(f"Received message from {user_name}: {user_message}")

        # Event Loop korrekt erstellen und Ollama mit chat_id aufrufen
        chat_id = update.effective_chat.id
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            self.ollama_client.generate_response(chat_id, user_message)
        )
        loop.close()

        # Antwort senden
        update.message.reply_text(response)
        self.logger.info(f"Sent response to {user_name}: {response[:50]}...")


    except Exception as e:
        self.logger.error(f"Error handling message: {e}")
        try:
            update.message.reply_text(
                "Sorry, ich konnte deine Nachricht gerade nicht verarbeiten."
            )
        except:
            pass

    def start(self):
        """Start the bot in a background thread"""
        try:
            self.updater = Updater(bot_token=self.bot_token, use_context=True)

            self.updater.dispatcher.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
            )

            self.logger.info("Starting Telegram bot...")

            self.updater.start_polling()
            self.updater.idle()

        except Exception as e:
            self.logger.error(f"Telegram bot crashed: {e}")

    def stop(self):
        """Stop the bot gracefully"""
        self.logger.info("Stopping Telegram bot...")
        if self.updater:
            self.updater.stop()
