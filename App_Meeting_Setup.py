from application import application
from imports import *


@application.route('/api/meetings/calendar', methods=['GET'])
@jwt_required()
def api_view_meeting_calendar():
    try:
        print(f"[DEBUG] api_view_meeting_calendar - Request received from IP: {request.remote_addr}")

        user_id = get_jwt_identity()  # or get_current_user_id()
        print(f"[DEBUG] api_view_meeting_calendar - User ID from JWT: {user_id}")

        # mandatory_meetings = get_user_committee_meetings_current_month(user_id)
        # print(f"[DEBUG] api_view_meeting_calendar - Retrieved {len(mandatory_meetings) if mandatory_meetings else 0} mandatory meetings for user {user_id}")

        schedule_meetings = get_all_schedule_meetings(user_specific=True)
        print(
            f"[DEBUG] api_view_meeting_calendar - Retrieved {len(schedule_meetings) if schedule_meetings else 0} schedule meetings for user {user_id}")
        if schedule_meetings:
            print(
                f"[DEBUG] api_view_meeting_calendar - First schedule meeting: {schedule_meetings[0] if schedule_meetings else 'None'}")

        print(f"[DEBUG] api_view_meeting_calendar - Preparing JSON response for user {user_id}")
        response = jsonify({
            "success": True,
            "data": {
                # "mandatory_meetings": mandatory_meetings,
                "schedule_meetings": schedule_meetings
            }
        })
        print(f"[DEBUG] api_view_meeting_calendar - JSON response created successfully for user {user_id}")

        return response, 200

    except Exception as e:
        print(f"[ERROR] api_view_meeting_calendar - Exception occurred: {str(e)}")
        print(f"[ERROR] api_view_meeting_calendar - Exception type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] api_view_meeting_calendar - Traceback: {traceback.format_exc()}")

        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/meetings/my', methods=['GET'])
