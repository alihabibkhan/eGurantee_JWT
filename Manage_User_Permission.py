from imports import *
from application import application


# ====================== USER PERMISSIONS APIs ======================

@application.route('/api/user-permissions', methods=['GET'])
@jwt_required()
def api_get_all_user_permissions():
    """Get all user permissions"""
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        query = """
            SELECT up.user_permission_id, u.user_id, u.name, u.email, 
                   wp.title, wp.route, wp.permission_key,
                   up.status, up.granted_date
            FROM tbl_user_permissions up
            JOIN tbl_web_permissions wp ON up.web_permission_id = wp.web_permission_id
            JOIN tbl_users u ON up.user_id = u.user_id
            WHERE wp.status = 1 and up.status = 1
            ORDER BY u.name, wp.title
        """
        user_permissions = fetch_records(query)

        return jsonify({
            'success': True,
            'user_permissions': user_permissions
        }), 200

    except Exception as e:
        print('api_get_all_user_permissions exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/users_rights', methods=['GET'])
@jwt_required()
def api_get_all_users_rights():
    """Get all users for dropdown"""
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        query = "SELECT user_id, name, email, rights FROM tbl_users ORDER BY name"
        users = fetch_records(query)

        # Convert to list of dictionaries with correct key names
        users_list = []
        if users:  # Check if users is not None or empty
            for user in users:
                users_list.append({
                    'userId': user.get('user_id'),  # Use .get() to avoid KeyError
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'rights': str(user.get('rights')) if user.get('rights') is not None else '0'
                })

        # Always return a list, even if empty
        print(f"API returning {len(users_list)} users")  # Debug print

        return jsonify({
            'success': True,
            'users': users_list  # This will be [] if no users found
        }), 200

    except Exception as e:
        print('api_get_all_users exception:-', str(e))
        return jsonify({
            'success': False,
            'error': 'Server error',
            'users': []  # Return empty list on error
        }), 500


@application.route('/api/web-permissions/simple', methods=['GET'])
@jwt_required()
def api_get_web_permissions_simple():
    """Get all active web permissions for dropdown"""
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        query = """
            SELECT web_permission_id, title, route 
            FROM tbl_web_permissions 
            WHERE status = 1 
            ORDER BY title
        """
        permissions = fetch_records(query)

        return jsonify({
            'success': True,
            'permissions': permissions
        }), 200

    except Exception as e:
        print('api_get_web_permissions_simple exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/user-permissions/assign', methods=['POST'])
@jwt_required()
def api_assign_user_permission():
    """Assign permission to users"""
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()
        role_id = data.get('role_id')
        user_ids = data.get('user_ids', [])
        web_permission_id = data.get('web_permission_id')

        if not user_ids or not web_permission_id:
            return jsonify({'error': 'Please select users and permission'}), 400

        current_user_id = get_jwt_identity()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        success_count = 0

        for user_id in user_ids:
            # Check if already exists
            check_query = f"""
                SELECT 1 FROM tbl_user_permissions 
                WHERE user_id = {user_id} AND web_permission_id = {web_permission_id}
            """
            if fetch_records(check_query):
                # Already exists → just activate it
                query = f"""
                    UPDATE tbl_user_permissions 
                    SET status = 1, granted_by = {current_user_id}, granted_date = '{current_time}'
                    WHERE user_id = {user_id} AND web_permission_id = {web_permission_id}
                """
            else:
                # Insert new
                query = f"""
                    INSERT INTO tbl_user_permissions 
                    (user_id, web_permission_id, granted_by, granted_date, status)
                    VALUES ({user_id}, {web_permission_id}, {current_user_id}, '{current_time}', 1)
                """

            try:
                execute_command(query)
                success_count += 1
            except Exception as e:
                print(f"Error assigning permission to user {user_id}: {str(e)}")

        if success_count > 0:
            return jsonify({
                'success': True,
                'message': f'Successfully assigned permission to {success_count} user(s)'
            }), 200
        else:
            return jsonify({'error': 'Failed to assign permissions'}), 400

    except Exception as e:
        print('api_assign_user_permission exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/user-permissions/revoke', methods=['POST'])
@jwt_required()
def api_revoke_user_permissions():
    """Revoke user permissions"""
    try:
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()
        user_permission_ids = data.get('user_permission_ids', [])

        if not user_permission_ids:
            return jsonify({'error': 'No permissions selected for revocation'}), 400

        success_count = 0
        for user_permission_id in user_permission_ids:
            query = f"""
                UPDATE tbl_user_permissions 
                SET status = 0
                WHERE user_permission_id = {user_permission_id}
            """
            try:
                execute_command(query)
                success_count += 1
            except Exception as e:
                print(f"Error revoking permission {user_permission_id}: {str(e)}")

        if success_count > 0:
            return jsonify({
                'success': True,
                'message': f'Successfully revoked {success_count} permission(s)'
            }), 200
        else:
            return jsonify({'error': 'Failed to revoke permissions'}), 400

    except Exception as e:
        print('api_revoke_user_permissions exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500