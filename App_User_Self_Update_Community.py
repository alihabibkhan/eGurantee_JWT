from imports import *
from application import application


@application.route('/api/community-service/dashboard', methods=['GET'])
@jwt_required()
def get_community_service_dashboard():
    """Get user's community service dashboard data"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        content = {
            'volunteer_info': get_all_user_data_by_id(user_id),
            'user_privileges': get_all_user_privileges_by_user_id(user_id),
            'service_hours': get_user_comm_svc_hours_by_user_id(user_id),
        }

        return jsonify({
            'success': True,
            'data': content
        }), 200

    except Exception as e:
        print('Community service dashboard exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to fetch community service data'
        }), 500


@application.route('/api/community-service/hours', methods=['POST'])
@jwt_required()
def create_community_service_hours():
    """Create new community service hours"""
    try:
        data = request.get_json()
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # Validate required fields
        required_fields = ['hours_contributed', 'service_category', 'month_year']

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Get form data
        hours_contributed = data['hours_contributed']
        service_category = data['service_category']
        brief_key_activities = data.get('brief_key_activities')
        month_year = data['month_year']
        status = '1'
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate data
        if int(hours_contributed) < 0:
            return jsonify({'error': 'Hours contributed must be non-negative'}), 400

        # Insert new record
        query = f"""
            INSERT INTO tbl_user_comm_svc_hours 
            (user_id, hours_contributed, service_category, brief_key_activities, month_year, status, 
             created_by, created_date, modified_by, modified_date)
            VALUES ({user_id}, {hours_contributed}, '{service_category}', 
                    {f"'{brief_key_activities}'" if brief_key_activities else 'NULL'}, 
                    '{month_year}-01', '{status}', 
                    {user_id}, '{current_time}', {user_id}, '{current_time}')
            RETURNING cum_sev_hr_id
        """

        result = execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Community service hours created successfully',
            'cum_sev_hr_id': result[0]['cum_sev_hr_id'] if result else None
        }), 201

    except Exception as e:
        print('Create community service hours exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to create community service hours'
        }), 500


@application.route('/api/community-service/hours/<int:cum_sev_hr_id>', methods=['GET'])
@jwt_required()
def get_community_service_hours_detail(cum_sev_hr_id):
    """Get specific community service hours detail"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        query = f"""
            SELECT cum_sev_hr_id, user_id, hours_contributed, service_category, 
                   brief_key_activities, status, created_by, 
                   TO_CHAR(month_year, 'YYYY-MM') AS month_year, 
                   created_date, modified_by, modified_date
            FROM tbl_user_comm_svc_hours 
            WHERE cum_sev_hr_id = {cum_sev_hr_id} AND user_id = {user_id} AND status != '2'
        """

        result = fetch_records(query)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404

        return jsonify({
            'success': True,
            'data': result[0]
        }), 200

    except Exception as e:
        print('Get community service hours detail exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to fetch community service hours'
        }), 500


@application.route('/api/community-service/hours/<int:cum_sev_hr_id>', methods=['PUT'])
@jwt_required()
def update_community_service_hours(cum_sev_hr_id):
    """Update community service hours"""
    try:
        data = request.get_json()
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # Check if record exists and belongs to user
        check_query = f"""
            SELECT cum_sev_hr_id FROM tbl_user_comm_svc_hours 
            WHERE cum_sev_hr_id = {cum_sev_hr_id} AND user_id = {user_id} AND status != '2'
        """
        existing = fetch_records(check_query)

        if not existing:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404

        # Validate required fields
        required_fields = ['hours_contributed', 'service_category', 'month_year']

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Get form data
        hours_contributed = data['hours_contributed']
        service_category = data['service_category']
        brief_key_activities = data.get('brief_key_activities')
        month_year = data['month_year']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update record
        query = f"""
            UPDATE tbl_user_comm_svc_hours 
            SET hours_contributed = {hours_contributed},
                service_category = '{service_category}',
                brief_key_activities = {f"'{brief_key_activities}'" if brief_key_activities else 'NULL'},
                month_year = '{month_year}-01',
                modified_by = {user_id},
                modified_date = '{current_time}'
            WHERE cum_sev_hr_id = {cum_sev_hr_id}
        """

        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Community service hours updated successfully'
        }), 200

    except Exception as e:
        print('Update community service hours exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to update community service hours'
        }), 500


@application.route('/api/community-service/hours/<int:cum_sev_hr_id>', methods=['DELETE'])
@jwt_required()
def delete_community_service_hours(cum_sev_hr_id):
    """Delete community service hours (soft delete)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if record exists and belongs to user
        check_query = f"""
            SELECT cum_sev_hr_id FROM tbl_user_comm_svc_hours 
            WHERE cum_sev_hr_id = {cum_sev_hr_id} AND user_id = {user_id} AND status != '2'
        """
        existing = fetch_records(check_query)

        if not existing:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404

        query = f"""
            UPDATE tbl_user_comm_svc_hours 
            SET status = '2', 
                modified_by = {user_id}, 
                modified_date = '{current_time}'
            WHERE cum_sev_hr_id = {cum_sev_hr_id}
        """

        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Community service hours deleted successfully'
        }), 200

    except Exception as e:
        print('Delete community service hours exception:- ', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to delete community service hours'
        }), 500