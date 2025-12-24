#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado
from library.handler.homepage import Homepage
from library.handler.api_zoe_battery import ApiZoeBattery
from library.handler.api_house_temp_current import ApiHouseTempCurrent
from library.handler.api_weather import ApiWeather
from library.handler.weather import Weather
from library.handler.health import Health
from tornado.web import Application
import os
import logging


rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

class Webserver():

    def __init__(self, database):
        self.logger = logging.getLogger('WEBSERVER')
        self.database = database

    def serve(self):
        settings = dict(
            template_path=rel('../templates'),
            static_path=rel('../static'),
            debug=True
        )
        app = Application([
            (r"/", Homepage),
            (r"/api/weather", ApiWeather),
            (r"/weather", Weather),
            (r"/health", Health),
            (r"/api/zoe/battery/current.json", ApiZoeBattery, dict(database=self.database)),
            (r"/api/house/temp/current.json", ApiHouseTempCurrent, dict(database=self.database)),
        ], **settings)

        http_server = tornado.httpserver.HTTPServer(app)
        port = '8080'
        http_server.listen(address='0.0.0.0', port=port)
        self.logger.info("[#] HomeAssistant is serving under 127.0.0.1:{} ...".format(port))
        tornado.ioloop.IOLoop.instance().start()