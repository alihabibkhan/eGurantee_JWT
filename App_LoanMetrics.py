from imports import *
from application import application


@application.route('/api/manage_loan_metrics', methods=['GET'])
@jwt_required()
def api_manage_loan_metrics():
    """API endpoint to get all loan metrics data for the dashboard"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = {
            'get_all_loan_products': get_all_loan_products(),
            'get_all_occupations': get_all_occupations(),
            'get_all_experience_ranges': get_all_experience_ranges(),
            'get_all_loan_metrics': get_all_loan_metrics(),
            'get_all_branches_info': get_all_branches_info()
        }

        return jsonify({
            'success': True,
            'data': data
        }), 200

    except Exception as e:
        print('api_manage_loan_metrics exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-metrics', methods=['GET'])
@jwt_required()
def api_get_all_loan_metrics():
    """API endpoint to get all loan metrics"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        metrics = get_all_loan_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-metrics/<int:loan_metric_id>', methods=['GET'])
@jwt_required()
def api_get_loan_metric(loan_metric_id):
    """API endpoint to get a single loan metric by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT lm.loan_metric_id, lm.product_id, lp.name as product_name, lp.gender,
                   lm.occupation_id, o.name as occupation_name,
                   lm.experience_id, er.label as experience_label,
                   lm.branch_id, b.branch_name,
                   lm.global_loan_ceiling, lm.repeat_increment, 
                   lm.required_paid_off, lm.interest_rate, 
                   lm.is_active, lm.status,
                   lm.created_by, lm.created_date, lm.modified_by, lm.modified_date
            FROM tbl_loan_metrics lm
            LEFT JOIN tbl_loan_products lp ON lm.product_id = lp.product_id
            LEFT JOIN tbl_occupations o ON lm.occupation_id = o.occupation_id
            LEFT JOIN tbl_experience_ranges er ON lm.experience_id = er.experience_range_id
            LEFT JOIN tbl_branches b ON lm.branch_id = b.branch_id
            WHERE lm.loan_metric_id = '{loan_metric_id}' 
              AND lm.status = '1'
        """
        metric = fetch_records(query)
        metric = metric[0] if metric else None

        if metric:
            return jsonify({
                'success': True,
                'data': {'loan_metric': metric}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Loan metric not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-metrics', methods=['POST'])
@application.route('/api/loan-metrics/<int:loan_metric_id>', methods=['POST'])
@jwt_required()
def api_save_loan_metric(loan_metric_id=None):
    """API endpoint to create or update a loan metric"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        product_id = data.get('product_id')
        occupation_id = data.get('occupation_id')
        experience_id = data.get('experience_id')
        branch_id = data.get('branch_id', '1')  # Default branch ID
        global_loan_ceiling = data.get('global_loan_ceiling')
        repeat_increment = data.get('repeat_increment')
        interest_rate = data.get('interest_rate')
        required_paid_off = data.get('required_paid_off')
        is_active = data.get('is_active', '1')

        current_user_id = str(get_current_user_id())
        current_timestamp = str(datetime.now())

        if loan_metric_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_loan_metrics 
                SET product_id = '{product_id}', 
                    occupation_id = '{occupation_id}', 
                    experience_id = '{experience_id}', 
                    branch_id = '{branch_id}', 
                    global_loan_ceiling = '{global_loan_ceiling}', 
                    repeat_increment = '{repeat_increment}', 
                    interest_rate = '{interest_rate}', 
                    required_paid_off = '{required_paid_off}', 
                    is_active = '{is_active}', 
                    status = '1', 
                    modified_by = '{current_user_id}', 
                    modified_date = '{current_timestamp}'
                WHERE loan_metric_id = '{loan_metric_id}'
            """
            execute_command(update_query)
            message = 'Loan metric updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_loan_metrics (
                    product_id, occupation_id, experience_id, branch_id, 
                    global_loan_ceiling, repeat_increment, required_paid_off, 
                    interest_rate, is_active, status, 
                    created_by, created_date, modified_by, modified_date
                ) VALUES (
                    '{product_id}', '{occupation_id}', '{experience_id}', '{branch_id}', 
                    '{global_loan_ceiling}', '{repeat_increment}', '{required_paid_off}', 
                    '{interest_rate}', '{is_active}', '1', 
                    '{current_user_id}', '{current_timestamp}', 
                    '{current_user_id}', '{current_timestamp}'
                )
            """
            execute_command(insert_query)
            message = 'Loan metric added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_loan_metric exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-metrics/<int:loan_metric_id>', methods=['DELETE'])
@jwt_required()
def api_delete_loan_metric(loan_metric_id):
    """API endpoint to delete a loan metric (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_loan_metrics 
            SET is_active = '0', status = '0'
            WHERE loan_metric_id = '{loan_metric_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Loan metric deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_loan_metric exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500

