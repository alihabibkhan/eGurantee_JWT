from imports import *
from application import application



# ───────────────────────────────────────────────
#  GET    /api/branches           → list + metadata
# ───────────────────────────────────────────────
@application.route('/api/branches', methods=['GET'])
@jwt_required()
def api_get_branches():
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    bank_details = get_all_bank_details()

    try:
        payload = {
            "branches": get_all_branches_info(),
            "bank_distributions": get_all_bank_distributions(),
            "national_council_distributions": get_all_national_council_distributions(),
            "kft_distributions": get_all_kft_distributions(),
            "branch_roles": get_all_branch_roles(),
            'bank_details': bank_details
        }
        return jsonify({"status": "ok", "data": payload}), 200

    except Exception as exc:
        print("api_get_branches error:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500


# ───────────────────────────────────────────────
#  GET    /api/branches/<int:branch_id>     → detail
#  POST   /api/branches                      → create
#  PATCH  /api/branches/<int:branch_id>      → update
# ───────────────────────────────────────────────
@application.route('/api/branches', methods=['POST'])
@application.route('/api/branches/<int:branch_id>', methods=['GET', 'PATCH'])
@jwt_required()
def api_branch_crud(branch_id=None):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        if request.method == 'GET':
            if not branch_id:
                return jsonify({"error": "branch_id required"}), 400

            query = """
                SELECT branch_id, branch, branch_code, branch_name, role, area, area_name,
                       branch_manager, email, bank_id, bank_distribution, kft_distribution,
                       national_council_distribution, live_branch, created_by, created_date,
                       modified_by, modified_date
                FROM tbl_branches
                WHERE branch_id = %s AND live_branch != 3
            """
            result = fetch_records(query, (branch_id,))
            if not result:
                return jsonify({"error": "branch not found or deleted"}), 404

            return jsonify({"status": "ok", "data": result[0]}), 200

        # ── CREATE or UPDATE ───────────────────────────────────────
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON payload required"}), 400

        required_fields = [
            'branch', 'branch_code', 'branch_name', 'role', 'area',
            'area_name', 'branch_manager', 'email', 'bank_id', 'live_branch'
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({"error": "missing fields", "fields": missing}), 400

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = get_current_user_id()

        fields = {
            "branch": data['branch'],
            "branch_code": data['branch_code'],
            "branch_name": data['branch_name'],
            "role": data['role'],
            "area": data['area'],
            "area_name": data['area_name'],
            "branch_manager": data['branch_manager'],
            "email": data['email'],
            "bank_id": data['bank_id'],
            "bank_distribution": data.get('bank_distribution'),
            "kft_distribution": data.get('kft_distribution'),
            "national_council_distribution": data.get('national_council_distribution'),
            "live_branch": data['live_branch'],
        }

        # Prepare escaped values (still using your escape function)
        escaped = {k: escape_sql_string(v) if isinstance(v, str) else v
                   for k, v in fields.items()}

        if request.method == 'POST':
            # CREATE
            query = """
                INSERT INTO tbl_branches (
                    branch_code, branch_name, role, area, email, bank_id,
                    bank_distribution, kft_distribution, national_council_distribution,
                    live_branch, created_by, created_date, modified_by, modified_date,
                    area_name, branch, branch_manager
                ) VALUES (
                    %(branch_code)s, %(branch_name)s, %(role)s, %(area)s, %(email)s, %(bank_id)s,
                    %(bank_distribution)s, %(kft_distribution)s, %(national_council_distribution)s,
                    %(live_branch)s, %(user_id)s, %(now)s, %(user_id)s, %(now)s,
                    %(area_name)s, %(branch)s, %(branch_manager)s
                )
                RETURNING branch_id
            """
            params = {**escaped, "user_id": user_id, "now": now}
            result = execute_command(query, params)
            new_id = result if result else None

            return jsonify({"status": "created", "branch_id": new_id}), 201

        else:  # PATCH
            if not branch_id:
                return jsonify({"error": "branch_id required"}), 400

            # Build SET clause dynamically (only fields that were sent)
            set_parts = []
            params = {}
            for k, v in escaped.items():
                if k in data:  # only update fields that were actually sent
                    set_parts.append(f"{k} = %({k})s")
                    params[k] = v

            if not set_parts:
                return jsonify({"error": "no fields to update"}), 400

            params["user_id"] = user_id
            params["now"] = now
            params["branch_id"] = branch_id

            set_clause = ", ".join(set_parts)
            query = f"""
                UPDATE tbl_branches
                SET {set_clause},
                    modified_by = %(user_id)s,
                    modified_date = %(now)s
                WHERE branch_id = %(branch_id)s
                AND live_branch != 3
                RETURNING branch_id
            """
            result = execute_command(query, params)

            if not result:
                return jsonify({"error": "branch not found or already deleted"}), 404

            return jsonify({"status": "updated"}), 200

    except Exception as exc:
        print("api_branch_crud error:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500


# ───────────────────────────────────────────────
#  DELETE   /api/branches/<int:branch_id>   (soft delete)
# ───────────────────────────────────────────────
@application.route('/api/branches/<int:branch_id>', methods=['DELETE'])
@jwt_required()
def api_delete_branch(branch_id):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = get_current_user_id()

        query = """
            UPDATE tbl_branches
            SET live_branch = 3,
                modified_by = %s,
                modified_date = %s
            WHERE branch_id = %s
            AND live_branch != 3
            RETURNING branch_id
        """
        result = execute_command(query, (user_id, now, branch_id))

        if not result:
            return jsonify({"error": "branch not found or already deleted"}), 404

        return jsonify({"status": "deleted"}), 200

    except Exception as exc:
        print("api_delete_branch error:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500
