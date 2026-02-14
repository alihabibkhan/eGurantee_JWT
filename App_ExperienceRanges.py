from imports import *
from application import application


@application.route('/api/experience-ranges', methods=['GET'])
@jwt_required()
def api_get_all_experience_ranges():
    """API endpoint to get all experience ranges"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        ranges = get_all_experience_ranges()
        return jsonify({
            'success': True,
            'data': ranges
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/experience-ranges/<int:experience_range_id>', methods=['GET'])
@jwt_required()
def api_get_experience_range(experience_range_id):
    """API endpoint to get a single experience range by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT experience_range_id, label, min_years, max_years, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_experience_ranges 
            WHERE experience_range_id = '{experience_range_id}' AND status = '1'
        """
        experience_range = fetch_records(query)
        experience_range = experience_range[0] if experience_range else None

        if experience_range:
            return jsonify({
                'success': True,
                'data': {'experience_range': experience_range}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Experience range not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/experience-ranges', methods=['POST'])
@application.route('/api/experience-ranges/<int:experience_range_id>', methods=['POST'])
@jwt_required()
def api_save_experience_range(experience_range_id=None):
    """API endpoint to create or update an experience range"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()
        label = data.get('label')
        min_years = data.get('min_years')
        max_years = data.get('max_years')

        current_user_id = str(get_current_user_id())
        current_timestamp = str(datetime.now())

        if experience_range_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_experience_ranges 
                SET label = '{label}', 
                    min_years = '{min_years}', 
                    max_years = '{max_years}', 
                    status = '1', 
                    modified_by = '{current_user_id}', 
                    modified_date = '{current_timestamp}'
                WHERE experience_range_id = '{experience_range_id}'
            """
            execute_command(update_query)
            message = 'Experience range updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_experience_ranges (
                    label, min_years, max_years, status, 
                    created_by, created_date, modified_by, modified_date
                ) VALUES (
                    '{label}', '{min_years}', '{max_years}', '1', 
                    '{current_user_id}', '{current_timestamp}', 
                    '{current_user_id}', '{current_timestamp}'
                )
            """
            execute_command(insert_query)
            message = 'Experience range added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_experience_range exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/experience-ranges/<int:experience_range_id>', methods=['DELETE'])
@jwt_required()
def api_delete_experience_range(experience_range_id):
    """API endpoint to delete an experience range (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_experience_ranges 
            SET status = '0'
            WHERE experience_range_id = '{experience_range_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Experience range deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_experience_range exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500