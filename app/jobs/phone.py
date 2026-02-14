#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from library.fritzbox import Fritzbox
from library.sql import Sql


class Phone():

    @staticmethod
    def fetch(database):
        sql = Sql()
        logger = logging.getLogger("Phone")
        try:
            fbox = Fritzbox()
            
            # Fetch all calls from Fritzbox API
            all_calls = fbox.get_call_history()
            last_known_id = 0
            
            # Get the last known call ID from database to avoid duplicates
            last_call_query = 'SELECT call_id FROM phone_calls ORDER BY "timestamp" DESC LIMIT 1;'
            records = database.read(last_call_query)
            if records and len(records) > 0:
                last_known_id = records[0][0]
            
            # Process all calls from the API
            for call in all_calls:
                # Only process new calls that we haven't seen before
                if call['id'] > last_known_id:
                    # Check if this specific call ID already exists in database
                    check_query = f"SELECT call_id FROM phone_calls WHERE call_id = {call["id"]};"
                    existing_records = database.read(check_query)
                    
                    # Only insert if this call ID doesn't already exist
                    if not existing_records or len(existing_records) == 0:
                        # Perform reverse lookup if name is not available
                        if (call['name'] is None and call['caller']) or (len(call['name']) == 0 and call['caller']):
                            call['name'] = Fritzbox.telefonbuch_reverse_lookup(call['caller'])
                        
                        # Persist the call to database
                        insert_stmt = sql.generate_phone_calls_insert_stmt(
                            call['id'],
                            call['caller'] if call['caller'] else '',
                            call['name'] if call['name'] else '',
                            call['date'],
                            call['duration']
                        )
                        database.execute(insert_stmt)
                    
        except Exception as e:
            logger.error("Error: %s. Cannot get Fritzbox phone data." % e)