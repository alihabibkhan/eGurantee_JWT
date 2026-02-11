from imports import *
from application import application


# National Council Distribution Routes
# National Council Distribution CRUD API
@application.route('/api/national-council-distributions', methods=['POST'])
@application.route('/api/national-council-distributions/<int:distribution_id>', methods=['GET', 'PATCH', 'DELETE'])
@jwt_required()
def api_national_council_distribution_crud(distribution_id=None):

    print("--------------------------------------------------")
    print("NATIONAL COUNCIL DISTRIBUTION API CALLED")
    print("Request Method:", request.method)
    print("Distribution ID:", distribution_id)

    identity = get_jwt_identity()
    print("JWT Identity:", identity)

    if not (is_admin() or is_executive_approver()):
        print("Permission denied")
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        # ====================== GET ======================
        if request.method == 'GET':
            print("Processing GET request")

            if not distribution_id:
                print("Missing distribution_id for GET")
                return jsonify({"error": "distribution_id required"}), 400

            query = """
                SELECT national_council_distribution_id, national_council_distribution_name, 
                       is_active, status, created_by, created_date, modified_by, modified_date
                FROM tbl_national_council_distribution 
                WHERE national_council_distribution_id = %s AND status != 3
            """
            print("Executing SELECT query:")
            print(query)
            print("Params:", (distribution_id,))

            result = fetch_records(query, (distribution_id,))
            print("Query Result:", result)

            if not result:
                print("Distribution not found")
                return jsonify({"error": "national council distribution not found"}), 404

            print("GET successful")
            return jsonify({"status": "ok", "data": result[0]}), 200

        # ====================== CREATE / UPDATE ======================

        if request.method != 'DELETE':
            data = request.get_json()
            print("Incoming JSON Payload:", data)

        if request.method == 'POST' or request.method == 'PATCH':
            print("Processing", request.method)

            if not data:
                print("No JSON payload provided")
                return jsonify({"error": "JSON payload required"}), 400

            required_fields = ['national_council_distribution_name', 'is_active']
            missing = [f for f in required_fields if f not in data]

            if missing:
                print("Missing required fields:", missing)
                return jsonify({"error": "missing fields", "fields": missing}), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()
            status = '1'

            print("User ID:", user_id)
            print("Timestamp:", now)

            # ---------------- POST ----------------
            if request.method == 'POST':
                print("Creating new distribution")

                query = """
                    INSERT INTO tbl_national_council_distribution 
                    (national_council_distribution_name, is_active, status, 
                     created_by, created_date, modified_by, modified_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING national_council_distribution_id
                """
                params = (
                    data['national_council_distribution_name'],
                    data['is_active'],
                    status,
                    user_id, now, user_id, now
                )

                print("Executing INSERT query:")
                print(query)
                print("Params:", params)

                result = execute_command(query, params)
                print("Insert Result:", result)

                new_id = result if result else None

                print("CREATE successful, New ID:", new_id)
                return jsonify({
                    "status": "created",
                    "national_council_distribution_id": new_id
                }), 201

            # ---------------- PATCH ----------------
            else:
                print("Updating distribution")

                if not distribution_id:
                    print("Missing distribution_id for PATCH")
                    return jsonify({"error": "distribution_id required"}), 400

                query = """
                    UPDATE tbl_national_council_distribution 
                    SET national_council_distribution_name = %s,
                        is_active = %s,
                        status = %s,
                        modified_by = %s,
                        modified_date = %s
                    WHERE national_council_distribution_id = %s
                    AND status != 3
                    RETURNING national_council_distribution_id
                """
                params = (
                    data['national_council_distribution_name'],
                    data['is_active'],
                    status,
                    user_id, now, distribution_id
                )

                print("Executing UPDATE query:")
                print(query)
                print("Params:", params)

                result = execute_command(query, params)
                print("Update Result:", result)

                # if not result:
                #     print("Distribution not found for update")
                #     return jsonify({"error": "national council distribution not found"}), 404

                print("UPDATE successful")
                return jsonify({"status": "updated"}), 200

        # ====================== DELETE ======================
        else:
            print("Processing DELETE request")

            if not distribution_id:
                print("Missing distribution_id for DELETE")
                return jsonify({"error": "distribution_id required"}), 400

            check_query = """
                SELECT COUNT(*) as count 
                FROM tbl_branches 
                WHERE national_council_distribution = %s
            """

            print("Checking usage before delete")
            print("Executing:", check_query)
            print("Params:", (distribution_id,))

            check_result = fetch_records(check_query, (distribution_id,))
            print("Usage Check Result:", check_result)

            if check_result and check_result[0]['count'] > 0:
                print("Cannot delete - distribution in use")
                return jsonify({
                    "error": "Cannot delete. Distribution is being used by branches."
                }), 400

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = get_current_user_id()

            query = """
                UPDATE tbl_national_council_distribution 
                SET status = 2, 
                    modified_by = %s, 
                    modified_date = %s
                WHERE national_council_distribution_id = %s
                AND status != 3
                RETURNING national_council_distribution_id
            """

            print("Executing SOFT DELETE query:")
            print(query)
            print("Params:", (user_id, now, distribution_id))

            result = execute_command(query, (user_id, now, distribution_id))
            print("Delete Result:", result)

            # if not result:
            #     print("Distribution not found for delete")
            #     return jsonify({"error": "national council distribution not found"}), 404

            print("DELETE successful")
            return jsonify({"status": "deleted"}), 200

    except Exception as exc:
        print("----- ERROR OCCURRED -----")
        print("Error Type:", type(exc).__name__)
        print("Error Message:", str(exc))
        return jsonify({"status": "error", "message": "internal error"}), 500
