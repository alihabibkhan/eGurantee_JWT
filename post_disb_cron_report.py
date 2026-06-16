from imports import *
from application import application


# Add these to your Flask application

@application.route('/api/reports/post-disb-email-runs', methods=['GET'])
@jwt_required()
def api_post_disb_email_runs():
    """Get post disbursement email processor cron runs with date filter"""
    try:
        current_user_id = get_jwt_identity()

        # Check permissions
        if not (is_admin() or is_executive_approver() or
                PermissionHelper.has_permission(current_user_id, "/api/reports/post-disb-email-runs")):
            return jsonify({"error": "Unauthorized access"}), 403

        # Get date parameters from query string
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        # Default to last 30 days if no filter
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch cron runs from database
        runs = get_post_disb_email_processor_runs(start_date, end_date)

        return jsonify({
            "success": True,
            "data": runs
        }), 200

    except Exception as e:
        application.logger.error(f"API error (post-disb-email): {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def get_post_disb_email_processor_runs(start_date, end_date):
    """
    Fetch post disbursement email processor runs from database
    Adjust table and column names according to your database schema
    """
    try:
        query = f"""
            SELECT 
                id,
                job_name,
                started_at,
                finished_at,
                status,
                duration_seconds,
                emails_found,
                files_processed,
                new_records_count,
                duplicates_count,
                anomalies_count,
                error_message,
                summary_path,
                anomalies_path
            FROM monitoring.post_disb_email_processor_runs
            WHERE DATE(started_at) BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY started_at DESC
        """

        results = fetch_records(query)

        # Convert datetime objects to string format for JSON serialization
        runs = []
        for row in results:
            run = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    run[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    run[key] = value
            runs.append(run)

        return runs

    except Exception as e:
        print(f"Error in get_post_disb_email_processor_runs: {str(e)}")
        return []