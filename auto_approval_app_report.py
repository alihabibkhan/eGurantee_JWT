from imports import *
from application import application


@application.route('/api/reports/auto-approval-log', methods=['GET'])
@jwt_required()
def api_auto_approval_log():
    """Get auto approval log with date filter"""
    try:
        current_user_id = get_jwt_identity()

        # Check permissions
        if not (is_admin() or is_executive_approver()):
            return jsonify({"error": "Unauthorized access"}), 403

        start_date = request.args.get('start')
        end_date = request.args.get('end')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        logs = get_auto_approval_log(start_date, end_date)

        return jsonify({
            "success": True,
            "data": logs
        }), 200

    except Exception as e:
        application.logger.error(f"API error (auto-approval-log): {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def get_auto_approval_log(start_date, end_date):
    query = f"""
        SELECT 
            log_id,
            record_id,
            module,
            application_no,
            cnic,
            borrower_name,
            branch_name,
            loan_amount,
            gender,
            approval_type,
            approved_by,
            approved_date,
            status,
            remarks,
            created_date
        FROM tbl_auto_approval_log
        WHERE DATE(created_date) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY created_date DESC
    """
    records = fetch_records(query)

    # Convert datetime objects to string format
    logs = []
    for row in records:
        log = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                log[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                log[key] = value
        logs.append(log)

    return logs