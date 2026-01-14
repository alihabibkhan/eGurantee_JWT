import psycopg2
from psycopg2 import Error
import time
from typing import List, Dict, Optional
import traceback
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

POSTGRES_CONNECTION = 'postgresql://neondb_owner:npg_3cqWiumCMK9O@ep-cool-mode-a8w2qohv-pooler.eastus2.azure.neon.tech/eguarantee_db?sslmode=require&channel_binding=require'

def db_connection():
    connection = None
    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            if attempt == 1:
                logger.info(f"Connection attempt {attempt} started")

            connection = psycopg2.connect(
                dsn=str(POSTGRES_CONNECTION)
            )

            if attempt == 1:
                logger.info("Connection successful")
            return connection

        except (Exception, Error) as error:
            logger.error(f"Error while connecting to PostgreSQL (Attempt {attempt}/{max_attempts}): {error}")
            attempt += 1
            if attempt <= max_attempts:
                time.sleep(2)  # Wait 2 seconds before retrying
            if attempt > max_attempts:
                logger.error(f"Failed to connect after {max_attempts} attempts")
                raise Exception("Database connection failed")
        finally:
            if attempt == max_attempts and connection is not None:
                connection.close()

    return None

def fetch_records(query: str, is_print: bool = False) -> List[Dict]:
    connection = None
    cursor = None
    results = []

    try:
        if is_print:
            logger.info("Connection start")
            logger.debug(f"Query: {query}")

        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        records = cursor.fetchall()

        for record in records:
            result_dict = dict(zip(columns, record))
            results.append(result_dict)

        if is_print:
            logger.info("Query execution completed")

        return results

    except (Exception, Error) as error:
        logger.error(f"Error while fetching records: {error}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            if is_print:
                logger.info("Connection closed")

def execute_command(query: str, is_print: bool = False) -> Optional[int]:
    connection = None
    cursor = None
    last_insert_id = None

    try:
        if is_print:
            logger.info("Connection start")
            logger.debug("Executing query:")
            logger.debug(query)

        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(query)
        connection.commit()

        if query.strip().lower().startswith('insert'):
            cursor.execute("SELECT LASTVAL()")
            last_insert_id = cursor.fetchone()[0]

        if is_print:
            logger.info("Query execution completed")

        return last_insert_id

    except (Exception, Error) as error:
        logger.error("Error while executing SQL command")
        logger.error(f"Error Message: {error}")
        logger.error("Traceback:", exc_info=True)

        # Log query for inspection
        logger.debug("Query snippet for inspection:")
        query_lines = query.strip().split(',')
        for i, line in enumerate(query_lines):
            logger.debug(f"[{i+1}] {line.strip()}")

        if connection:
            connection.rollback()
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            if is_print:
                logger.info("Connection closed")