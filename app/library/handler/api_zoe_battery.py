#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from library.sql import Sql
import logging


class ApiZoeBattery(RequestHandler):

    def initialize(self, database):
        self.logger = logging.getLogger('API_ZOE_BATTERY_HANDLER')
        self.database = database
        self.sql = Sql()

    def get(self):
        self.logger.info("... requesting zoe battery status via json api!")
        
        try:
            # Fetch latest Zoe data from database
            result = self.database.read(self.sql.generate_zoe_last_entry_query())
            
            if result:
                battery_level, total_mileage = result[0]
                
                zoe_data = {
                    "battery_level": battery_level,
                    "total_mileage": total_mileage
                }
            else:
                # No data available, return empty state
                zoe_data = {
                    "battery_level": 0,
                    "total_mileage": 0
                }
            
            self.set_header("Content-Type", "application/json")
            self.write(zoe_data)
            
        except Exception as e:
            self.logger.error("Error fetching Zoe data: %s" % e)
            self.set_status(500)
            self.write({"error": "Failed to fetch Zoe data"})
