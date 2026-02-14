#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger("MAIN")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


class Energy:
    async def get(self, request: Request):
        logger.info("... rendering Energy Page!")
        return templates.TemplateResponse("energy.html", {"request": request})
