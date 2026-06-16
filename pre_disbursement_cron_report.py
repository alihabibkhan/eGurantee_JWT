from imports import *
from application import application


# Add these to your Flask application file (e.g., application.py or routes.py)

# ====================== PRE-DISBURSEMENT CRON REPORT APIs ======================

@application.route('/api/reports/pre-disbursement-runs', methods=['GET'])
@jwt_required()
def api_pre_disbursement_runs():
    """Get pre-disbursement cron job runs with date filter"""
    try:
        current_user_id = get_jwt_identity()

        # Check permissions
        if not (is_admin() or is_executive_approver()):
            return jsonify({"error": "Unauthorized access"}), 403

        # Get date parameters from query string
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        # Optional: default to last 30 days if no filter
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Fetch cron runs from database
        runs = get_pre_disb_processor_runs(start_date, end_date)

        return jsonify({
            "success": True,
            "data": runs,
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            }
        }), 200

    except Exception as e:
        application.logger.error(f"API error (pre-disbursement runs): {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def get_pre_disb_processor_runs(start_date, end_date):
    """
    Fetch pre-disbursement processor runs from database
    This function should be implemented based on your database schema
    """
    try:
        # Example query - adjust table and column names according to your database
        query = f"""
            SELECT 
                id, started_at, finished_at, status, duration_seconds,
                emails_found, files_processed, new_records_count,
                duplicates_count, anomalies_count,
                summary_path, anomalies_path, error_message,
                created_at
            FROM monitoring.pre_disb_email_processor_runs
            WHERE started_at >= '{start_date}' AND started_at <= '{end_date + " 23:59:59"}'
            ORDER BY started_at DESC
        """

        results = fetch_records(query)

        # Convert to list of dictionaries with proper formatting
        runs = []
        for row in results:
            run = {
                'started_at': row.get('started_at'),
                'finished_at': row.get('finished_at'),
                'status': row.get('status', 'unknown'),
                'duration_seconds': row.get('duration_seconds'),
                'emails_found': row.get('emails_found', 0),
                'files_processed': row.get('files_processed', 0),
                'new_records_count': row.get('new_records_count', 0),
                'duplicates_count': row.get('duplicates_count', 0),
                'anomalies_count': row.get('anomalies_count', 0),
                'summary_path': row.get('summary_path'),
                'anomalies_path': row.get('anomalies_path'),
                'error_message': row.get('error_message')
            }
            runs.append(run)

        return runs

    except Exception as e:
        print(f"Error fetching pre-disbursement runs: {str(e)}")
        return []


# Optional: Add an endpoint to download files
@application.route('/api/reports/download/<path:file_path>', methods=['GET'])
@jwt_required()
def api_download_report_file(file_path):
    """Download summary or anomalies report file"""
    try:
        current_user_id = get_jwt_identity()

        # Check permissions
        if not (is_admin() or is_executive_approver()):
            return jsonify({"error": "Unauthorized access"}), 403

        # Security: Ensure file path is within allowed directory
        import os
        base_dir = os.path.join(os.path.dirname(__file__), 'reports')
        full_path = os.path.abspath(os.path.join(base_dir, file_path))

        # Check if path is within base directory (prevent directory traversal)
        if not full_path.startswith(base_dir):
            return jsonify({"error": "Invalid file path"}), 400

        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        # Return file
        from flask import send_file
        return send_file(full_path, as_attachment=True)

    except Exception as e:
        application.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": str(e)}), 500