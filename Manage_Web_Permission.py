from imports import *
from application import application


# ====================== WEB PERMISSIONS APIs ======================

@application.route('/api/web-permissions', methods=['GET'])
@jwt_required()
def api_get_all_web_permissions():
    """Get all web permissions (with optional filters)"""
    try:
        current_user_id = get_jwt_identity()

        # Use your existing is_admin() method
        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        # Optional filters from query params
        category = request.args.get('category', '')
        status = request.args.get('status', '')

        query = """
            SELECT web_permission_id, category, title, route, permission_key, description, 
                   status, created_date, modified_date
            FROM tbl_web_permissions 
            where status = 1
        """

        if category:
            query += f" AND category = '{escape_sql_string(category)}'"
        if status:
            query += f" AND status = {int(status)}"

        query += " ORDER BY title ASC"

        permissions = fetch_records(query)

        return jsonify({
            'success': True,
            'permissions': permissions,
            'total': len(permissions)
        }), 200

    except Exception as e:
        print('api_get_all_web_permissions exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/web-permissions/<int:permission_id>', methods=['GET'])
@jwt_required()
def api_get_web_permission_by_id(permission_id):
    """Get single web permission by ID"""
    try:
        current_user_id = get_jwt_identity()

        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        query = f"""
            SELECT web_permission_id, category, title, route, permission_key, description, status
            FROM tbl_web_permissions 
            WHERE web_permission_id = {permission_id}
        """
        result = fetch_records(query)

        if not result:
            return jsonify({'error': 'Permission not found'}), 404

        return jsonify({
            'success': True,
            'permission': result[0]
        }), 200

    except Exception as e:
        print('api_get_web_permission_by_id exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/web-permissions', methods=['POST'])
@jwt_required()
def api_create_web_permission():
    """Create a new web permission"""
    try:
        current_user_id = get_jwt_identity()

        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()

        # Validate required fields
        required_fields = ['category', 'title', 'route', 'permission_key', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        category = data['category']
        title = data['title']
        route = data['route']
        permission_key = data['permission_key']
        description = data.get('description', '')
        status = data['status']

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Use your existing escape_sql_string method
        category_esc = escape_sql_string(category)
        title_esc = escape_sql_string(title)
        route_esc = escape_sql_string(route)
        permission_key_esc = escape_sql_string(permission_key)
        description_esc = escape_sql_string(description)

        query = f"""
            INSERT INTO tbl_web_permissions 
            (category, title, route, permission_key, description, status, 
             created_by, created_date, modified_by, modified_date)
            VALUES ({category_esc}, {title_esc}, {route_esc}, {permission_key_esc}, 
                    {description_esc}, {status}, {current_user_id}, '{current_time}', 
                    {current_user_id}, '{current_time}')
            RETURNING web_permission_id
        """

        result = execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Web permission created successfully',
            'web_permission_id': result
        }), 201

    except Exception as e:
        print('api_create_web_permission exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/web-permissions/<int:permission_id>', methods=['PUT'])
@jwt_required()
def api_update_web_permission(permission_id):
    """Update an existing web permission"""
    try:
        current_user_id = get_jwt_identity()

        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()

        # Check if permission exists using your fetch_records
        check_query = f"""
            SELECT web_permission_id FROM tbl_web_permissions 
            WHERE web_permission_id = {permission_id}
        """
        existing = fetch_records(check_query)

        if not existing:
            return jsonify({'error': 'Permission not found'}), 404

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build update query dynamically
        update_parts = []

        if 'category' in data:
            update_parts.append(f"category = {escape_sql_string(data['category'])}")
        if 'title' in data:
            update_parts.append(f"title = {escape_sql_string(data['title'])}")
        if 'route' in data:
            update_parts.append(f"route = {escape_sql_string(data['route'])}")
        if 'permission_key' in data:
            update_parts.append(f"permission_key = {escape_sql_string(data['permission_key'])}")
        if 'description' in data:
            update_parts.append(f"description = {escape_sql_string(data['description'])}")
        if 'status' in data:
            update_parts.append(f"status = {data['status']}")

        if not update_parts:
            return jsonify({'error': 'No fields to update'}), 400

        update_parts.append(f"modified_by = {current_user_id}")
        update_parts.append(f"modified_date = '{current_time}'")

        query = f"""
            UPDATE tbl_web_permissions 
            SET {', '.join(update_parts)}
            WHERE web_permission_id = {permission_id}
        """

        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Web permission updated successfully'
        }), 200

    except Exception as e:
        print('api_update_web_permission exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/web-permissions/<int:permission_id>', methods=['DELETE'])
@jwt_required()
def api_delete_web_permission(permission_id):
    """Soft delete a web permission (set status to 0)"""
    try:
        current_user_id = get_jwt_identity()

        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Use your existing execute_command for soft delete
        query = f"""
            UPDATE tbl_web_permissions 
            SET status = 0, 
                modified_by = {current_user_id}, 
                modified_date = '{current_time}'
            WHERE web_permission_id = {permission_id}
        """
        execute_command(query)

        return jsonify({
            'success': True,
            'message': 'Web permission deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_web_permission exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500


@application.route('/api/web-permissions/bulk-delete', methods=['POST'])
@jwt_required()
def api_bulk_delete_web_permissions():
    """Bulk delete multiple web permissions"""
    try:
        current_user_id = get_jwt_identity()

        if not is_admin():
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()
        permission_ids = data.get('permission_ids', [])

        if not permission_ids or not isinstance(permission_ids, list):
            return jsonify({'error': 'Invalid permission_ids array'}), 400

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Bulk soft delete
        for permission_id in permission_ids:
            query = f"""
                UPDATE tbl_web_permissions 
                SET status = 0, 
                    modified_by = {current_user_id}, 
                    modified_date = '{current_time}'
                WHERE web_permission_id = {permission_id}
            """
            execute_command(query)

        return jsonify({
            'success': True,
            'message': f'{len(permission_ids)} permissions deleted successfully',
            'deleted_count': len(permission_ids)
        }), 200

    except Exception as e:
        print('api_bulk_delete_web_permissions exception:-', str(e))
        return jsonify({'error': 'Server error'}), 500
