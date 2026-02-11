from imports import *
from application import application


# Bank Distribution Routes
# ────────────────────────────────────────────────
# CREATE - POST /api/bank-distributions
# ────────────────────────────────────────────────
@application.route('/api/bank-distributions', methods=['POST'])
@jwt_required()
def api_create_bank_distribution():
    try:
        if not (is_admin() or is_executive_approver()):  # ← adapt if needed
            return jsonify({"error": "Insufficient permissions"}), 403

        user_id = get_current_user_id()

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "JSON payload required"}), 400

        name = data.get('bank_distribution_name')
        is_active = data.get('is_active')

        if not name:
            return jsonify({"error": "bank_distribution_name is required"}), 400

        # Normalize is_active
        is_active = 1 if is_active in (True, 'true', '1', 1) else 0

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = """
            INSERT INTO tbl_bank_distribution 
            (bank_distribution_name, is_active, status, created_by, created_date, modified_by, modified_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING bank_distribution_id
        """
        params = (name, is_active, 1, user_id, now, user_id, now)

        result = execute_command(query, params)  # ← adjust to your function
        new_id = result if result else None

        if not new_id:
            return jsonify({"error": "Failed to create record"}), 500

        return jsonify({
            "message": "Created successfully",
            "bank_distribution_id": new_id
        }), 200

    except Exception as e:
        print("API create bank distribution error:", str(e))
        return jsonify({"error": "Server error"}), 500


# ────────────────────────────────────────────────
# UPDATE - PUT /api/bank-distributions/<id>
# ────────────────────────────────────────────────
@application.route('/api/bank-distributions/<int:bank_distribution_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def api_update_bank_distribution(bank_distribution_id):

    print("----- UPDATE BANK DISTRIBUTION API CALLED -----")
    print("Bank Distribution ID:", bank_distribution_id)

    try:
        user_id = get_current_user_id()
        print("Current User ID:", user_id)

        data = request.get_json(silent=True)
        print("Incoming JSON Payload:", data)

        if not data:
            print("No JSON payload received")
            return jsonify({"error": "JSON payload required"}), 400

        name = data.get('bank_distribution_name')
        is_active = data.get('is_active')

        print("Parsed Name:", name)
        print("Parsed is_active:", is_active)

        if name is None and is_active is None:
            print("No fields provided for update")
            return jsonify({"error": "No fields to update"}), 400

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Current Timestamp:", now)

        updates = []
        params = []

        if name is not None:
            updates.append("bank_distribution_name = %s")
            params.append(name)
            print("Adding name update")

        # if is_active is not None:
        #     val = 1 if is_active in (True, 'true', '1', 1) else 0
        #     updates.append("is_active = %s")
        #     params.append(val)
        #     print("Converted is_active to:", val)

        updates.append("modified_by = %s")
        params.append(user_id)

        updates.append("modified_date = %s")
        params.append(now)

        params.append(bank_distribution_id)

        query = f"""
            UPDATE tbl_bank_distribution
            SET {', '.join(updates)}
            WHERE bank_distribution_id = %s
              AND status != 3
            RETURNING bank_distribution_id
        """

        print("Executing Query:")
        print(query)
        print("Query Parameters:", params)

        result = execute_command(query, params)
        print("Query Execution Result:", result)

        # if not result:
        #     print("No rows updated. Possibly invalid ID or already deleted.")
        #     return jsonify({"error": "Bank distribution not found or inactive"}), 404

        print("Update successful for ID:", bank_distribution_id)
        print("----- UPDATE SUCCESS -----")

        return jsonify({"message": "Updated successfully"}), 200

    except Exception as e:
        print("----- UPDATE FAILED -----")
        print("Error Type:", type(e).__name__)
        print("Error Message:", str(e))
        return jsonify({"error": "Server error"}), 500



# ────────────────────────────────────────────────
# DELETE (soft) - DELETE /api/bank-distributions/<id>
# ────────────────────────────────────────────────
@application.route('/api/bank-distributions/<int:bank_distribution_id>', methods=['DELETE'])
@jwt_required()
def api_delete_bank_distribution(bank_distribution_id):
    print("----- DELETE BANK DISTRIBUTION API CALLED -----")
    print("Received bank_distribution_id:", bank_distribution_id)

    try:
        user_id = get_current_user_id()
        print("Current User ID:", user_id)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Current Timestamp:", now)

        query = """
            UPDATE tbl_bank_distribution
            SET status = 2,
                modified_by = %s,
                modified_date = %s
            WHERE bank_distribution_id = %s
              AND status != 3
            RETURNING bank_distribution_id
        """
        print("Executing Query:")
        print(query)

        params = (user_id, now, bank_distribution_id)
        print("Query Parameters:", params)

        result = execute_command(query, params)
        print("Query Execution Result:", result)

        # if not result:
        #     print("No rows affected. Possibly invalid ID or already deleted.")
        #     return jsonify({"error": "Bank distribution not found or already deleted"}), 404

        print("Delete successful for ID:", bank_distribution_id)
        print("----- DELETE SUCCESS -----")

        return jsonify({"message": "Deleted successfully"}), 200

    except Exception as e:
        print("----- DELETE FAILED -----")
        print("Error Type:", type(e).__name__)
        print("Error Message:", str(e))
        return jsonify({"error": "Server error"}), 500


# ────────────────────────────────────────────────
# GET ONE - GET /api/bank-distributions/<id>
# ────────────────────────────────────────────────
@application.route('/api/bank-distributions/<int:bank_distribution_id>', methods=['GET'])
@jwt_required()
def api_get_bank_distribution(bank_distribution_id):
    try:
        query = """
            SELECT 
                bank_distribution_id,
                bank_distribution_name,
                is_active,
                status,
                created_by,
                created_date,
                modified_by,
                modified_date
            FROM tbl_bank_distribution
            WHERE bank_distribution_id = %s
              AND status != 3
        """
        result = fetch_records(query, (bank_distribution_id,))  # ← your function

        if not result:
            return jsonify({"error": "Not found"}), 404

        return jsonify(result[0]), 200

    except Exception as e:
        print("API get bank distribution error:", str(e))
        return jsonify({"error": "Server error"}), 500