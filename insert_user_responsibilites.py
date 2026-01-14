import pandas as pd
import datetime
import re
from imports import *

# Valid values for validation
VALID_ROLES = {
    'Trustee', 'Director', 'Board Observer', 'Associate Director', 'Ex-Officio'
}
VALID_RESPONSIBILITIES = {
    'Trust Chairman', 'Trust Secretary', 'BOD Chairman', 'BOD Secretary',
    'Cluster Lead', 'Operation Manager', 'Regional Supervisor', 'Regional Manager',
    'Committee Lead', 'Committee Member', 'QRM Coordinator', 'Trust Treasurer'
}
VALID_COMMITTEES = {
    'Executive Committee', 'Gilgit Baltistan Committee', 'Chitral Committee',
    'South-Central Committee', 'Risk Management Committee', 'Finance Committee',
    'Information Technology Committee', 'Program Impact Committee'
}

def sanitize_sql_string(value):
    """Basic sanitization to prevent SQL injection."""
    # Remove dangerous characters and escape single quotes
    value = re.sub(r'[\'";]', '', value)
    return value.replace("'", "''")

def get_user_id(email):
    """Fetch user_id from tbl_users using email."""
    email = sanitize_sql_string(email)
    query = f"SELECT user_id FROM tbl_users WHERE email = '{email}'"
    result = fetch_records(query)
    if not result:
        raise ValueError(f"No user found with email: {email}")
    return result[0]['user_id'] if isinstance(result[0], dict) else result[0][0]

def generate_insert_query(row, created_by=12, modified_by=12, current_datetime='2025-10-04 20:59:00'):
    """Generate SQL INSERT query for a single row."""
    # Validate and map fields
    email = row['Email']
    role = row['Role']
    responsibility = row['Responsibility']
    committee = row['Committee']

    # Check for empty or NaN values in Role, Responsibility, or Committee
    if (pd.isna(email) or not str(email).strip() or
        pd.isna(role) or not str(role).strip() or
        pd.isna(responsibility) or not str(responsibility).strip() or
        pd.isna(committee) or not str(committee).strip()):
        print(f"Skipping row for email {email}: Role, Responsibility, or Committee is empty or NaN")
        return None

    email = str(email).strip()
    role = str(role).strip()
    responsibility = str(responsibility).strip()
    committee = str(committee).strip()

    print(f'email: {email}, role: {role}, responsibility: {responsibility}, committee: {committee}')

    # Fetch user_id
    user_id = get_user_id(email)
    print(f'user_id: {user_id}')

    # Validate role
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid Role value '{role}' for email {email}. Must be one of {VALID_ROLES}")

    # Validate responsibility
    if responsibility not in VALID_RESPONSIBILITIES:
        raise ValueError(f"Invalid Responsibility value '{responsibility}' for email {email}. Must be one of {VALID_RESPONSIBILITIES}")

    # Validate committee
    if committee not in VALID_COMMITTEES:
        raise ValueError(f"Invalid Committee value '{committee}' for email {email}. Must be one of {VALID_COMMITTEES}")

    # Handle status
    status = row.get('Status', 1)
    try:
        status = int(status)
        if status not in [0, 1]:
            status = 1  # Default to 1 if invalid
    except (ValueError, TypeError):
        status = 1

    # Sanitize strings for SQL
    role = sanitize_sql_string(role)
    responsibility = sanitize_sql_string(responsibility)
    committee = sanitize_sql_string(committee)

    # Generate SQL query
    query = (
        f"INSERT INTO tbl_user_privileges (user_id, role, responsibility, committee, status, created_by, created_date, modified_by, modified_date) "
        f"VALUES ({user_id}, '{role}', '{responsibility}', '{committee}', {status}, {created_by}, '{current_datetime}', {modified_by}, '{current_datetime}');"
    )
    return query

def read_excel_and_generate_queries(excel_file):
    """Read Excel file and generate SQL INSERT queries."""
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)

        # Validate required columns
        required_columns = ['Email', 'Role', 'Responsibility', 'Committee']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Excel file must contain columns: {required_columns}")

        # Generate SQL queries
        queries = []
        for index, row in df.iterrows():
            try:
                query = generate_insert_query(row)
                if query:  # Only append if query is not None
                    queries.append(query)
            except Exception as e:
                print(f"Error processing row {index + 2}: {e}")

        return queries

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def main():
    excel_file = 'valunteer_responsibilities.xlsx'  # Corrected file name
    queries = read_excel_and_generate_queries(excel_file)

    # Print or save queries
    for query in queries:
        print(query)

    # Save to a file
    with open('insert_user_privileges.sql', 'w') as f:
        for query in queries:
            f.write(query + '\n')

if __name__ == '__main__':
    main()