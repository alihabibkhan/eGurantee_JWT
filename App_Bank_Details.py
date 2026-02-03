from imports import *
from application import application


@application.route('/api/bank-details', methods=['GET'])
@jwt_required()
def get_all_bank_details_api():
    """Get all bank details"""
    try:
        bank_details = get_all_bank_details()
        return jsonify({
            'success': True,
            'data': bank_details
        }), 200
    except Exception as e:
        print('Get all bank details exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to fetch bank details'
        }), 500


@application.route('/api/bank-details/<int:bank_id>', methods=['GET'])
@jwt_required()
def get_bank_detail_api(bank_id):
    """Get specific bank detail by ID"""
    try:
        query = f"""
            SELECT bank_id, bank_name, currency, date_account_opened, bank_code, 
                   branch_of_account, IBAN, account_title, date_account_closed, status
            FROM tbl_bank_details 
            WHERE bank_id = {bank_id} AND status != 3
        """
        result = fetch_records(query)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Bank detail not found'
            }), 404

        return jsonify({
            'success': True,
            'data': result[0]
        }), 200
    except Exception as e:
        print('Get bank detail exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to fetch bank detail'
        }), 500


@application.route('/api/bank-details', methods=['POST'])
@jwt_required()
def create_bank_detail_api():
    """Create new bank detail"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['bank_code', 'bank_name', 'branch_of_account',
                           'currency', 'IBAN', 'account_title', 'date_account_opened']

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Get form data
        bank_code = data['bank_code']
        bank_name = data['bank_name']
        branch_of_account = data['branch_of_account']
        currency = data['currency']
        IBAN = data['IBAN']
        account_title = data['account_title']
        status = data.get('status', 1)
        date_account_closed = data.get('date_account_closed')
        date_account_opened = data['date_account_opened']

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Escape string inputs
        bank_code_escaped = escape_sql_string(bank_code)
        branch_of_account_escaped = escape_sql_string(branch_of_account)
        IBAN_escaped = escape_sql_string(IBAN)
        account_title_escaped = escape_sql_string(account_title)
        date_account_closed_escaped = escape_sql_string(date_account_closed) if date_account_closed else 'NULL'

        # Insert new record
        query = f"""
            INSERT INTO tbl_bank_details 
            (bank_code, branch_of_account, IBAN, account_title, date_account_closed, 
             status, created_by, created_date, modifed_by, modified_date, 
             currency, date_account_opened, bank_name)
            VALUES ({bank_code_escaped}, {branch_of_account_escaped}, {IBAN_escaped}, 
                    {account_title_escaped}, {date_account_closed_escaped}, 
                    {status}, {current_user_id}, '{current_time}', 
                    {current_user_id}, '{current_time}', '{currency}', 
                    '{date_account_opened}', '{bank_name}')
            RETURNING bank_id
        """

        result = execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Bank detail created successfully',
            'bank_id': result
        }), 201

    except Exception as e:
        print('Create bank detail exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to create bank detail'
        }), 500


@application.route('/api/bank-details/<int:bank_id>', methods=['PUT'])
@jwt_required()
def update_bank_detail_api(bank_id):
    """Update existing bank detail"""
    try:
        # Check if bank detail exists
        check_query = f"""
            SELECT bank_id FROM tbl_bank_details 
            WHERE bank_id = {bank_id} AND status != 3
        """
        existing = fetch_records(check_query)

        if not existing:
            return jsonify({
                'success': False,
                'error': 'Bank detail not found'
            }), 404

        data = request.get_json()

        # Get form data
        bank_code = data['bank_code']
        bank_name = data['bank_name']
        branch_of_account = data['branch_of_account']
        currency = data['currency']
        IBAN = data['IBAN']
        account_title = data['account_title']
        status = data['status']
        date_account_closed = data.get('date_account_closed')
        date_account_opened = data['date_account_opened']

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Escape string inputs
        bank_code_escaped = escape_sql_string(bank_code)
        branch_of_account_escaped = escape_sql_string(branch_of_account)
        IBAN_escaped = escape_sql_string(IBAN)
        account_title_escaped = escape_sql_string(account_title)
        date_account_closed_escaped = escape_sql_string(date_account_closed) if date_account_closed else 'NULL'

        # Update existing record
        query = f"""
            UPDATE tbl_bank_details 
            SET bank_code = {bank_code_escaped},
                bank_name = '{bank_name}', 
                branch_of_account = {branch_of_account_escaped},
                currency = '{currency}',
                IBAN = {IBAN_escaped}, 
                account_title = {account_title_escaped},
                date_account_opened = '{date_account_opened}',
                date_account_closed = {date_account_closed_escaped},
                status = '{status}',
                modifed_by = {current_user_id}, 
                modified_date = '{current_time}'
            WHERE bank_id = {bank_id}
        """

        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Bank detail updated successfully'
        }), 200

    except Exception as e:
        print('Update bank detail exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to update bank detail'
        }), 500


@application.route('/api/bank-details/<int:bank_id>', methods=['DELETE'])
@jwt_required()
def delete_bank_detail_api(bank_id):
    """Soft delete bank detail"""
    try:
        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if bank detail exists
        check_query = f"""
            SELECT bank_id FROM tbl_bank_details 
            WHERE bank_id = {bank_id} AND status != 3
        """
        existing = fetch_records(check_query)

        if not existing:
            return jsonify({
                'success': False,
                'error': 'Bank detail not found'
            }), 404

        query = f"""
            UPDATE tbl_bank_details 
            SET status = 3, 
                modifed_by = {current_user_id}, 
                modified_date = '{current_time}'
            WHERE bank_id = {bank_id}
        """

        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Bank detail deleted successfully'
        }), 200

    except Exception as e:
        print('Delete bank detail exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to delete bank detail'
        }), 500

