#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from library.Configuration import Configuration
from library.sql import Sql


class HomeAutomation:
    @staticmethod
    def fetch(database):
        config = Configuration()
        insert = ""
        sql = Sql()
        logger = logging.getLogger("HomeAutomation")

        def get_garage_data():
            fc = FritzConnection(
                address=config.fritz_api_ip(),
                user=config.fritz_api_user(),
                password=config.fritz_api_pass(),
            )
            fh = FritzHomeAutomation(fc)
            return fh.get_device_information_by_identifier(
                config.fritz_garage_solar_ain()
            )

        try:
            garage_solar_socket = get_garage_data()

            garage_temp = garage_solar_socket["NewTemperatureCelsius"] * 0.1
            overall_status = 0
            if garage_solar_socket["NewPresent"] == "CONNECTED":
                overall_status = 1
            garage_power = garage_solar_socket["NewMultimeterPower"] / 100
            insert = sql.generate_solarpanel_insert_stmt(
                garage_temp, overall_status, garage_power
            )
            database.execute(insert)
        except Exception as e:
            logger.error("Error: %s. Cannot get HomeAutomation data." % e)
