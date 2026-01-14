import pandas as pd
from datetime import datetime

# Read Excel file (replace 'input.xlsx' with your Excel file path)
df = pd.read_excel('latest_branches_data.xlsx', dtype={'branch_code': str, 'branch': str})

# Prepare current datetime
current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Prepare SQL insert statements
insert_queries = []

# Iterate through each row in the Excel sheet
for index, row in df.iterrows():
    # Format values, preserving leading zeros
    branch_code = str(row['branch_code']).strip()
    role = str(row['role']).strip()
    branch_name = str(row['branch_name']).strip()
    branch = str(row['branch']).strip()
    area = str(row['area']).strip()
    area_name = str(row['area_name']).strip()
    branch_manager = str(row['branch_manager']).strip()
    email = str(row['Email']).strip()
    live_branch = int(row['live_branch'])

    # Escape single quotes for SQL
    branch_code = branch_code.replace("'", "''")
    role = role.replace("'", "''")
    branch_name = branch_name.replace("'", "''")
    branch = branch.replace("'", "''")
    area = area.replace("'", "''")
    area_name = area_name.replace("'", "''")
    branch_manager = branch_manager.replace("'", "''")
    email = email.replace("'", "''")

    # Create SQL insert query
    query = f"""INSERT INTO tbl_branches (
        branch_code, role, branch_name, branch, area, area_name, branch_manager, email, live_branch,
        bank_id, created_by, created_date, modified_by, modified_date,
        bank_distribution, kft_distribution, national_council_distribution
    ) VALUES (
        '{branch_code}', '{role}', '{branch_name}', '{branch}', '{area}', '{area_name}', '{branch_manager}', '{email}', {live_branch},
        1, 1, '{current_datetime}', 1, '{current_datetime}',
        '', '', ''
    );"""
    insert_queries.append(query)

# Save to SQL file
with open('insert_queries.sql', 'w') as f:
    for query in insert_queries:
        f.write(query + '\n')

# Print SQL queries
for query in insert_queries:
    print(query)