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
    print(f"→ api_branch_crud | method={request.method} | branch_id={branch_id} | user={identity}")

    if not (is_admin() or is_executive_approver()):
        print("   → Access denied: not admin or executive approver")
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        # ── GET single branch ────────────────────────────────────────────────
        if request.method == 'GET':
            if not branch_id:
                print("   → GET: missing branch_id")
                return jsonify({"error": "branch_id required"}), 400

            query = f"""
                SELECT branch_id, branch, branch_code, branch_name, role, area, area_name,
                       branch_manager, email, bank_id, bank_distribution, kft_distribution,
                       national_council_distribution, live_branch, created_by, created_date,
                       modified_by, modified_date
                FROM tbl_branches
                WHERE branch_id = {branch_id} AND live_branch != 3
            """

            print("   → GET query:")
            print(query)

            result = fetch_records(query)

            if not result:
                print(f"   → Branch not found or deleted: {branch_id}")
                return jsonify({"error": "branch not found or deleted"}), 404

            print(f"   → GET success → branch {branch_id}")
            return jsonify({"status": "ok", "data": result[0]}), 200

        # ── CREATE & UPDATE shared logic ─────────────────────────────────────
        data = request.get_json(silent=True)
        print(f"   → JSON payload: {data}")

        if not data:
            print("   → No valid JSON payload")
            return jsonify({"error": "JSON payload required"}), 400

        required_fields = [
            'branch', 'branch_code', 'branch_name', 'role', 'area',
            'area_name', 'branch_manager', 'email', 'bank_id', 'live_branch'
        ]

        missing = [f for f in required_fields if f not in data]
        if missing:
            print(f"   → Missing required fields: {missing}")
            return jsonify({"error": "missing fields", "fields": missing}), 400

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = get_current_user_id()
        print(f"   → user_id={user_id}  now={now}")

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

        print("   → Prepared fields:")
        for k, v in sorted(fields.items()):
            print(f"      {k: <28}: {v}")

        # ────────────────────────────────────────────────────────────────
        # Helper: format value for SQL (NO surrounding quotes here!)
        def sql_value(v):
            if v is None:
                return 'NULL'
            if isinstance(v, str):
                return f"'{escape_sql_string(v)}'"
            # numbers, booleans, etc → direct insertion
            return str(v)

        # ── CREATE (POST) ────────────────────────────────────────────────
        if request.method == 'POST':
            query = f"""
                INSERT INTO tbl_branches (
                    branch_code, branch_name, role, area, email, bank_id,
                    bank_distribution, kft_distribution, national_council_distribution,
                    live_branch, created_by, created_date, modified_by, modified_date,
                    area_name, branch, branch_manager
                ) VALUES (
                    {sql_value(fields['branch_code'])},
                    {sql_value(fields['branch_name'])},
                    {sql_value(fields['role'])},
                    {sql_value(fields['area'])},
                    {sql_value(fields['email'])},
                    {sql_value(fields['bank_id'])},
                    {sql_value(fields['bank_distribution'])},
                    {sql_value(fields['kft_distribution'])},
                    {sql_value(fields['national_council_distribution'])},
                    {sql_value(fields['live_branch'])},
                    {sql_value(user_id)},
                    {sql_value(now)},
                    {sql_value(user_id)},
                    {sql_value(now)},
                    {sql_value(fields['area_name'])},
                    {sql_value(fields['branch'])},
                    {sql_value(fields['branch_manager'])}
                )
                RETURNING branch_id
            """

            print("   → INSERT query:")
            print(query)

            new_id = execute_command(query)

            if new_id is not None:
                print(f"   → Created branch_id = {new_id}")
                return jsonify({"status": "created", "branch_id": new_id}), 201
            else:
                print("   → INSERT returned no branch_id")
                return jsonify({"status": "created", "branch_id": None}), 201

        # ── UPDATE (PATCH) ───────────────────────────────────────────────
        else:  # PATCH
            if not branch_id:
                print("   → PATCH missing branch_id")
                return jsonify({"error": "branch_id required"}), 400

            set_clauses = []

            for key, value in fields.items():
                if key in data:  # only fields actually sent
                    set_clauses.append(f"{key} = {sql_value(value)}")

            if not set_clauses:
                print("   → No fields to update")
                return jsonify({"error": "no fields to update"}), 400

            set_clause = ", ".join(set_clauses)

            query = f"""
                UPDATE tbl_branches
                SET {set_clause},
                    modified_by = {sql_value(user_id)},
                    modified_date = {sql_value(now)}
                WHERE branch_id = {branch_id}
                  AND live_branch != 3
                RETURNING branch_id
            """

            print("   → UPDATE query:")
            print(query)

            result = execute_command(query)

            if result is not None:
                print(f"   → Updated branch_id = {result}")
                return jsonify({"status": "updated"}), 200
            else:
                print(f"   → Branch not found or deleted: {branch_id}")
                return jsonify({"error": "branch not found or already deleted"}), 404

    except Exception as exc:
        print("═" * 60)
        print("api_branch_crud EXCEPTION")
        print("═" * 60)
        print(f"Type:    {type(exc).__name__}")
        print(f"Message: {exc}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "internal server error"}), 500


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
