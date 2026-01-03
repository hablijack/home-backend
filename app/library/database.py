#!/usr/bin/python3
# -*- coding: utf-8 -*-

import psycopg2
from library.sql import Sql
import logging
from library.Configuration import Configuration

class Database():

    def __init__(self):
        self.config = Configuration()
        self.conn = psycopg2.connect(
            host=self.config.postgres_host(),
            port=5433, 
            dbname=self.config.postgres_db(), 
            user=self.config.postgres_user(), 
            password=self.config.postgres_password(), 
            target_session_attrs="read-write"
        )

    def execute(self, insert_statement):
        cur = self.conn.cursor()
        try:
            cur.execute(insert_statement)
            self.conn.commit()
        except Exception as error:
            print(f"Error: '{error}'")
            self.conn.rollback()
        finally:
            cur.close()
    
    def read(self, select_statement):
        cur = None
        records = None
        try:
            cur = self.conn.cursor()
            cur.execute(select_statement)
            records = cur.fetchall()
        except Exception as error:
            print(f"Error: '{error}'")
            self.conn.rollback()
            records = None
        finally:
            if cur:
                cur.close()
            return records
            

    @staticmethod
    def cleanup(database):
        sql = Sql()
        logger = logging.getLogger("Database")
        try:
            cleanup_statement = sql.generate_solarpanel_cleanup_stmt()
            database.execute(cleanup_statement)
            cleanup_statement = sql.generate_zoe_cleanup_stmt()
            database.execute(cleanup_statement)
            cleanup_statement = sql.generate_e320_cleanup_stmt()
            database.execute(cleanup_statement)
            cleanup_statement = sql.generate_phone_calls_cleanup_stmt()
            database.execute(cleanup_statement)
            cleanup_statement = sql.generate_phone_calls_cleanup_stmt()
            database.execute(cleanup_statement)
        except Exception as error:
            logger.error(f"Error: '{error}'")

    @staticmethod
    def initialize_tables(database):
        sql = Sql()
        logger = logging.getLogger("Database")
        try:
            table_statement = sql.generate_solarpanel_table_stmt()
            database.execute(table_statement)
            index_statement = sql.generate_solarpanel_index_stmt()
            database.execute(index_statement)
            
            table_statement = sql.generate_zoe_table_stmt()
            database.execute(table_statement)
            index_statement = sql.generate_zoe_index_stmt()
            database.execute(index_statement)
            
            table_statement = sql.generate_e320_table_stmt()
            database.execute(table_statement)
            index_statement = sql.generate_e320_index_stmt()
            database.execute(index_statement)
            
            table_statement = sql.generate_phone_calls_table_stmt()
            database.execute(table_statement)
            index_statement = sql.generate_phone_calls_index_stmt()
            database.execute(index_statement)
            
            logger.info("Database tables initialized successfully")
        except Exception as error:
            logger.error(f"Error initializing tables: '{error}'")