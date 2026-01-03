from datetime import datetime as dt

class Sql():

    def generate_solarpanel_insert_stmt(self, temp, status, power):
        insert_stmt = 'INSERT INTO "solarpanels" ("timestamp","temperature","status","power") VALUES (\'{}\', {}, {}, {});'
        return insert_stmt.format(dt.now(), temp, status, power)

    def generate_zoe_insert_stmt(self, battery_level, total_mileage):
        insert_stmt = 'INSERT INTO "zoe" ("timestamp","battery_level","total_mileage") VALUES (\'{}\', {}, {});'
        return insert_stmt.format(dt.now(), battery_level, total_mileage)

    def generate_solarpanel_index_stmt(self):
        return 'CREATE INDEX IF NOT EXISTS solarpanels_index ON solarpanels (timestamp);'

    def generate_zoe_index_stmt(self):
        return 'CREATE INDEX IF NOT EXISTS zoe_index ON zoe (timestamp);'

    def generate_zoe_table_stmt(self):
        return 'CREATE TABLE IF NOT EXISTS "zoe" ("id" BIGSERIAL NOT NULL,"timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,"battery_level" FLOAT NOT NULL,"total_mileage" FLOAT NOT NULL,PRIMARY KEY ("id"));'

    def generate_solarpanel_table_stmt(self):
        return 'CREATE TABLE IF NOT EXISTS "solarpanels" ("id" BIGSERIAL NOT NULL,"timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,"temperature" FLOAT NOT NULL,"status" INT NOT NULL,"power" FLOAT NOT NULL,PRIMARY KEY ("id"));'

    def generate_solarpanel_cleanup_stmt(self):
        return 'DELETE FROM solarpanels WHERE timestamp < now() - interval \'1 days\';'
    
    def generate_zoe_cleanup_stmt(self):
        return 'DELETE FROM zoe WHERE timestamp < now() - interval \'1 days\';'

    def generate_solarpanel_last_entry_query(self):
        return 'SELECT temperature, power FROM solarpanels ORDER BY "timestamp" DESC LIMIT 1;'

    def generate_solarpanel_all_entries_query(self):
        return 'SELECT temperature, timestamp, power FROM solarpanels WHERE DATE(timestamp) = current_date order by timestamp ASC;'

    def generate_zoe_last_entry_query(self):
        return 'SELECT battery_level, total_mileage FROM zoe ORDER BY "timestamp" DESC LIMIT 1;'

    def generate_e320_insert_stmt(self, e_in, e_out, power):
        insert_stmt = 'INSERT INTO "e320" ("timestamp","e_in","e_out","power") VALUES (\'{}\', {}, {}, {});'
        return insert_stmt.format(dt.now(), e_in, e_out, power)

    def generate_e320_table_stmt(self):
        return 'CREATE TABLE IF NOT EXISTS "e320" ("id" BIGSERIAL NOT NULL,"timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,"e_in" FLOAT NOT NULL,"e_out" FLOAT NOT NULL,"power" FLOAT NOT NULL,PRIMARY KEY ("id"));'

    def generate_e320_index_stmt(self):
        return 'CREATE INDEX IF NOT EXISTS e320_index ON e320 (timestamp);'

    def generate_e320_cleanup_stmt(self):
        return 'DELETE FROM e320 WHERE timestamp < now() - interval \'1 days\';'

    def generate_e320_last_entry_query(self):
        return 'SELECT e_in, e_out, power FROM e320 ORDER BY "timestamp" DESC LIMIT 1;'

    def generate_e320_all_entries_query(self):
        return 'SELECT timestamp, e_in, e_out, power FROM e320 WHERE DATE(timestamp) = current_date order by timestamp ASC;'

    def generate_phone_calls_insert_stmt(self, call_id, caller_number, caller_name, call_date, call_duration):
        insert_stmt = 'INSERT INTO "phone_calls" ("timestamp","call_id","caller_number","caller_name","call_date","call_duration") VALUES (\'{}\', {}, \'{}\', \'{}\', \'{}\', \'{}\');'
        return insert_stmt.format(dt.now(), call_id, caller_number, caller_name, call_date, call_duration)

    def generate_phone_calls_table_stmt(self):
        return 'CREATE TABLE IF NOT EXISTS "phone_calls" ("id" BIGSERIAL NOT NULL,"timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,"call_id" INTEGER NOT NULL,"caller_number" VARCHAR(50),"caller_name" VARCHAR(100),"call_date" VARCHAR(50),"call_duration" VARCHAR(20),PRIMARY KEY ("id"));'

    def generate_phone_calls_index_stmt(self):
        return 'CREATE INDEX IF NOT EXISTS phone_calls_index ON phone_calls (timestamp);'

    def generate_phone_calls_cleanup_stmt(self):
        return 'DELETE FROM phone_calls WHERE timestamp < now() - interval \'7 days\';'

    def generate_phone_calls_last_entry_query(self):
        return 'SELECT caller_number, caller_name, call_date, call_duration FROM phone_calls ORDER BY "timestamp" DESC LIMIT 1;'

    def generate_phone_calls_all_entries_query(self):
        return 'SELECT timestamp, caller_number, caller_name, call_date, call_duration FROM phone_calls WHERE DATE(timestamp) = current_date order by timestamp ASC;'