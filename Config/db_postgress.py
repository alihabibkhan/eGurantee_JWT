import psycopg2
from psycopg2 import Error
import time
from typing import Optional, List, Dict, Tuple, Union
import traceback
import os

POSTGRES_CONNECTION = os.getenv('POSTGRES_CONNECTION')


def db_connection():
    connection = None
    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            if attempt == 1:
                print(f"Connection attempt {attempt} started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            connection = psycopg2.connect(
                dsn=str(POSTGRES_CONNECTION)
            )

            if attempt == 1:
                print(f"Connection successful at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return connection

        except (Exception, Error) as error:
            print(f"Error while connecting to PostgreSQL (Attempt {attempt}/{max_attempts}): {error}")
            attempt += 1
            if attempt <= max_attempts:
                time.sleep(2)  # Wait 2 seconds before retrying
            if attempt > max_attempts:
                print(f"Failed to connect after {max_attempts} attempts")
                raise Exception("Database connection failed")
        finally:
            if attempt == max_attempts and connection is not None:
                connection.close()

    return None


def fetch_records(
        query: str,
        params: Union[Tuple, List, Dict, None] = None,
        is_print: bool = False
) -> List[Dict]:
    """
    Execute a SELECT query with optional parameters and return results as list of dicts.

    Args:
        query: SQL query string (use placeholders: %s for psycopg2/mysql, ? for sqlite)
        params: Parameters to safely bind (tuple, list, or dict depending on DB driver)
               Pass None or () if no parameters
        is_print: Whether to print debug timing/info

    Returns:
        List of dictionaries (each row as dict with column names as keys)
    """
    connection = None
    cursor = None
    results = []

    try:
        if is_print:
            print(f"Connection start at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Query:", query)
            if params:
                print("Params:", params)

        connection = db_connection()
        cursor = connection.cursor()

        # Execute with parameters if provided, otherwise plain execute
        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        records = cursor.fetchall()

        for record in records:
            result_dict = dict(zip(columns, record))
            results.append(result_dict)

        if is_print:
            print(f"Query execution completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Rows returned: {len(results)}")

        return results

    except (Exception, Error) as error:
        print(f"Error while fetching records: {error}")
        print(f"Query was: {query}")
        if params:
            print(f"Params were: {params}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            if is_print:
                print(f"Connection closed at {time.strftime('%Y-%m-%d %H:%M:%S')}")


def execute_command(
        query: str,
        params: Union[Tuple, List, Dict, None] = None,
        is_print: bool = False
) -> Optional[int]:
    """
    Execute an INSERT, UPDATE, DELETE or other modifying SQL command with optional parameters.

    Args:
        query: SQL command string (use placeholders: %s for psycopg2/mysql, ? for sqlite)
        params: Parameters to safely bind (tuple, list, or dict). Pass None or () if none.
        is_print: Whether to print debug information

    Returns:
        Optional[int]: For INSERT queries - the last inserted ID (if supported),
                       otherwise None on success or None + error on failure
    """
    connection = None
    cursor = None
    last_insert_id = None

    try:
        if is_print:
            print(f"Connection start at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Executing query:")
            print(query)
            if params:
                print("Parameters:", params)

        connection = db_connection()
        cursor = connection.cursor()

        # Execute with parameters if provided
        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        connection.commit()

        # Try to get last inserted ID only for INSERT statements
        # (you can make this more precise by checking query type if needed)
        query_lower = query.strip().lower()
        if query_lower.startswith('insert'):
            # PostgreSQL style with LASTVAL() — common pattern
            # For MySQL use cursor.lastrowid
            # For SQLite use cursor.lastrowid
            try:
                # Option 1: PostgreSQL (LASTVAL)
                cursor.execute("SELECT LASTVAL()")
                last_insert_id = cursor.fetchone()[0]
            except Exception as inner_e:
                # Option 2: Fallback for MySQL / SQLite style drivers
                if hasattr(cursor, 'lastrowid') and cursor.lastrowid:
                    last_insert_id = cursor.lastrowid
                else:
                    print("Warning: Could not retrieve last insert ID:", str(inner_e))

        if is_print:
            print(f"Query execution completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            if last_insert_id is not None:
                print(f"Last inserted ID: {last_insert_id}")

        return last_insert_id

    except (Exception, Error) as error:
        print("❌ Error while executing SQL command.")
        print(f"  ➤ Error Message: {error}")
        print("  ➤ Traceback:")
        traceback.print_exc()

        if params:
            print("  ➤ Parameters were:", params)

        print("  ➤ Query:")
        print("    " + query)

        if connection:
            connection.rollback()

        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            if is_print:
                print(f"Connection closed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
