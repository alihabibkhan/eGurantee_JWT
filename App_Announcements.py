from imports import *
from application import application


# Announcements API - JWT Protected
@application.route('/api/announcements', methods=['GET'])
@jwt_required()
def api_get_announcements():
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        # Fetch only non-deleted records (status = 1)
        query = """
            SELECT 
                id, title, message, start_date, end_date, is_active, priority,
                background_color, text_color, link_url, link_text,
                created_at, created_by
            FROM announcements
            WHERE status = 1
            ORDER BY priority DESC, created_at DESC
        """
        announcements = fetch_records(query)

        return jsonify({
            "success": True,
            "data": announcements
        }), 200

    except Exception as exc:
        print("api_get_announcements error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to fetch announcements"
        }), 500


@application.route('/api/announcements/<int:ann_id>', methods=['GET'])
@jwt_required()
def api_get_announcement(ann_id):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        query = """
            SELECT 
                id, title, message, start_date, end_date, is_active, priority,
                background_color, text_color, link_url, link_text,
                created_at, created_by
            FROM announcements 
            WHERE id = %s AND status = 1
        """
        result = fetch_records(query, (ann_id,))

        if not result:
            return jsonify({"error": "Announcement not found"}), 404

        return jsonify({
            "success": True,
            "data": result[0]
        }), 200

    except Exception as exc:
        print("api_get_announcement error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to fetch announcement"
        }), 500


@application.route('/api/announcements', methods=['POST'])
@jwt_required()
def api_create_announcement():
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['title', 'message']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({"error": "missing fields", "fields": missing}), 400

        # Get form data
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        is_active = data.get('is_active', True)
        priority = data.get('priority', 0)
        background_color = data.get('background_color', '#9b2ab8')
        text_color = data.get('text_color', '#ffffff')
        link_url = data.get('link_url', '').strip()
        link_text = data.get('link_text', '').strip()

        current_user_id = get_current_user_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert new announcement
        query = """
            INSERT INTO announcements 
            (title, message, start_date, end_date, is_active, priority,
             background_color, text_color, link_url, link_text, created_by, 
             created_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            title, message, start_date, end_date, is_active, priority,
            background_color, text_color, link_url if link_url else None,
            link_text if link_text else None, current_user_id, current_time, 1
        )

        result = execute_command(query, params)
        new_id = result if result else None

        return jsonify({
            "success": True,
            "message": "Announcement created successfully",
            "id": new_id
        }), 201

    except Exception as exc:
        print("api_create_announcement error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to create announcement"
        }), 500


@application.route('/api/announcements/<int:ann_id>', methods=['PUT'])
@jwt_required()
def api_update_announcement(ann_id):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        data = request.get_json()

        # Check if announcement exists
        check_query = "SELECT id FROM announcements WHERE id = %s AND status = 1"
        existing = fetch_records(check_query, (ann_id,))

        if not existing:
            return jsonify({"error": "Announcement not found"}), 404

        # Get form data
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        is_active = data.get('is_active', True)
        priority = data.get('priority', 0)
        background_color = data.get('background_color', '#9b2ab8')
        text_color = data.get('text_color', '#ffffff')
        link_url = data.get('link_url', '').strip()
        link_text = data.get('link_text', '').strip()

        # Update announcement
        query = """
            UPDATE announcements 
            SET title = %s,
                message = %s,
                start_date = %s,
                end_date = %s,
                is_active = %s,
                priority = %s,
                background_color = %s,
                text_color = %s,
                link_url = %s,
                link_text = %s
            WHERE id = %s AND status = 1
        """
        params = (
            title, message, start_date, end_date, is_active, priority,
            background_color, text_color, link_url if link_url else None,
            link_text if link_text else None, ann_id
        )

        execute_command(query, params)

        return jsonify({
            "success": True,
            "message": "Announcement updated successfully"
        }), 200

    except Exception as exc:
        print("api_update_announcement error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to update announcement"
        }), 500


@application.route('/api/announcements/<int:ann_id>', methods=['DELETE'])
@jwt_required()
def api_delete_announcement(ann_id):
    identity = get_jwt_identity()
    if not (is_admin() or is_executive_approver()):
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        # Soft delete - set status = 2
        query = """
            UPDATE announcements 
            SET status = 2
            WHERE id = %s AND status = 1
            RETURNING id
        """
        result = execute_command(query, (ann_id,))

        # if not result:
        #     return jsonify({"error": "Announcement not found"}), 404

        return jsonify({
            "success": True,
            "message": "Announcement deleted successfully"
        }), 200

    except Exception as exc:
        print("api_delete_announcement error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to delete announcement"
        }), 500


# Public endpoint for marquee (no authentication required)
@application.route('/api/announcements/marquee', methods=['GET'])
def api_get_marquee_content():
    try:
        limit = request.args.get('limit', default=1, type=int)

        query = """
            SELECT 
                title,
                message,
                link_url,
                link_text,
                background_color,
                text_color,
                priority
            FROM announcements
            WHERE is_active = TRUE
              AND status = 1
              AND (start_date IS NULL OR start_date <= NOW())
              AND (end_date IS NULL OR end_date >= NOW())
            ORDER BY priority DESC, created_at DESC
            LIMIT %s
        """
        records = fetch_records(query, (limit,))

        marquee_items = []
        for row in records:
            # Build rich content with optional link
            content = row['message'].strip()

            if row['link_url'] and row['link_text']:
                content = f'{content} <a href="{row["link_url"]}" target="_blank" style="color: inherit; text-decoration: underline;">{row["link_text"]}</a>'

            style = ""
            if row['background_color']:
                style += f"background: {row['background_color']}; "
            if row['text_color']:
                style += f"color: {row['text_color']}; "

            marquee_items.append({
                'content': content,
                'style': style.strip(),
                'priority': row['priority']
            })

        return jsonify({
            "success": True,
            "data": marquee_items
        }), 200

    except Exception as exc:
        print("api_get_marquee_content error:", str(exc))
        return jsonify({
            "success": False,
            "error": "Failed to fetch marquee content"
        }), 500