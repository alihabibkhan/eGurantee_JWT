from imports import *
from application import application


# KFT Distribution Routes
# KFT Distribution CRUD API
@application.route('/api/kft-distributions', methods=['POST'])
@application.route('/api/kft-distributions/<int:distribution_id>', methods=['GET', 'PATCH', 'DELETE'])
@jwt_required()
def api_kft_distribution_crud(distribution_id=None):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        if request.method == 'GET':
            if not distribution_id:
                return jsonify({"error": "distribution_id required"}), 400

            query = """
                SELECT kft_distribution_id, kft_distribution_name, 
                       is_active, status, created_by, created_date, modified_by, modified_date
                FROM tbl_kft_distribution 
                WHERE kft_distribution_id = %s AND status != 3
            """
            result = fetch_records(query, (distribution_id,))
            if not result:
                return jsonify({"error": "KFT distribution not found"}), 404

            return jsonify({"status": "ok", "data": result[0]}), 200

        # ── CREATE or UPDATE or DELETE ───────────────────────────────────────
        if request.method != 'DELETE':
            data = request.get_json()
            print("Incoming JSON Payload:", data)

        if request.method == 'POST' or request.method == 'PATCH':
            if not data:
                return jsonify({"error": "JSON payload required"}), 400

            required_fields = ['kft_distribution_name', 'is_active']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return jsonify({"error": "missing fields", "fields": missing}), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()
            status = '1'

            if request.method == 'POST':
                # CREATE
                query = """
                    INSERT INTO tbl_kft_distribution 
                    (kft_distribution_name, is_active, status, 
                     created_by, created_date, modified_by, modified_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING kft_distribution_id
                """
                params = (
                    data['kft_distribution_name'],
                    data['is_active'],
                    status,
                    user_id, now, user_id, now
                )
                result = execute_command(query, params)
                new_id = result if result else None

                return jsonify({"status": "created", "kft_distribution_id": new_id}), 201

            else:  # PATCH
                if not distribution_id:
                    return jsonify({"error": "distribution_id required"}), 400

                query = """
                    UPDATE tbl_kft_distribution 
                    SET kft_distribution_name = %s,
                        is_active = %s,
                        status = %s,
                        modified_by = %s,
                        modified_date = %s
                    WHERE kft_distribution_id = %s
                    AND status != 3
                    RETURNING kft_distribution_id
                """
                params = (
                    data['kft_distribution_name'],
                    data['is_active'],
                    status,
                    user_id, now, distribution_id
                )
                result = execute_command(query, params)

                # if not result:
                #     return jsonify({"error": "KFT distribution not found"}), 404

                return jsonify({"status": "updated"}), 200

        else:  # DELETE (soft delete - update status to 2)
            if not distribution_id:
                return jsonify({"error": "distribution_id required"}), 400

            # Check if distribution is being used
            check_query = """
                SELECT COUNT(*) as count 
                FROM tbl_branches 
                WHERE kft_distribution = %s
            """
            check_result = fetch_records(check_query, (distribution_id,))

            if check_result and check_result[0]['count'] > 0:
                return jsonify({
                    "error": "Cannot delete. KFT distribution is being used by branches."
                }), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()

            query = """
                UPDATE tbl_kft_distribution 
                SET status = 2, 
                    modified_by = %s, 
                    modified_date = %s
                WHERE kft_distribution_id = %s
                AND status != 3
                RETURNING kft_distribution_id
            """
            result = execute_command(query, (user_id, now, distribution_id))

            # if not result:
            #     return jsonify({"error": "KFT distribution not found"}), 404

            return jsonify({"status": "deleted"}), 200

    except Exception as exc:
        print("api_kft_distribution_crud error:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500