@jwt_required()
def api_view_my_meetings():
    try:
        user_id = get_jwt_identity()
        meetings = get_all_schedule_meetings(user_specific=True)
        return jsonify({
            "success": True,
            "data": {"schedule_meetings": meetings}
        }), 200
    except Exception as e:
        print(f"api_view_my_meetings error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/meetings/schedule', methods=['GET'])
@jwt_required()
def api_view_schedule_meetings():
    try:
        user_id = get_jwt_identity()
        mandatory_meetings = get_user_committee_meetings_current_month()
        return jsonify({
            "success": True,
            "data": {"mandatory_meetings": mandatory_meetings}
        }), 200
    except Exception as e:
        print(f"api_view_schedule_meetings error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/post-meeting-action-items-data', methods=['GET'])
@jwt_required()
def api_post_meeting_action_items_data():
    try:
        meetings = get_all_schedule_meetings()

        priorities = get_all_meeting_action_items_priorities()

        query = """
            SELECT DISTINCT u.user_id, u.name, up.committee 
            FROM tbl_users u
            INNER JOIN tbl_user_privileges up ON up.user_id = u.user_id
        """
        assignees = fetch_records(query)

        statuses = get_all_meeting_action_items_status()

        return jsonify({
            "success": True,
            "data": {
                "schedule_meetings": meetings,
                "priorities": priorities,
                "assignees": assignees,
                "statuses": statuses
            }
        }), 200
    except Exception as e:
        print(f"api_post_meeting_action_items_data error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/action-items/<int:schedule_meeting_id>', methods=['GET'])
@jwt_required()
def api_get_action_items(schedule_meeting_id):
    try:
        query = """
            SELECT pmu.post_meeting_id, pmu.action_items, pmu.target_completion_date, maip.maip_id,
                   maip.maip_name AS priority_name, u.name AS assignee_name, u.user_id as assigne_id,
                   mais.mais_name AS status_name, mais.mais_id, pmu.date_followup, pmu.notes_followup, pmu.date_completed
            FROM tbl_post_meeting_updates pmu
            LEFT JOIN tbl_meeting_action_items_priorities maip ON pmu.action_item_priority = maip.maip_id
            LEFT JOIN tbl_users u ON pmu.assigned_to = u.user_id
            LEFT JOIN tbl_meeting_action_items_status mais ON pmu.action_item_status = mais.mais_id
            WHERE pmu.schedule_meeting_id = %s AND pmu.status = 1
        """
        result = fetch_records(query, (schedule_meeting_id,))
        return jsonify({"success": True, "action_items": result}), 200
    except Exception as e:
        print(f"get_action_items error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/action-item/<int:post_meeting_id>', methods=['GET'])
@jwt_required()
def api_get_action_item(post_meeting_id):
    try:
        query = """
            SELECT post_meeting_id, action_items, action_item_priority,
                   assigned_to, target_completion_date, action_item_status,
                   notes_followup, date_followup, date_completed
            FROM tbl_post_meeting_updates
            WHERE post_meeting_id = %s AND status = 1
        """
        result = fetch_records(query, (post_meeting_id,))
        if result:
            return jsonify({"success": True, "action_item": result[0]}), 200
        return jsonify({"success": False, "message": "Action item not found"}), 404
    except Exception as e:
        print(f"get_action_item error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/action-item', methods=['POST'])
@jwt_required()
def api_save_action_item():
    try:
        data = request.get_json()
        required = ['schedule_meeting_id', 'action_items', 'action_item_priority', 'assigned_to', 'target_completion_date', 'action_item_status']
        if not all(k in data for k in required):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        user_id = get_jwt_identity()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'post_meeting_id' in data and data['post_meeting_id']:  # Update
            query = """
                UPDATE tbl_post_meeting_updates
                SET action_items = %s,
                    action_item_priority = %s,
                    assigned_to = %s,
                    target_completion_date = %s::date,
                    action_item_status = %s,
                    notes_followup = %s,
                    date_followup = %s::date,
                    date_completed = %s::date,
                    modified_by = %s,
                    modified_date = %s
                WHERE post_meeting_id = %s AND status = 1
            """
            params = (
                data['action_items'],
                data['action_item_priority'] or None,
                data['assigned_to'] or None,
                data['target_completion_date'],
                data['action_item_status'] or None,
                data.get('notes_followup'),
                data.get('date_followup'),
                data.get('date_completed'),
                user_id,
                now,
                data['post_meeting_id']
            )
        else:  # Insert
            query = """
                INSERT INTO tbl_post_meeting_updates (
                    schedule_meeting_id, action_items, action_item_priority, assigned_to,
                    target_completion_date, action_item_status, notes_followup, date_followup,
                    date_completed, status, created_by, created_date, modified_by, modified_date
                ) VALUES (%s, %s, %s, %s, %s::date, %s, %s, %s::date, %s::date, 1, %s, %s, %s, %s)
                RETURNING post_meeting_id
            """
            params = (
                data['schedule_meeting_id'],
                data['action_items'],
                data['action_item_priority'] or None,
                data['assigned_to'] or None,
                data['target_completion_date'],
                data['action_item_status'] or None,
                data.get('notes_followup'),
                data.get('date_followup'),
                data.get('date_completed'),
                user_id,
                now,
                user_id,
                now
            )

        execute_command(query, params)
        return jsonify({"success": True, "message": "Action item saved successfully"}), 200
    except Exception as e:
        print(f"save_action_item error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/action-item/<int:post_meeting_id>', methods=['DELETE'])
@jwt_required()
def api_delete_action_item(post_meeting_id):
    try:
        user_id = get_jwt_identity()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = """
            UPDATE tbl_post_meeting_updates
            SET status = 2, modified_by = %s, modified_date = %s
            WHERE post_meeting_id = %s AND status = 1
        """
        execute_command(query, (user_id, now, post_meeting_id))
        return jsonify({"success": True, "message": "Action item deleted"}), 200
    except Exception as e:
        print(f"delete_action_item error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/meeting-categories', methods=['GET'])
@jwt_required()
def api_get_meeting_categories():
    try:
        categories = get_all_meeting_categories()
        return jsonify({"success": True, "data": categories}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/meeting-category', methods=['POST'])
@application.route('/api/meeting-category/<int:category_id>', methods=['PUT'])
@jwt_required()
def api_save_meeting_category(category_id=None):
    try:
        if not (is_admin() or is_executive_approver()):  # or check JWT claims
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        data = request.get_json()
        if not data.get('meeting_category_name'):
            return jsonify({"success": False, "message": "Name is required"}), 400

        user_id = get_jwt_identity()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if category_id:  # Update
            query = """
                UPDATE tbl_meeting_categories
                SET meeting_category_code = %s,
                    meeting_category_name = %s,
                    status = 1,
                    modified_by = %s,
                    modified_date = %s
                WHERE meeting_category_id = %s
            """
            params = (
                data.get('meeting_category_code'),
                data['meeting_category_name'],
                user_id,
                now,
                category_id
            )
        else:  # Insert
            query = """
                INSERT INTO tbl_meeting_categories
                (meeting_category_code, meeting_category_name, status, created_by, created_date, modified_by, modified_date)
                VALUES (%s, %s, 1, %s, %s, %s, %s)
                RETURNING meeting_category_id
            """
            params = (
                data.get('meeting_category_code'),
                data['meeting_category_name'],
                user_id,
                now,
                user_id,
                now
            )

        execute_command(query, params)
        return jsonify({"success": True, "message": "Category saved"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/meeting-category/<int:category_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_category(category_id):
    try:
        if not (is_admin() or is_executive_approver()):
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        user_id = get_jwt_identity()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = """
            UPDATE tbl_meeting_categories
            SET status = 2, modified_by = %s, modified_date = %s
            WHERE meeting_category_id = %s
        """
        execute_command(query, (user_id, now, category_id))
        return jsonify({"success": True, "message": "Category deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@application.route('/api/get-master-book-action-items', methods=['POST'])
@jwt_required()
def get_master_book_action_items():
    try:
        # Safely get JSON — handle empty body gracefully
        data = request.get_json(silent=True) or {}
        print("Received filters:", data)  # Debug

        filters = {
            'meetingCategoryWithCode': data.get('meetingCategoryWithCode', ''),
            'Frequency': data.get('Frequency', ''),
            'TragetRangeAnnualOfMeetings': data.get('TragetRangeAnnualOfMeetings', ''),
            'proposed_month': data.get('proposed_month', ''),
            'national_council_distribution_name': data.get('national_council_distribution_name', ''),
            'resp_committ': data.get('resp_committ', ''),
            'meeting_priority_name': data.get('meeting_priority_name', ''),
            'meeting_title': data.get('meeting_title', ''),
            'meeting_aganda': data.get('meeting_aganda', ''),
            'assigned_leads': data.get('assigned_leads', ''),
            'schedule_meeting_id': data.get('schedule_meeting_id', ''),
            'last_updated_by': data.get('last_updated_by', ''),
            'schedule_date': data.get('schedule_date', ''),
            'pre_ms_name': data.get('pre_ms_name', ''),
            # Add any missing ones from your Flutter filters
            'action_items': data.get('action_items', ''),
            'action_item_priority': data.get('action_item_priority', ''),
            'assigned_to': data.get('assigned_to', ''),
            'target_completion_date': data.get('target_completion_date', ''),
            'action_item_status': data.get('action_item_status', ''),
            'notes_followup': data.get('notes_followup', ''),
            'date_followup': data.get('date_followup', ''),
            'date_completed': data.get('date_completed', ''),
            'pmu_created_by': data.get('pmu_created_by', ''),
            'pmu_modified_by': data.get('pmu_modified_by', ''),
        }

        mandatory_meetings = get_meeting_master_book_data()
        filtered_data = mandatory_meetings

        for key, value in filters.items():
            if value.strip():  # skip empty/whitespace
                search_val = str(value).lower().strip()
                filtered_data = [
                    m for m in filtered_data
                    if search_val in str(m.get(key, '')).lower()
                ]

        print(f"Filtered records count: {len(filtered_data)}")

        return jsonify({
            'success': True,
            'records': filtered_data
        }), 200

    except Exception as e:
        print('get_master_book_action_items exception:', str(e))
        import traceback
        traceback.print_exc()  # full stack trace in console
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meetings/schedule/<int:mand_meet_id>', methods=['GET', 'POST'])
@jwt_required()
def api_schedule_meeting(mand_meet_id):
    try:
        if not is_login():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        if request.method == 'GET':
            # Fetch mandatory meeting details
            mandatory_meeting = get_mandatory_meeting_details_by_id(mand_meet_id)
            # Fetch existing schedule meeting data
            schedule_meeting_details = get_schedule_meeting(mand_meet_id)
            # Fetch pre-meeting statuses
            pre_meeting_statuses = get_all_pre_meeting_status()

            return jsonify({
                'success': True,
                'data': {
                    'mandatory_meeting': mandatory_meeting,
                    'schedule_meeting_details': schedule_meeting_details,
                    'get_all_pre_meeting_status': pre_meeting_statuses
                }
            })

        elif request.method == 'POST':
            data = request.get_json()

            meeting_title = data.get('meeting_title')
            meeting_aganda = data.get('meeting_aganda')
            schedule_date = data.get('schedule_date')
            pre_ms_id = data.get('pre_ms_id')
            status = '1'
            current_user_id = get_current_user_id()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Escape strings
            meeting_title_escaped = escape_sql_string(meeting_title)
            meeting_aganda_escaped = escape_sql_string(meeting_aganda)

            schedule_meeting_details = get_schedule_meeting(mand_meet_id)

            if schedule_meeting_details:
                # Update
                query = f"""
                    UPDATE tbl_schedule_meetings 
                    SET meeting_title = {meeting_title_escaped},
                        meeting_aganda = {meeting_aganda_escaped},
                        schedule_date = '{schedule_date}',
                        pre_ms_id = {pre_ms_id},
                        status = {status},
                        modified_by = {current_user_id},
                        modified_date = '{current_time}'
                    WHERE schedule_meeting_id = {schedule_meeting_details['schedule_meeting_id']}
                """
                execute_command(query)
            else:
                # Insert
                query = f"""
                    INSERT INTO tbl_schedule_meetings 
                    (mand_meet_id, meeting_title, meeting_aganda, schedule_date, pre_ms_id, 
                     status, created_by, created_date, modified_by, modified_date)
                    VALUES ({mand_meet_id}, {meeting_title_escaped}, {meeting_aganda_escaped}, 
                            '{schedule_date}', {pre_ms_id}, {status}, 
                            {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
                """
                execute_command(query)

            return jsonify({'success': True, 'message': 'Meeting saved successfully'})

    except Exception as e:
        print('API schedule meeting exception:', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500