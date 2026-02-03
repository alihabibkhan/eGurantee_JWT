from imports import *
from application import application


@application.route('/api/bank-details', methods=['GET'])
@jwt_required()
def api_get_all_bank_details():
    try:
        # Add your user role validation here
        if not (is_admin() or is_executive_approver()):
            return jsonify({'error': 'Unauthorized access'}), 403

        banks = get_all_bank_details()  # Your existing function
        return jsonify({'banks': banks}), 200
    except Exception as e:
        print('API get bank details exception:', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/bank-entries', methods=['GET'])
@jwt_required()
def api_get_all_bank_entries():
    try:
        if not (is_admin() or is_executive_approver()):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Optional: Add filters from query parameters
        bank_id = request.args.get('bank_id')
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')
        general_ledger = request.args.get('general_ledger')
        narration = request.args.get('narration')
        inst_no = request.args.get('inst_no')

        # Build query with filters
        entries = get_filtered_bank_entries(
            bank_id=bank_id,
            date_start=date_start,
            date_end=date_end,
            general_ledger=general_ledger,
            narration=narration,
            inst_no=inst_no
        )

        return jsonify({'entries': entries}), 200
    except Exception as e:
        print('API get bank entries exception:', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/bank-entries', methods=['POST'])
@jwt_required()
def api_add_bank_entry():
    try:
        if not (is_admin() or is_executive_approver()):
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()

        # Validation
        required_fields = ['bank_id', 'date_posted', 'general_ledger']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        # Add your existing validation logic here
        check_query = f"SELECT bank_id FROM tbl_bank_details WHERE bank_id = {data['bank_id']} AND status = '1'"
        bank_exists = fetch_records(check_query)
        if not bank_exists:
            return jsonify({'error': 'Invalid bank ID'}), 400

        # Calculate balance based on previous entries
        withdrawal = float(data.get('withdrawal', 0) or 0)
        deposit = float(data.get('deposit', 0) or 0)

        # Get previous balance
        prev_balance_query = f"""
            SELECT balance FROM tbl_bank_entry_management 
            WHERE bank_id = {data['bank_id']} 
            AND date_posted < '{data['date_posted']}'
            AND status = '1'
            ORDER BY date_posted DESC 
            LIMIT 1
        """
        prev_record = fetch_records(prev_balance_query)
        prev_balance = float(prev_record[0]['balance']) if prev_record else 0

        balance = prev_balance + deposit - withdrawal

        query = f"""
            INSERT INTO tbl_bank_entry_management (
                bank_id, date_posted, mode, general_ledger, nature_of_transaction, 
                narration, inst_no, withdrawal, deposit, balance, date_reconciled, 
                status, created_by, created_date, modified_by, modified_date
            ) VALUES (
                {data['bank_id']}, '{data['date_posted']}', '', '{data['general_ledger']}', '', 
                '{data.get('narration', '')}', '{data.get('inst_no', '')}', 
                {withdrawal}, {deposit}, {balance}, 
                '{datetime.now().strftime('%Y-%m-%d')}', '1', 
                {get_current_user_id()}, 
                '{datetime.now()}', 
                {get_current_user_id()}, 
                '{datetime.now()}'
            ) RETURNING bank_entry_id
        """

        result = execute_command(query)

        if result:
            return jsonify({
                'message': 'Bank entry added successfully',
                'bank_entry_id': result
            }), 201
        else:
            return jsonify({'error': 'Failed to add bank entry'}), 500

    except Exception as e:
        print('API add bank entry exception:', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/bank-entries/<int:bank_entry_id>', methods=['PUT'])
@jwt_required()
def api_update_bank_entry(bank_entry_id):
    try:
        if not (is_admin() or is_executive_approver()):
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()

        # Check if entry exists
        check_query = f"SELECT bank_entry_id FROM tbl_bank_entry_management WHERE bank_entry_id = {bank_entry_id}"
        entry_exists = fetch_records(check_query)
        if not entry_exists:
            return jsonify({'error': 'Bank entry not found'}), 404

        # Recalculate balance
        withdrawal = float(data.get('withdrawal', 0) or 0)
        deposit = float(data.get('deposit', 0) or 0)

        # Get previous balance (excluding current entry)
        prev_balance_query = f"""
            SELECT balance FROM tbl_bank_entry_management 
            WHERE bank_id = {data['bank_id']} 
            AND date_posted < '{data['date_posted']}'
            AND bank_entry_id != {bank_entry_id}
            AND status = '1'
            ORDER BY date_posted DESC 
            LIMIT 1
        """
        prev_record = fetch_records(prev_balance_query)
        prev_balance = float(prev_record[0]['balance']) if prev_record else 0

        balance = prev_balance + deposit - withdrawal

        query = f"""
            UPDATE tbl_bank_entry_management
            SET bank_id = {data['bank_id']}, 
                date_posted = '{data['date_posted']}', 
                general_ledger = '{data['general_ledger']}', 
                narration = '{data.get('narration', '')}', 
                inst_no = '{data.get('inst_no', '')}', 
                withdrawal = {withdrawal}, 
                deposit = {deposit}, 
                balance = {balance}, 
                modified_by = {get_current_user_id()}, 
                modified_date = '{datetime.now()}'
            WHERE bank_entry_id = {bank_entry_id}
        """

        execute_command(query)

        return jsonify({'message': 'Bank entry updated successfully'}), 200

    except Exception as e:
        print('API update bank entry exception:', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/bank-entries/<int:bank_entry_id>', methods=['DELETE'])
@jwt_required()
def api_delete_bank_entry(bank_entry_id):
    try:
        if not (is_admin() or is_executive_approver()):
            return jsonify({'error': 'Unauthorized access'}), 403

        check_query = f"SELECT bank_entry_id FROM tbl_bank_entry_management WHERE bank_entry_id = {bank_entry_id}"
        entry_exists = fetch_records(check_query)
        if not entry_exists:
            return jsonify({'error': 'Bank entry not found'}), 404

        query = f"""
            UPDATE tbl_bank_entry_management
            SET status = '2',
                modified_by = {get_current_user_id()},
                modified_date = '{datetime.now()}'
            WHERE bank_entry_id = {bank_entry_id}
        """

        execute_command(query)

        return jsonify({'message': 'Bank entry deleted successfully'}), 200

    except Exception as e:
        print('API delete bank entry exception:', str(e))
        return jsonify({'error': 'Server error'}), 500


# Helper function to get filtered entries
def get_filtered_bank_entries(bank_id=None, date_start=None, date_end=None,
                              general_ledger=None, narration=None, inst_no=None):
    base_query = """
                 SELECT * \
                 FROM tbl_bank_entry_management
                 WHERE status = '1' \
                 """

    conditions = []
    params = []

    if bank_id:
        conditions.append("bank_id = %s")
        params.append(bank_id)

    if date_start:
        conditions.append("date_posted >= %s")
        params.append(date_start)

    if date_end:
        conditions.append("date_posted <= %s")
        params.append(date_end)

    if general_ledger:
        conditions.append("general_ledger = %s")
        params.append(general_ledger)

    if narration:
        conditions.append("narration ILIKE %s")
        params.append(f"%{narration}%")

    if inst_no:
        conditions.append("inst_no ILIKE %s")
        params.append(f"%{inst_no}%")

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    base_query += " ORDER BY date_posted DESC"

    # Execute query with params
    return fetch_records(base_query, tuple(params))