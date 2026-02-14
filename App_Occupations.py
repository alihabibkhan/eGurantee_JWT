from imports import *
from application import application


@application.route('/api/occupations', methods=['GET'])
@jwt_required()
def api_get_all_occupations():
    """API endpoint to get all occupations"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        occupations = get_all_occupations()
        return jsonify({
            'success': True,
            'data': occupations
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/occupations/<int:occupation_id>', methods=['GET'])
@jwt_required()
def api_get_occupation(occupation_id):
    """API endpoint to get a single occupation by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT occupation_id, name, status, created_by, created_date, modified_by, modified_date
            FROM tbl_occupations 
            WHERE occupation_id = '{occupation_id}' AND status = '1'
        """
        occupation = fetch_records(query)
        occupation = occupation[0] if occupation else None

        if occupation:
            return jsonify({'success': True, 'data': {'occupation': occupation}}), 200
        else:
            return jsonify({'success': False, 'message': 'Occupation not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/occupations', methods=['POST'])
@application.route('/api/occupations/<int:occupation_id>', methods=['POST'])
@jwt_required()
def api_save_occupation(occupation_id=None):
    """API endpoint to create or update an occupation"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()
        name = data.get('name')

        current_user_id = str(get_current_user_id())
        current_timestamp = str(datetime.now())

        if occupation_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_occupations 
                SET name = '{name}', 
                    status = '1', 
                    modified_by = '{current_user_id}', 
                    modified_date = '{current_timestamp}'
                WHERE occupation_id = '{occupation_id}'
            """
            execute_command(update_query)
            message = 'Occupation updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_occupations (
                    name, status, created_by, created_date, modified_by, modified_date
                ) VALUES (
                    '{name}', '1', '{current_user_id}', '{current_timestamp}', 
                    '{current_user_id}', '{current_timestamp}'
                )
            """
            execute_command(insert_query)
            message = 'Occupation added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_occupation exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/occupations/<int:occupation_id>', methods=['DELETE'])
@jwt_required()
def api_delete_occupation(occupation_id):
    """API endpoint to delete an occupation (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_occupations 
            SET status = '0'
            WHERE occupation_id = '{occupation_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Occupation deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_occupation exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
