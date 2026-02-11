from imports import *
from application import application


# Branch Role Routes
# Branch Role CRUD API
@application.route('/api/branch-roles', methods=['POST'])
@application.route('/api/branch-roles/<int:role_id>', methods=['GET', 'PATCH', 'DELETE'])
@jwt_required()
def api_branch_role_crud(role_id=None):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        if request.method == 'GET':
            if not role_id:
                return jsonify({"error": "role_id required"}), 400

            query = """
                SELECT branch_role_id, branch_role_name, 
                       is_active, status, created_by, created_date, modified_by, modified_date
                FROM tbl_branch_role 
                WHERE branch_role_id = %s AND status != 3
            """
            result = fetch_records(query, (role_id,))
            if not result:
                return jsonify({"error": "branch role not found"}), 404

            return jsonify({"status": "ok", "data": result[0]}), 200

        # ── CREATE or UPDATE or DELETE ───────────────────────────────────────
        if request.method != 'DELETE':
            data = request.get_json()
            print("Incoming JSON Payload:", data)

        if request.method == 'POST' or request.method == 'PATCH':
            if not data:
                return jsonify({"error": "JSON payload required"}), 400

            required_fields = ['branch_role_name', 'is_active']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return jsonify({"error": "missing fields", "fields": missing}), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()
            status = '1'

            if request.method == 'POST':
                # CREATE
                query = """
                    INSERT INTO tbl_branch_role 
                    (branch_role_name, is_active, status, 
                     created_by, created_date, modified_by, modified_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING branch_role_id
                """
                params = (
                    data['branch_role_name'],
                    data['is_active'],
                    status,
                    user_id, now, user_id, now
                )
                result = execute_command(query, params)
                new_id = result if result else None

                return jsonify({"status": "created", "branch_role_id": new_id}), 201

            else:  # PATCH
                if not role_id:
                    return jsonify({"error": "role_id required"}), 400

                query = """
                    UPDATE tbl_branch_role 
                    SET branch_role_name = %s,
                        is_active = %s,
                        status = %s,
                        modified_by = %s,
                        modified_date = %s
                    WHERE branch_role_id = %s
                    AND status != 3
                    RETURNING branch_role_id
                """
                params = (
                    data['branch_role_name'],
                    data['is_active'],
                    status,
                    user_id, now, role_id
                )
                result = execute_command(query, params)

                # if not result:
                #     return jsonify({"error": "branch role not found"}), 404

                return jsonify({"status": "updated"}), 200

        else:  # DELETE (soft delete - update status to 2)
            if not role_id:
                return jsonify({"error": "role_id required"}), 400

            # Check if role is being used
            check_query = """
                SELECT COUNT(*) as count 
                FROM tbl_branches 
                WHERE role = %s
            """
            check_result = fetch_records(check_query, (role_id,))

            if check_result and check_result[0]['count'] > 0:
                return jsonify({
                    "error": "Cannot delete. Branch role is being used by branches."
                }), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()

            query = """
                UPDATE tbl_branch_role 
                SET status = 2, 
                    modified_by = %s, 
                    modified_date = %s
                WHERE branch_role_id = %s
                AND status != 3
                RETURNING branch_role_id
            """
            result = execute_command(query, (user_id, now, role_id))

            # if not result:
            #     return jsonify({"error": "branch role not found"}), 404

            return jsonify({"status": "deleted"}), 200

    except Exception as exc:
        print("api_branch_role_crud error:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500