#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
from urllib.request import urlopen
from library.sql import Sql


class E320():

    @staticmethod
    def fetch(database):
        sql = Sql()
        logger = logging.getLogger("E320")
        try:
            with urlopen("http://192.168.178.79/cm?cmnd=status+10") as response:
                data = json.loads(response.read().decode("utf-8"))
                
                e_in = data['StatusSNS']['E320']['E_in']
                e_out = data['StatusSNS']['E320']['E_out']
                power = data['StatusSNS']['E320']['Power']
                
                insert_stmt = sql.generate_e320_insert_stmt(e_in, e_out, power)
                database.execute(insert_stmt)
        except Exception as e:
            logger.error("Error: %s. Cannot get E320 data." % e)