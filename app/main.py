#!/usr/bin/python3
# -*- coding: utf-8 -*-

import signal
import sys
import logging
from library.webserver import Webserver
from library.database import Database
from library.scheduler import Scheduler
from dotenv import load_dotenv


load_dotenv()
database = Database()
Database.initialize_tables(database)

def signal_handler(signal, frame):
  sys.exit(0)


if __name__ in '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s [%(name)s] %(message)s",
        datefmt='%d.%m.%Y %H:%M:%S',
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    signal.signal(signal.SIGINT, signal_handler)
    Scheduler(database).start()
    Webserver(database).serve()
