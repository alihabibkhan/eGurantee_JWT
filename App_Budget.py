from imports import *
from application import application


# Budget Management API - Simple GET endpoint only (matches original functionality)
@application.route('/api/budget', methods=['GET'])
@jwt_required()
def api_get_budget():
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        # Fetch all budget info grouped by branch - exactly like the original
        budget_data = get_all_budget_info_grouped_by_branch()

        # Return in the same structure as the original template expected
        return jsonify({
            "success": True,
            "data": budget_data
        }), 200

    except Exception as exc:
        print("api_get_budget error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to fetch budget data"
        }), 500
