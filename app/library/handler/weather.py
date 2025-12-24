#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import logging


class Weather(RequestHandler):

    def initialize(self):
        self.logger = logging.getLogger('WEATHER_PAGE_HANDLER')

    def get(self):
        self.logger.info("... rendering Weather Page!")
        self.render('weather.html')