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



# ==================== MEETING SETUP API ROUTES ====================
@application.route('/api/manage-meeting-setup', methods=['GET'])
@jwt_required()
def api_manage_meeting_setup():
    """API endpoint to get all meeting setup data for the dashboard"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = {
            'meeting_categories': get_all_meeting_categories(),
            'meeting_frequencies': get_all_meeting_frequencies(),
            'meeting_priorities': get_all_meeting_priorities(),
            'pre_meeting_status': get_all_pre_meeting_status(),
            'post_meeting_status': get_all_post_meeting_status(),
            'meeting_action_items': get_all_meeting_action_items(),
            'meeting_action_items_priorities': get_all_meeting_action_items_priorities(),
            'meeting_action_items_status': get_all_meeting_action_items_status(),
            'mandatory_meetings': get_all_mandatory_meetings(),
            'national_council_distributions': get_all_national_council_distributions()
        }

        return jsonify({
            'success': True,
            'data': data
        }), 200

    except Exception as e:
        print('api_manage_meeting_setup exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING CATEGORIES API ====================
@application.route('/api/meeting-categories', methods=['GET'])
@jwt_required()
def api_get_all_meeting_categories():
    """API endpoint to get all meeting categories"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        categories = get_all_meeting_categories()
        return jsonify({
            'success': True,
            'data': categories
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-categories/<int:meeting_category_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_category(meeting_category_id):
    """API endpoint to get a single meeting category by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT meeting_category_id, meeting_category_code, meeting_category_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_categories 
            WHERE meeting_category_id = {meeting_category_id} AND status != 3
        """
        category = fetch_records(query)
        category = category[0] if category else None

        if category:
            return jsonify({
                'success': True,
                'data': {'meeting_category': category}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting category not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-categories', methods=['POST'])
@application.route('/api/meeting-categories/<int:meeting_category_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_category(meeting_category_id=None):
    """API endpoint to create or update a meeting category"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        meeting_category_code = data.get('meeting_category_code')
        meeting_category_name = data.get('meeting_category_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        meeting_category_code_escaped = escape_sql_string(meeting_category_code)
        meeting_category_name_escaped = escape_sql_string(meeting_category_name)

        if meeting_category_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_categories 
                SET meeting_category_code = {meeting_category_code_escaped},
                    meeting_category_name = {meeting_category_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE meeting_category_id = {meeting_category_id}
            """
            execute_command(update_query)
            message = 'Meeting category updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_categories
                (meeting_category_code, meeting_category_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({meeting_category_code_escaped}, {meeting_category_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting category added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_category exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-categories/<int:meeting_category_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_category(meeting_category_id):
    """API endpoint to delete a meeting category (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_categories 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE meeting_category_id = {meeting_category_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting category deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_category exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING FREQUENCIES API ====================

@application.route('/api/meeting-frequencies', methods=['GET'])
@jwt_required()
def api_get_all_meeting_frequencies():
    """API endpoint to get all meeting frequencies"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        frequencies = get_all_meeting_frequencies()
        return jsonify({
            'success': True,
            'data': frequencies
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-frequencies/<int:meeting_freq_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_frequency(meeting_freq_id):
    """API endpoint to get a single meeting frequency by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT meeting_freq_id, meeting_freq_title, min_freq, max_freq, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_frequencies 
            WHERE meeting_freq_id = {meeting_freq_id} AND status != 3
        """
        frequency = fetch_records(query)
        frequency = frequency[0] if frequency else None

        if frequency:
            return jsonify({
                'success': True,
                'data': {'meeting_frequency': frequency}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting frequency not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-frequencies', methods=['POST'])
@application.route('/api/meeting-frequencies/<int:meeting_freq_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_frequency(meeting_freq_id=None):
    """API endpoint to create or update a meeting frequency"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        meeting_freq_title = data.get('meeting_freq_title')
        min_freq = data.get('min_freq')
        max_freq = data.get('max_freq')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        meeting_freq_title_escaped = escape_sql_string(meeting_freq_title)

        if meeting_freq_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_frequencies 
                SET meeting_freq_title = {meeting_freq_title_escaped},
                    min_freq = {min_freq},
                    max_freq = {max_freq},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE meeting_freq_id = {meeting_freq_id}
            """
            execute_command(update_query)
            message = 'Meeting frequency updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_frequencies 
                (meeting_freq_title, min_freq, max_freq, status, created_by, created_date, modified_by, modified_date)
                VALUES ({meeting_freq_title_escaped}, {min_freq}, {max_freq}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting frequency added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_frequency exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-frequencies/<int:meeting_freq_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_frequency(meeting_freq_id):
    """API endpoint to delete a meeting frequency (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_frequencies 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE meeting_freq_id = {meeting_freq_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting frequency deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_frequency exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING PRIORITIES API ====================

@application.route('/api/meeting-priorities', methods=['GET'])
@jwt_required()
def api_get_all_meeting_priorities():
    """API endpoint to get all meeting priorities"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        priorities = get_all_meeting_priorities()
        return jsonify({
            'success': True,
            'data': priorities
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-priorities/<int:meeting_priority_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_priority(meeting_priority_id):
    """API endpoint to get a single meeting priority by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT meeting_priority_id, meeting_priority_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_priorities 
            WHERE meeting_priority_id = {meeting_priority_id} AND status != 3
        """
        priority = fetch_records(query)
        priority = priority[0] if priority else None

        if priority:
            return jsonify({
                'success': True,
                'data': {'meeting_priority': priority}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting priority not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-priorities', methods=['POST'])
@application.route('/api/meeting-priorities/<int:meeting_priority_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_priority(meeting_priority_id=None):
    """API endpoint to create or update a meeting priority"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        meeting_priority_name = data.get('meeting_priority_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        meeting_priority_name_escaped = escape_sql_string(meeting_priority_name)

        if meeting_priority_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_priorities 
                SET meeting_priority_name = {meeting_priority_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE meeting_priority_id = {meeting_priority_id}
            """
            execute_command(update_query)
            message = 'Meeting priority updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_priorities 
                (meeting_priority_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({meeting_priority_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting priority added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_priority exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-priorities/<int:meeting_priority_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_priority(meeting_priority_id):
    """API endpoint to delete a meeting priority (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_priorities 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE meeting_priority_id = {meeting_priority_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting priority deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_priority exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== PRE-MEETING STATUS API ====================

@application.route('/api/pre-meeting-status', methods=['GET'])
@jwt_required()
def api_get_all_pre_meeting_status():
    """API endpoint to get all pre-meeting statuses"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        statuses = get_all_pre_meeting_status()
        return jsonify({
            'success': True,
            'data': statuses
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/pre-meeting-status/<int:pre_ms_id>', methods=['GET'])
@jwt_required()
def api_get_pre_meeting_status(pre_ms_id):
    """API endpoint to get a single pre-meeting status by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT pre_ms_id, pre_ms_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_pre_meeting_status 
            WHERE pre_ms_id = {pre_ms_id} AND status != 3
        """
        status = fetch_records(query)
        status = status[0] if status else None

        if status:
            return jsonify({
                'success': True,
                'data': {'pre_meeting_status': status}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Pre-meeting status not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/pre-meeting-status', methods=['POST'])
@application.route('/api/pre-meeting-status/<int:pre_ms_id>', methods=['POST'])
@jwt_required()
def api_save_pre_meeting_status(pre_ms_id=None):
    """API endpoint to create or update a pre-meeting status"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        pre_ms_name = data.get('pre_ms_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        pre_ms_name_escaped = escape_sql_string(pre_ms_name)

        if pre_ms_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_pre_meeting_status 
                SET pre_ms_name = {pre_ms_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE pre_ms_id = {pre_ms_id}
            """
            execute_command(update_query)
            message = 'Pre-meeting status updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_pre_meeting_status 
                (pre_ms_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({pre_ms_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Pre-meeting status added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_pre_meeting_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/pre-meeting-status/<int:pre_ms_id>', methods=['DELETE'])
@jwt_required()
def api_delete_pre_meeting_status(pre_ms_id):
    """API endpoint to delete a pre-meeting status (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_pre_meeting_status 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE pre_ms_id = {pre_ms_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Pre-meeting status deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_pre_meeting_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== POST-MEETING STATUS API ====================

@application.route('/api/post-meeting-status', methods=['GET'])
@jwt_required()
def api_get_all_post_meeting_status():
    """API endpoint to get all post-meeting statuses"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        statuses = get_all_post_meeting_status()
        return jsonify({
            'success': True,
            'data': statuses
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/post-meeting-status/<int:post_ms_id>', methods=['GET'])
@jwt_required()
def api_get_post_meeting_status(post_ms_id):
    """API endpoint to get a single post-meeting status by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT post_ms_id, post_ms_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_post_meeting_status 
            WHERE post_ms_id = {post_ms_id} AND status != 3
        """
        status = fetch_records(query)
        status = status[0] if status else None

        if status:
            return jsonify({
                'success': True,
                'data': {'post_meeting_status': status}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Post-meeting status not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/post-meeting-status', methods=['POST'])
@application.route('/api/post-meeting-status/<int:post_ms_id>', methods=['POST'])
@jwt_required()
def api_save_post_meeting_status(post_ms_id=None):
    """API endpoint to create or update a post-meeting status"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        post_ms_name = data.get('post_ms_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        post_ms_name_escaped = escape_sql_string(post_ms_name)

        if post_ms_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_post_meeting_status 
                SET post_ms_name = {post_ms_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE post_ms_id = {post_ms_id}
            """
            execute_command(update_query)
            message = 'Post-meeting status updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_post_meeting_status 
                (post_ms_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({post_ms_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Post-meeting status added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_post_meeting_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/post-meeting-status/<int:post_ms_id>', methods=['DELETE'])
@jwt_required()
def api_delete_post_meeting_status(post_ms_id):
    """API endpoint to delete a post-meeting status (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_post_meeting_status 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE post_ms_id = {post_ms_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Post-meeting status deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_post_meeting_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING ACTION ITEMS API ====================

@application.route('/api/meeting-action-items', methods=['GET'])
@jwt_required()
def api_get_all_meeting_action_items():
    """API endpoint to get all meeting action items"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        items = get_all_meeting_action_items()
        return jsonify({
            'success': True,
            'data': items
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items/<int:mai_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_action_item(mai_id):
    """API endpoint to get a single meeting action item by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT mai_id, mai_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_action_items 
            WHERE mai_id = {mai_id} AND status != 3
        """
        item = fetch_records(query)
        item = item[0] if item else None

        if item:
            return jsonify({
                'success': True,
                'data': {'meeting_action_item': item}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting action item not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items', methods=['POST'])
@application.route('/api/meeting-action-items/<int:mai_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_action_item(mai_id=None):
    """API endpoint to create or update a meeting action item"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        mai_name = data.get('mai_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        mai_name_escaped = escape_sql_string(mai_name)

        if mai_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_action_items 
                SET mai_name = {mai_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE mai_id = {mai_id}
            """
            execute_command(update_query)
            message = 'Meeting action item updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_action_items 
                (mai_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({mai_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting action item added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_action_item exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items/<int:mai_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_action_item(mai_id):
    """API endpoint to delete a meeting action item (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_action_items 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE mai_id = {mai_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting action item deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_action_item exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING ACTION ITEMS PRIORITIES API ====================

@application.route('/api/meeting-action-items-priorities', methods=['GET'])
@jwt_required()
def api_get_all_meeting_action_items_priorities():
    """API endpoint to get all meeting action items priorities"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        priorities = get_all_meeting_action_items_priorities()
        return jsonify({
            'success': True,
            'data': priorities
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-priorities/<int:maip_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_action_item_priority(maip_id):
    """API endpoint to get a single meeting action item priority by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT maip_id, maip_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_action_items_priorities 
            WHERE maip_id = {maip_id} AND status != 3
        """
        priority = fetch_records(query)
        priority = priority[0] if priority else None

        if priority:
            return jsonify({
                'success': True,
                'data': {'meeting_action_item_priority': priority}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting action item priority not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-priorities', methods=['POST'])
@application.route('/api/meeting-action-items-priorities/<int:maip_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_action_item_priority(maip_id=None):
    """API endpoint to create or update a meeting action item priority"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        maip_name = data.get('maip_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        maip_name_escaped = escape_sql_string(maip_name)

        if maip_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_action_items_priorities 
                SET maip_name = {maip_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE maip_id = {maip_id}
            """
            execute_command(update_query)
            message = 'Meeting action item priority updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_action_items_priorities 
                (maip_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({maip_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting action item priority added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_action_item_priority exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-priorities/<int:maip_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_action_item_priority(maip_id):
    """API endpoint to delete a meeting action item priority (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_action_items_priorities 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE maip_id = {maip_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting action item priority deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_action_item_priority exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MEETING ACTION ITEMS STATUS API ====================

@application.route('/api/meeting-action-items-status', methods=['GET'])
@jwt_required()
def api_get_all_meeting_action_items_status():
    """API endpoint to get all meeting action items statuses"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        statuses = get_all_meeting_action_items_status()
        return jsonify({
            'success': True,
            'data': statuses
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-status/<int:mais_id>', methods=['GET'])
@jwt_required()
def api_get_meeting_action_item_status(mais_id):
    """API endpoint to get a single meeting action item status by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT mais_id, mais_name, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_meeting_action_items_status 
            WHERE mais_id = {mais_id} AND status != 3
        """
        status = fetch_records(query)
        status = status[0] if status else None

        if status:
            return jsonify({
                'success': True,
                'data': {'meeting_action_item_status': status}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Meeting action item status not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-status', methods=['POST'])
@application.route('/api/meeting-action-items-status/<int:mais_id>', methods=['POST'])
@jwt_required()
def api_save_meeting_action_item_status(mais_id=None):
    """API endpoint to create or update a meeting action item status"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        mais_name = data.get('mais_name')

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        mais_name_escaped = escape_sql_string(mais_name)

        if mais_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_meeting_action_items_status 
                SET mais_name = {mais_name_escaped},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE mais_id = {mais_id}
            """
            execute_command(update_query)
            message = 'Meeting action item status updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_meeting_action_items_status 
                (mais_name, status, created_by, created_date, modified_by, modified_date)
                VALUES ({mais_name_escaped}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Meeting action item status added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_meeting_action_item_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/meeting-action-items-status/<int:mais_id>', methods=['DELETE'])
@jwt_required()
def api_delete_meeting_action_item_status(mais_id):
    """API endpoint to delete a meeting action item status (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_meeting_action_items_status 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE mais_id = {mais_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Meeting action item status deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_meeting_action_item_status exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MANDATORY MEETINGS API ====================

@application.route('/api/mandatory-meetings', methods=['GET'])
@jwt_required()
def api_get_all_mandatory_meetings():
    """API endpoint to get all mandatory meetings"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        meetings = get_all_mandatory_meetings()
        return jsonify({
            'success': True,
            'data': meetings
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/mandatory-meetings/<int:mand_meet_id>', methods=['GET'])
@jwt_required()
def api_get_mandatory_meeting(mand_meet_id):
    """API endpoint to get a single mandatory meeting by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT mand_meet_id, meeting_category_id, meeting_freq_id, proposed_month, nc_disb_id, 
                   resp_committ, meeting_priority_id, status, created_by, created_date, modified_by, modified_date
            FROM tbl_mandatory_meetings 
            WHERE mand_meet_id = {mand_meet_id} AND status != 3
        """
        meeting = fetch_records(query)
        meeting = meeting[0] if meeting else None

        if meeting:
            return jsonify({
                'success': True,
                'data': {'mandatory_meeting': meeting}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Mandatory meeting not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/mandatory-meetings', methods=['POST'])
@application.route('/api/mandatory-meetings/<int:mand_meet_id>', methods=['POST'])
@jwt_required()
def api_save_mandatory_meeting(mand_meet_id=None):
    """API endpoint to create or update a mandatory meeting"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        meeting_category_id = data.get('meeting_category_id')
        meeting_freq_id = data.get('meeting_freq_id')
        proposed_month = data.get('proposed_month')
        nc_disb_id = data.get('nc_disb_id')
        resp_committ = data.get('resp_committ')
        meeting_priority_id = data.get('meeting_priority_id')

        # Convert proposed_month (YYYY-MM) to a full date (YYYY-MM-01)
        if proposed_month:
            proposed_month = f"{proposed_month}-01"
        else:
            proposed_month = None

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        resp_committ_escaped = escape_sql_string(resp_committ) if resp_committ else 'NULL'

        if mand_meet_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_mandatory_meetings 
                SET meeting_category_id = {meeting_category_id},
                    meeting_freq_id = {meeting_freq_id},
                    proposed_month = '{proposed_month}',
                    nc_disb_id = {nc_disb_id},
                    resp_committ = {resp_committ_escaped},
                    meeting_priority_id = {meeting_priority_id},
                    status = 1,
                    modified_by = {current_user_id},
                    modified_date = '{current_time}'
                WHERE mand_meet_id = {mand_meet_id}
            """
            execute_command(update_query)
            message = 'Mandatory meeting updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_mandatory_meetings 
                (meeting_category_id, meeting_freq_id, proposed_month, nc_disb_id, resp_committ, 
                 meeting_priority_id, status, created_by, created_date, modified_by, modified_date)
                VALUES ({meeting_category_id}, {meeting_freq_id}, '{proposed_month}', {nc_disb_id}, 
                        {resp_committ_escaped}, {meeting_priority_id}, 1, 
                        {current_user_id}, '{current_time}', {current_user_id}, '{current_time}')
            """
            execute_command(insert_query)
            message = 'Mandatory meeting added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_mandatory_meeting exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/mandatory-meetings/<int:mand_meet_id>', methods=['DELETE'])
@jwt_required()
def api_delete_mandatory_meeting(mand_meet_id):
    """API endpoint to delete a mandatory meeting (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        delete_query = f"""
            UPDATE tbl_mandatory_meetings 
            SET status = 2, modified_by = {current_user_id}, modified_date = '{current_time}'
            WHERE mand_meet_id = {mand_meet_id}
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Mandatory meeting deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_mandatory_meeting exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== NATIONAL COUNCIL DISTRIBUTIONS API (Helper) ====================

@application.route('/api/national-council-distributions', methods=['GET'])
@jwt_required()
def api_get_all_national_council_distributions():
    """API endpoint to get all national council distributions"""
    try:
        if not is_login():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        distributions = get_all_national_council_distributions()
        return jsonify({
            'success': True,
            'data': distributions
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500