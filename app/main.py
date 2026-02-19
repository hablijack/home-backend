#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s [%(name)s] %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext import filters

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from library.Configuration import Configuration
from library.database import Database
from library.ollama_client import OllamaClient
from library.sql import Sql

config = Configuration()
logger = logging.getLogger("MAIN")

db = None
try:
    db = Database()
    Database.initialize_tables(db)
except Exception as e:
    logger.warning(f"Database connection failed: {e}")

scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
ollama_client = OllamaClient()
sql = Sql()

telegram_app = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("Scheduler started")
    yield
    logger.info("Shutting down...")
    if telegram_app and telegram_app.updater:
        logger.info("Stopping Telegram bot...")
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("Telegram bot stopped")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(lifespan=lifespan)

static_path = os.path.join(BASE_DIR, "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# -----------------------
# Telegram Bot
# -----------------------


async def start_command(update: Update, context):
    await update.message.reply_text("Bot läuft!")


async def message_handler(update: Update, context):
    try:
        # Grunddaten
        user_message = update.message.text
        chat_id = update.effective_chat.id  # Chat-ID für Kontexte
        user = update.effective_user
        user_name = user.full_name if user else "User"
        logger.info(f"Received message from {user_name}: {user_message}")

        # Erste Rückmeldung an Nutzer
        sent_message = await update.message.reply_text("🤖 Generiere Antwort...")
        current_text = ""
        last_edit_time = 0

        # Callback für Streaming
        async def on_chunk(chunk: str):
            nonlocal current_text, last_edit_time
            if not chunk:
                return
            current_text += chunk
            import time
            now = time.time()
            if now - last_edit_time > 1.5:  # Telegram Rate-Limit
                try:
                    await sent_message.edit_text(current_text)
                    last_edit_time = now
                except Exception:
                    pass

        # Ollama Streaming aufrufen
        try:
            result = await ollama_client.stream_response(chat_id, user_message, on_chunk)
            if result:
                await sent_message.edit_text(result)  # Endgültige Antwort
            else:
                await sent_message.edit_text("Sorry, ich konnte keine Antwort generieren.")
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            await sent_message.edit_text(
                "Entschuldigung, beim Generieren der Antwort ist ein Fehler aufgetreten."
            )

        logger.info(f"Sent response to {user_name}: {current_text[:50]}...")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        try:
            await update.message.reply_text(
                "Entschuldigung, beim Verarbeiten deiner Nachricht ist ein Fehler aufgetreten."
            )
        except Exception:
            pass


async def run_bot():
    global telegram_app
    try:
        telegram_app = ApplicationBuilder().token(config.telegram_bot_token()).build()
        telegram_app.add_handler(CommandHandler("start", start_command))

        async def group_message_handler(update: Update, context):
            if update.message and update.message.text:
                await message_handler(update, context)

        telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        telegram_app.add_handler(
            MessageHandler(
                filters.ChatType.GROUP | filters.ChatType.SUPERGROUP,
                group_message_handler,
            )
        )

        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.bot.initialize()
        await telegram_app.updater.start_polling()
        logger.info("Telegram bot started")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")


# -----------------------
# Scheduler Jobs
# -----------------------


def register_scheduler_jobs():
    from jobs.homeAutomation import HomeAutomation
    from jobs.zoe import Zoe
    from jobs.e320 import E320
    from jobs.phone import Phone

    if config.scheduler_active():
        if db:
            scheduler.add_job(HomeAutomation.fetch, "interval", [db], minutes=1)
            scheduler.add_job(E320.fetch, "interval", [db], minutes=1)
            scheduler.add_job(Zoe.fetch, "interval", [db], minutes=15)
            scheduler.add_job(Phone.fetch, "interval", [db], minutes=15)
            scheduler.add_job(Database.cleanup, "cron", [db], hour=10, minute=30)
            logger.info("Scheduler jobs registered with database")
        else:
            logger.warning("Scheduler jobs NOT registered - no database connection")


register_scheduler_jobs()


# -----------------------
# FastAPI Routes
# -----------------------


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/weather")
async def api_weather():
    from library.handler.api_weather import ApiWeather

    handler = ApiWeather()
    return {"weather": handler.fetch()}


@app.get("/weather", response_class=HTMLResponse)
async def weather_page(request: Request):
    from library.handler.weather import Weather

    handler = Weather()
    return await handler.get(request)


@app.get("/energy", response_class=HTMLResponse)
async def energy_page(request: Request):
    from library.handler.energy import Energy

    handler = Energy()
    return await handler.get(request)


@app.get("/api/energy")
async def api_energy():
    from library.handler.api_energy import ApiEnergy

    handler = ApiEnergy()
    return await handler.get()


@app.get("/api/openmeteo")
async def api_openmeteo():
    from library.handler.api_openmeteo import ApiOpenMeteo

    handler = ApiOpenMeteo()
    return await handler.get()


@app.get("/api/zoe/battery/current.json")
async def api_zoe_battery():
    if not db:
        return {"error": "Database not connected"}
    handler = ApiZoeBattery(db)
    return await handler.get()


@app.get("/api/house/temp/current.json")
async def api_house_temp():
    if not db:
        return {"error": "Database not connected"}
    handler = ApiHouseTempCurrent(db)
    return await handler.get()


@app.get("/api/telegram/health")
async def api_telegram_health():
    if not db:
        return {"error": "Database not connected"}
    handler = ApiTelegramHealth(db)
    return await handler.get()


# -----------------------
# Handler Classes (FastAPI compatible)
# -----------------------


class ApiZoeBattery:
    def __init__(self, database):
        self.database = database
        self.logger = logging.getLogger("API_ZOE_BATTERY_HANDLER")

    async def get(self):
        try:
            result = self.database.read(sql.generate_zoe_last_entry_query())
            if result:
                battery_level, total_mileage = result[0]
                return {"battery_level": battery_level, "total_mileage": total_mileage}
            return {"battery_level": 0, "total_mileage": 0}
        except Exception as e:
            self.logger.error(f"Error fetching Zoe data: {e}")
            return {"error": "Failed to fetch Zoe data"}


class ApiHouseTempCurrent:
    def __init__(self, database):
        self.database = database
        self.logger = logging.getLogger("API_HOUSE_TEMP_HANDLER")

    async def get(self):
        try:
            result = self.database.read(sql.generate_solarpanel_last_entry_query())
            if result:
                temp, status, power = result[0]
                return {"temp": temp, "status": status, "power": power}
            return {"temp": 0, "status": 0, "power": 0}
        except Exception as e:
            self.logger.error(f"Error fetching house temp data: {e}")
            return {"error": "Failed to fetch house temp data"}


class ApiTelegramHealth:
    def __init__(self, database):
        self.database = database
        self.logger = logging.getLogger("API_TELEGRAM_HEALTH_HANDLER")

    async def get(self):
        return {"status": "ok", "bot": "running" if telegram_app else "stopped"}


# -----------------------
# Main
# -----------------------


async def main():
    try:
        await asyncio.gather(
            run_bot(),
            uvicorn.Server(
                uvicorn.Config(
                    app,
                    host="0.0.0.0",
                    port=8000,
                    log_config={
                        "version": 1,
                        "disable_existing_loggers": False,
                        "formatters": {
                            "default": {
                                "format": "%(asctime)s - %(levelname)s [%(name)s] %(message)s",
                                "datefmt": "%d.%m.%Y %H:%M:%S",
                            },
                            "access": {
                                "format": "%(asctime)s - %(levelname)s [%(name)s] %(message)s",
                                "datefmt": "%d.%m.%Y %H:%M:%S",
                            },
                        },
                    },
                )
            ).serve(),
        )
    except asyncio.CancelledError:
        logger.info("Main task cancelled - shutdown initiated")


if __name__ == "__main__":
    asyncio.run(main())
