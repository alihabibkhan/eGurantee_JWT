import pandas as pd
from datetime import datetime

def escape_sql_string(value):
    """Escape single quotes in SQL string values."""
    if value is None or pd.isna(value):
        return 'NULL'
    # Perform replacement outside f-string to avoid backslashes in expression
    escaped_value = str(value).replace("'", "''")
    return f"'{escaped_value}'"

def format_date(date):
    """Format date to YYYY-MM-DD for SQL."""
    if pd.isna(date):
        return 'NULL'
    if isinstance(date, str):
        try:
            # Parse string to datetime
            parsed_date = pd.to_datetime(date)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            return 'NULL'
    elif isinstance(date, pd.Timestamp) or isinstance(date, datetime):
        return date.strftime('%Y-%m-%d')
    return 'NULL'

def format_number(value):
    """Format numeric value to preserve decimal places."""
    if pd.isna(value):
        return '0.00'
    try:
        # Convert to float and format to 2 decimal places
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return '0.00'

def generate_insert_queries(excel_file, output_file='insert_bank_entries.sql'):
    """
    Read Excel file and generate PostgreSQL INSERT queries for tbl_bank_entry_management.

    Args:
        excel_file (str): Path to the Excel file.
        output_file (str): Path to save the generated SQL queries.
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)

        # Normalize column names (remove spaces, convert to lowercase for comparison)
        df.columns = [col.strip().lower() for col in df.columns]
        expected_columns = ['date posted', 'general ledger', 'narration', 'inst. no.', 'withdrawal', 'deposit', 'balance']

        # Check for required columns
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in Excel: {', '.join(missing_cols)}")

        # Current date for date_reconciled, created_date, modified_date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Initialize SQL queries list
        queries = []

        # Generate INSERT query for each row
        for index, row in df.iterrows():
            # Get values with defaults for missing or NaN values
            date_posted = format_date(row['date posted'])
            general_ledger = escape_sql_string(row['general ledger'])
            narration = escape_sql_string(row['narration'])
            inst_no = escape_sql_string(row['inst. no.'])
            withdrawal = format_number(row['withdrawal'])
            deposit = format_number(row['deposit'])
            balance = format_number(row['balance'])

            # Validate required fields
            if date_posted == 'NULL':
                print(f"Warning: Skipping row {index + 2} due to invalid date_posted")
                continue
            if general_ledger == 'NULL':
                print(f"Warning: Skipping row {index + 2} due to missing general_ledger")
                continue

            # Generate INSERT query
            query = f"""
            INSERT INTO tbl_bank_entry_management (
                bank_id, date_posted, mode, general_ledger, nature_of_transaction,
                narration, inst_no, withdrawal, deposit, balance, date_reconciled,
                status, created_by, created_date, modified_by, modified_date
            ) VALUES (
                1, '{date_posted}', '', {general_ledger}, '',
                {narration}, {inst_no}, {withdrawal}, {deposit}, {balance}, '{current_date}',
                1, 1, '{current_date}', 1, '{current_date}'
            ) RETURNING bank_entry_id;
            """
            queries.append(query)

        # Write queries to output file
        with open(output_file, 'w') as f:
            for query in queries:
                f.write(query + '\n')

        print(f"Generated {len(queries)} INSERT queries and saved to {output_file}")

    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        raise

if __name__ == '__main__':
    # Example usage
    excel_file_path = 'Bank Statement of Account.xlsx'  # Replace with your Excel file path
    try:
        generate_insert_queries(excel_file_path)
    except Exception as e:
        print(f"Failed to generate queries: {str(e)}")