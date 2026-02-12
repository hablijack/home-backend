#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apscheduler.schedulers.background import BackgroundScheduler
from jobs.homeAutomation import HomeAutomation

from jobs.zoe import Zoe
from jobs.e320 import E320
from jobs.phone import Phone
from jobs.telegram import TelegramJob
from library.database import Database
from library.Configuration import Configuration


class Scheduler:
    def __init__(self, database):
        self.config = Configuration()
        self.database = database
        self.scheduler = BackgroundScheduler({"apscheduler.timezone": "Europe/Berlin"})
        self.register_jobs()

    def start(self):
        self.scheduler.start()


def register_jobs(self):
    if self.config.scheduler_active():
        Phone.fetch(self.database)
        TelegramJob.start(self.database)  # Start Telegram bot service
        self.scheduler.add_job(
            HomeAutomation.fetch, "interval", [self.database], minutes=1
        )
        self.scheduler.add_job(E320.fetch, "interval", [self.database], minutes=1)
        self.scheduler.add_job(Zoe.fetch, "interval", [self.database], minutes=15)
        self.scheduler.add_job(Phone.fetch, "interval", [self.database], minutes=15)
        self.scheduler.add_job(
            Database.cleanup, "cron", [self.database], hour="10", minute="30"
        )
    else:
        pass
