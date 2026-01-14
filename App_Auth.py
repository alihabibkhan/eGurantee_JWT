from imports import *
from application import application
s = URLSafeTimedSerializer(application.config['SECRET_KEY'])


# =============================================
# LOGIN – GET shows form, POST accepts JSON only
# =============================================
@application.route('/login', methods=['GET', 'POST'])
@application.route('/Login', methods=['GET', 'POST'])
def login():

    if is_login():
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('Login.html')

    if not request.is_json:
        return jsonify({"status": "error", "message": "JSON request required"}), 400

    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    # SAFE parameterized query
    query = f"SELECT * FROM tbl_users WHERE email = '{str(email)}'"
    users = fetch_records(query)  # ← MUST support params tuple!

    if not users or not check_password_hash(users[0]['password'], password):
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    user = users[0]

    access_token = create_access_token(identity=str(user['user_id']))

    resp = jsonify({
        "status": "success",
        "message": f"Welcome, {user.get('name', 'User')}",
        "access_token": access_token,
        "user": {
            "user_id": user['user_id'],
            "name": user.get('name'),
            "email": user.get('email'),
            "rights": user.get('rights')
        }
    })

    set_access_cookies(resp, access_token)  # sets access_token_cookie
    return resp, 200


@application.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def profile():
    if not is_login():
        return redirect(url_for('login'))

    current_user_id = get_jwt_identity()

    try:
        # ─── GET: show profile page ───
        if request.method == 'GET':
            query = f"""
                SELECT u."name", u."email", u."signature", u."scan_sign" 
                FROM tbl_users u 
                WHERE u."active" = '1' AND u."user_id" = '{current_user_id}'
            """
            user = fetch_records(query)
            if not user:
                abort(404, description="User not found")
            user = user[0]

            image_base64 = None
            if user.get('scan_sign'):
                image_base64 = base64.b64encode(user['scan_sign']).decode('utf-8')

            content = {
                'is_user_have_sign': is_user_have_sign(),
                'user': user,
                'image_base64': image_base64,
            }

            return render_template('profile.html', result=content)

        # ─── POST: update profile (only JSON accepted) ───
        if not request.is_json:
            return jsonify({"error": "JSON payload required"}), 415

        data = request.get_json()

        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        signature_base64 = data.get('signature')  # optional base64 string

        if not name:
            return jsonify({"error": "Name is required"}), 400

        safe_name = name.replace("'", "''")
        updates = [f'"name" = \'{safe_name}\'']

        if password:
            hashed = generate_password_hash(password)
            updates.append(f'"password" = \'{hashed}\'')

        if signature_base64:
            try:
                image_data = base64.b64decode(signature_base64)
                updates.append(f'"scan_sign" = {psycopg2.Binary(image_data)}')
            except Exception as decode_err:
                return jsonify({"error": "Invalid signature image format"}), 400

        query = f"""
            UPDATE tbl_users
            SET {', '.join(updates)}
            WHERE "user_id" = '{current_user_id}' AND "active" = '1'
        """

        print(query)
        execute_command(query)

        return jsonify({
            "message": "Profile updated successfully",
            "name": name
        })

    except Exception as e:
        print('profile page exception:- ', str(e))
        return jsonify({"error": "Server error"}), 500


@application.route('/Logout', methods=['POST', 'GET'])
@application.route('/logout', methods=['POST', 'GET'])
@jwt_required(optional=True)  # Allow even if token invalid/expired
def logout():
    if request.method == 'GET':
        return render_template('Login.html')

    response = jsonify({
        "status": "success",
        "message": "You have been logged out."
    })

    # If you ever switch to cookies, uncomment this:
    unset_jwt_cookies(response)

    return response, 200


@application.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # Fetch user record using provided query structure
        query = f"""
            SELECT u.name, u.email, u.signature, u.scan_sign 
            FROM tbl_users u 
            WHERE u.active = '1' AND u.email = '{email}'
        """
        user = fetch_records(query)

        if user:
            # Generate reset token
            token = s.dumps(email, salt='password-reset-salt')
            print('token:- ', token)
            reset_url = url_for('reset_password', token=token, _external=True)

            # Email content
            subject = "Password Reset Request"
            html_message = f"""
            <h3>Reset Your Password</h3>
            <p>Click the link below to reset your password. This link will expire in 10 minutes:</p>
            <a href="{reset_url}">Reset Password</a>
            <p>If you did not request a password reset, please ignore this email.</p>
            """

            from Model_Email import send_email

            # Send email using provided function
            if send_email(subject, [email], None, html_message=html_message):
                flash('A password reset link has been sent to your email. It will expire in 10 minutes.', 'success')
            else:
                flash('Failed to send reset email. Please try again.', 'danger')
        else:
            flash('Email not found. Please check your email address.', 'danger')

        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@application.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=600)  # 10 minutes
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('login'))
    except:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        # Fetch user record to verify email
        query = f"""
            SELECT u.name, u.email, u.signature, u.scan_sign 
            FROM tbl_users u 
            WHERE u.active = '1' AND u.email = '{email}'
        """
        user = fetch_records(query)

        if user:
            # Update password (assuming you have a method to hash and set password)
            hashed_password = generate_password_hash(password)  # Replace with your password hashing method
            update_query = f"""
                UPDATE tbl_users 
                SET password = '{hashed_password}' 
                WHERE email = '{email}' AND active = '1'
            """

            execute_command(update_query)

            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('login'))

        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)  # You'll need to create this template



# Reuse your DB connection setup here if needed (e.g., init_db() or similar)

@application.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()  # Expect JSON body from mobile app
        email = data.get('email')
        password = data.get('password')

        print('email:- ', email, ' password:- ', password)

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        # Parameterized query to prevent SQL injection (update fetch_records if it doesn't support params)
        query = "SELECT * FROM tbl_users u WHERE u.email = %s"  # Use %s or ? depending on your DB driver
        user = fetch_records(query, (email,))  # Pass params as tuple
        print('user data:- ', user)

        if user and check_password_hash(user[0]['password'], password):
            # Generate JWT token with user identity (e.g., email or user_id)
            access_token = create_access_token(identity=user[0]['user_id'])
            return jsonify({
                'message': 'Login successful',
                'token': access_token,
                'user': {
                    'userId': user[0]['user_id'],
                    'name': user[0]['name'],
                    'email': user[0]['email'],
                    'rights': user[0]['rights']
                }
            }), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401

    except Exception as e:
        print('API login exception:', str(e))
        return jsonify({'message': 'Server error'}), 500


@application.route('/api/profile', methods=['GET', 'POST'])
@jwt_required()
def api_profile():
    """
    Single endpoint for profile:
    - GET: Retrieve current user's profile
    - POST: Update current user's profile (partial updates supported)
    """
    user_id = get_jwt_identity()  # This is the user_id you set during login

    if request.method == 'GET':
        try:
            query = """
                SELECT user_id, name, email, signature, scan_sign
                FROM tbl_users
                WHERE user_id = %s AND active = '1'
                LIMIT 1
            """
            records = fetch_records(query, params=(user_id,))

            if not records:
                return jsonify({'message': 'User not found or inactive'}), 404

            user = records[0]

            # Convert BYTEA (scan_sign) to base64 for mobile display
            scan_sign_base64 = None
            if user['scan_sign']:
                scan_sign_base64 = base64.b64encode(user['scan_sign']).decode('utf-8')

            return jsonify({
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'signature': user.get('signature'),  # text field, if used
                'scan_sign_base64': scan_sign_base64,  # for image preview
                'has_signature': bool(user['scan_sign'])
            }), 200

        except Exception as e:
            print(f"GET /api/profile error: {str(e)}")
            return jsonify({'message': 'Server error'}), 500

    elif request.method == 'POST':
        try:
            scan_sign_base64 = None
            # For simplicity, support both JSON and multipart/form-data
            # Mobile apps often use multipart when uploading files
            if request.is_json:
                data = request.get_json()
                name = data.get('name')
                password = data.get('password')
                # If sending image as base64 → less common, but possible
                scan_sign_base64 = data.get('scan_sign_base64')
            else:
                # multipart/form-data (recommended for file upload)
                data = request.form
                name = data.get('name')
                password = data.get('password')
                scan_sign_file = request.files.get('scan_sign')

            update_fields = []
            params = []

            if name is not None and name.strip():
                update_fields.append('"name" = %s')
                params.append(name.strip())

            if password and password.strip():
                hashed = generate_password_hash(password.strip())
                update_fields.append('"password" = %s')
                params.append(hashed)

            # Handle signature image upload
            image_data = None
            if 'scan_sign' in request.files and request.files['scan_sign'].filename:
                file = request.files['scan_sign']
                image_data = file.read()
                if image_data:
                    update_fields.append('"scan_sign" = %s')
                    params.append(psycopg2.Binary(image_data))

            # Optional: if you accept base64 image instead (less efficient)
            elif scan_sign_base64:
                try:
                    image_data = base64.b64decode(scan_sign_base64)
                    update_fields.append('"scan_sign" = %s')
                    params.append(psycopg2.Binary(image_data))
                except Exception as decode_err:
                    return jsonify({'message': 'Invalid base64 image data'}), 400

            if not update_fields:
                return jsonify({'message': 'No fields provided to update'}), 400

            update_query = f"""
                UPDATE tbl_users
                SET {", ".join(update_fields)}
                WHERE user_id = %s AND active = '1'
            """
            params.append(user_id)

            result = execute_command(update_query, params=tuple(params))

            if result is None:  # execute_command returns None on success (or last id)
                return jsonify({'message': 'Profile updated successfully'}), 200
            else:
                return jsonify({'message': 'Update failed'}), 500

        except Exception as e:
            print(f"POST /api/profile error: {str(e)}")
            return jsonify({'message': 'Server error during update'}), 500

    else:
        return jsonify({'message': 'Method not allowed'}), 405


@application.route('/api/logout', methods=['POST'])
@jwt_required()
def api_logout():

    response = jsonify({
        "status": "success",
        "message": "You have been logged out."
    })

    return response, 200