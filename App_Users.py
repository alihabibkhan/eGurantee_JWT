from imports import *
from application import application


def generate_random_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(11))
    return password


# ==================== USER MANAGEMENT API ROUTES ====================

@application.route('/api/users', methods=['GET'])
def api_get_all_users():
    """API endpoint to get all users"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        users = get_all_user_data()
        return jsonify({
            'success': True,
            'data': users
        }), 200
    except Exception as e:
        print('api_get_all_users exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-management-data', methods=['GET'])
def api_get_user_management_data():
    """API endpoint to get all data for user management dashboard"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = {
            'users': get_all_user_data(),
            'branches': get_all_branches_info(),
            'privileges': get_all_user_privileges(),
            'service_terms': get_all_user_service_terms(),
            'branch_roles': get_all_branch_roles()
        }

        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        print('api_get_user_management_data exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """API endpoint to get a single user by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT u.user_id, u.name, u.email, u.rights, u.signature, u.scan_sign, u.active, 
                   u.created_by, u.created_date, u.volunteer_id, u.gender, u.dob, u.phone, 
                   u.country_of_residence, u.date_of_joining, u.orientation_completed_on, 
                   u.manager_id, u.assigned_branch as assigned_branch_roles, u.date_of_retirement, u.reason,
                   m.name as manager_name
            FROM tbl_users u 
            LEFT JOIN tbl_users m ON u.manager_id = m.user_id
            WHERE u.user_id = '{user_id}'
        """
        user = fetch_records(query)
        user = user[0] if user else None

        if user:
            # Don't send binary signature data in JSON
            if 'scan_sign' in user:
                del user['scan_sign']

            # Get user privileges
            priv_query = f"""
                SELECT * FROM tbl_user_privileges 
                WHERE user_id = '{user_id}' AND status != 0
            """
            user['privileges'] = fetch_records(priv_query)

            # Get user service terms
            terms_query = f"""
                SELECT * FROM tbl_user_service_terms 
                WHERE user_id = '{user_id}' AND status != 0
            """
            user['service_terms'] = fetch_records(terms_query)

            return jsonify({
                'success': True,
                'data': {'user': user}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404

    except Exception as e:
        print('api_get_user exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users', methods=['POST'])
def api_create_user():
    """API endpoint to create a new user"""
    try:
        print("→ api_create_user called")

        if not is_login() or not (is_admin() or is_executive_approver()):
            print("→ Unauthorized access attempt")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        print("→ Authorization passed")

        data = request.get_json()
        print("→ Received JSON data:", data)

        name = data.get('name')
        email = data.get('email')
        rights = data.get('rights')
        signature = data.get('signature')
        active = data.get('active', '1')
        gender = data.get('gender')
        dob = data.get('dob')
        phone = data.get('phone')
        country_of_residence = data.get('country_of_residence')
        date_of_joining = data.get('date_of_joining')
        orientation_completed_on = data.get('orientation_completed_on')
        manager_id = data.get('manager_id')
        assigned_branches = data.get('assigned_branches', [])
        date_of_retirement = data.get('date_of_retirement')
        reason = data.get('reason')

        print(f"→ name = {name}")
        print(f"→ email = {email}")
        print(f"→ rights = {rights}")
        print(f"→ assigned_branches = {assigned_branches}")

        # Handle NULL values for optional fields
        gender = f"'{gender}'" if gender else 'NULL'
        dob = f"'{dob}'" if dob else 'NULL'
        phone = f"'{phone}'" if phone else 'NULL'
        country_of_residence = f"'{country_of_residence}'" if country_of_residence else 'NULL'
        date_of_joining = f"'{date_of_joining}'" if date_of_joining else 'NULL'
        orientation_completed_on = f"'{orientation_completed_on}'" if orientation_completed_on else 'NULL'
        manager_id = f"'{manager_id}'" if manager_id else 'NULL'
        assigned_branch = f"ARRAY[{','.join(map(str, assigned_branches))}]::INTEGER[]" if assigned_branches else 'NULL'
        signature = f"'{signature}'" if signature else 'NULL'
        date_of_retirement = f"'{date_of_retirement}'" if date_of_retirement else 'NULL'
        reason = f"'{reason}'" if reason else 'NULL'

        print("→ Prepared SQL-safe values:")
        print(f"   gender = {gender}")
        print(f"   dob = {dob}")
        print(f"   assigned_branch = {assigned_branch}")

        # Generate password
        password = generate_random_password()
        hashed_password = generate_password_hash(password)
        print("→ Generated password (plain):", password)
        print("→ Hashed password length:", len(hashed_password))

        insert_query = f"""
            INSERT INTO tbl_users (
                name, email, rights, password, signature, active, created_by, created_date,
                gender, dob, phone, country_of_residence, date_of_joining, orientation_completed_on,
                manager_id, assigned_branch, date_of_retirement, reason
            ) VALUES (
                '{name}', '{email}', {rights}, '{hashed_password}', {signature}, {active}, 
                '{str(get_current_user_id())}', '{str(datetime.now())}', {gender}, {dob}, {phone}, 
                {country_of_residence}, {date_of_joining}, {orientation_completed_on}, 
                {manager_id}, {assigned_branch}, {date_of_retirement}, {reason}
            ) RETURNING user_id
        """

        print("→ Final INSERT query:")
        print(insert_query.replace("    ", "").strip())   # cleaner output

        result = execute_command(insert_query)
        print("→ execute_command result:", result)

        new_user_id = result
        print("→ Created user_id:", new_user_id)

        # Send email with credentials
        url = "https://egurantee-hlut.onrender.com/"
        subject = "Welcome to eGurantee System"
        html_message = f"""
            <h3>Here are your credentials</h3>
            <p>Email: {email}</p>
            <p>Password: {password}</p>
            <a href="{url}">You can login through this link.</a>
        """

        print("→ Preparing to send email to:", email)

        from Model_Email import send_email
        send_email(subject, [email], None, html_message=html_message)
        print("→ Email function called")

        print("→ Request completed successfully")
        return jsonify({
            'success': True,
            'message': 'User created successfully. Password has been sent to the user.',
            'data': {'user_id': new_user_id}
        }), 201

    except Exception as e:
        print('api_create_user exception:- ', str(e))
        import traceback
        print("→ Full traceback:")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    """API endpoint to update an existing user"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        name = data.get('name')
        email = data.get('email')
        rights = data.get('rights')
        signature = data.get('signature')
        active = data.get('active', '1')
        gender = data.get('gender')
        dob = data.get('dob')
        phone = data.get('phone')
        country_of_residence = data.get('country_of_residence')
        date_of_joining = data.get('date_of_joining')
        orientation_completed_on = data.get('orientation_completed_on')
        manager_id = data.get('manager_id')
        assigned_branches = data.get('assigned_branches', [])
        date_of_retirement = data.get('date_of_retirement')
        reason = data.get('reason')

        # Handle NULL values for optional fields
        gender = f"'{gender}'" if gender else 'NULL'
        dob = f"'{dob}'" if dob else 'NULL'
        phone = f"'{phone}'" if phone else 'NULL'
        country_of_residence = f"'{country_of_residence}'" if country_of_residence else 'NULL'
        date_of_joining = f"'{date_of_joining}'" if date_of_joining else 'NULL'
        orientation_completed_on = f"'{orientation_completed_on}'" if orientation_completed_on else 'NULL'
        manager_id = f"'{manager_id}'" if manager_id else 'NULL'
        assigned_branch = f"ARRAY[{','.join(map(str, assigned_branches))}]::INTEGER[]" if assigned_branches else 'NULL'
        signature = f"'{signature}'" if signature else 'NULL'
        date_of_retirement = f"'{date_of_retirement}'" if date_of_retirement else 'NULL'
        reason = f"'{reason}'" if reason else 'NULL'

        update_query = f"""
            UPDATE tbl_users 
            SET name = '{name}', email = '{email}', rights = {rights}, signature = {signature}, 
                active = {active}, gender = {gender}, dob = {dob}, phone = {phone}, 
                country_of_residence = {country_of_residence}, date_of_joining = {date_of_joining}, 
                orientation_completed_on = {orientation_completed_on}, manager_id = {manager_id}, 
                date_of_retirement = {date_of_retirement}, reason = {reason},
                assigned_branch = {assigned_branch}
            WHERE user_id = '{user_id}'
        """

        execute_command(update_query)

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        }), 200

    except Exception as e:
        print('api_update_user exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users/<int:user_id>/signature', methods=['POST'])
def api_upload_user_signature(user_id):
    """API endpoint to upload user signature image"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        if 'scan_sign' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400

        file = request.files['scan_sign']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        # Read file as binary
        scan_sign_data = file.read()
        binary_data = psycopg2.Binary(scan_sign_data)

        update_query = f"""
            UPDATE tbl_users 
            SET scan_sign = %s
            WHERE user_id = '{user_id}'
        """

        execute_command(update_query, (binary_data,))

        return jsonify({
            'success': True,
            'message': 'Signature uploaded successfully'
        }), 200

    except Exception as e:
        print('api_upload_user_signature exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users/<int:user_id>/signature', methods=['GET'])
def api_get_user_signature(user_id):
    """API endpoint to get user signature image"""
    try:
        if not is_login():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT scan_sign 
            FROM tbl_users 
            WHERE user_id = '{user_id}' AND active = '1'
        """
        result = fetch_records(query)

        if result and result[0]['scan_sign']:
            # Return base64 encoded image
            import base64
            image_base64 = base64.b64encode(result[0]['scan_sign']).decode('utf-8')
            return jsonify({
                'success': True,
                'data': {
                    'image': image_base64,
                    'mime_type': 'image/jpeg'  # You might want to detect this
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Signature not found'
            }), 404

    except Exception as e:
        print('api_get_user_signature exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """API endpoint to soft delete a user"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_users 
            SET active = '0'
            WHERE user_id = '{user_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_user exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== USER PRIVILEGES API ====================

@application.route('/api/users/<int:user_id>/privileges', methods=['GET'])
def api_get_user_privileges(user_id):
    """API endpoint to get all privileges for a user"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT * FROM tbl_user_privileges 
            WHERE user_id = '{user_id}' AND status != 0
        """
        privileges = fetch_records(query)

        return jsonify({
            'success': True,
            'data': privileges
        }), 200

    except Exception as e:
        print('api_get_user_privileges exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-privileges', methods=['POST'])
def api_create_user_privilege():
    """API endpoint to create a new user privilege"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        user_id = data.get('user_id')
        role = data.get('role')
        responsibility = data.get('responsibility')
        committee = data.get('committee')
        status = data.get('status', 1)

        created_by = str(get_current_user_id())
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        insert_query = f"""
            INSERT INTO tbl_user_privileges (
                user_id, role, responsibility, committee, status, 
                created_by, created_date, modified_by, modified_date
            ) VALUES (
                '{user_id}', '{role}', '{responsibility}', '{committee}', {status}, 
                '{created_by}', '{current_time}', '{created_by}', '{current_time}'
            ) RETURNING id
        """

        result = execute_command(insert_query)
        new_id = result

        return jsonify({
            'success': True,
            'message': 'User privilege created successfully',
            'data': {'id': new_id}
        }), 201

    except Exception as e:
        print('api_create_user_privilege exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-privileges/<int:privilege_id>', methods=['PUT'])
def api_update_user_privilege(privilege_id):
    """API endpoint to update a user privilege"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        user_id = data.get('user_id')
        role = data.get('role')
        responsibility = data.get('responsibility')
        committee = data.get('committee')
        status = data.get('status', 1)

        modified_by = str(get_current_user_id())
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        update_query = f"""
            UPDATE tbl_user_privileges
            SET user_id = '{user_id}', role = '{role}', responsibility = '{responsibility}',
                committee = '{committee}', status = {status}, modified_by = '{modified_by}',
                modified_date = '{current_time}'
            WHERE id = '{privilege_id}'
        """

        print('update_query')
        print(update_query)

        execute_command(update_query)

        return jsonify({
            'success': True,
            'message': 'User privilege updated successfully'
        }), 200

    except Exception as e:
        print('api_update_user_privilege exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-privileges/<int:privilege_id>', methods=['DELETE'])
def api_delete_user_privilege(privilege_id):
    """API endpoint to soft delete a user privilege"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_user_privileges 
            SET status = 0
            WHERE id = '{privilege_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'User privilege deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_user_privilege exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== USER SERVICE TERMS API ====================

@application.route('/api/users/<int:user_id>/service-terms', methods=['GET'])
def api_get_user_service_terms(user_id):
    """API endpoint to get all service terms for a user"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT * FROM tbl_user_service_terms 
            WHERE user_id = '{user_id}' AND status != 0
        """
        terms = fetch_records(query)

        return jsonify({
            'success': True,
            'data': terms
        }), 200

    except Exception as e:
        print('api_get_user_service_terms exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-service-terms', methods=['POST'])
def api_create_user_service_term():
    """API endpoint to create a new user service term"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        user_id = data.get('user_id')
        term = data.get('term')
        tenure_cap = data.get('tenure_cap')
        actual_end_date = data.get('actual_end_date')
        month_served = data.get('month_served')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        status = data.get('status', 1)

        created_by = str(get_current_user_id())
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        to_date_value = f"'{to_date}'" if to_date else 'NULL'
        actual_end_date_value = f"'{actual_end_date}'" if actual_end_date else 'NULL'

        insert_query = f"""
            INSERT INTO tbl_user_service_terms (
                user_id, term, from_date, to_date, status, created_by, created_date, 
                modified_by, modified_date, tenure_cap, actual_end_date, month_served
            ) VALUES (
                '{user_id}', '{term}', '{from_date}', {to_date_value}, {status}, 
                '{created_by}', '{current_time}', '{created_by}', '{current_time}', 
                '{tenure_cap}', {actual_end_date_value}, '{month_served}'
            ) RETURNING id
        """

        result = execute_command(insert_query)
        new_id = result

        return jsonify({
            'success': True,
            'message': 'User service term created successfully',
            'data': {'id': new_id}
        }), 201

    except Exception as e:
        print('api_create_user_service_term exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-service-terms/<int:term_id>', methods=['PUT'])
def api_update_user_service_term(term_id):
    """API endpoint to update a user service term"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        user_id = data.get('user_id')
        term = data.get('term')
        tenure_cap = data.get('tenure_cap')
        actual_end_date = data.get('actual_end_date')
        month_served = data.get('month_served')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        status = data.get('status', 1)

        modified_by = str(get_current_user_id())
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        to_date_value = f"'{to_date}'" if to_date else 'NULL'
        actual_end_date_value = f"'{actual_end_date}'" if actual_end_date else 'NULL'

        update_query = f"""
            UPDATE tbl_user_service_terms
            SET user_id = '{user_id}', term = '{term}', from_date = '{from_date}',
                to_date = {to_date_value}, status = {status}, tenure_cap = '{tenure_cap}',
                actual_end_date = {actual_end_date_value}, month_served = '{month_served}',
                modified_by = '{modified_by}', modified_date = '{current_time}'
            WHERE id = '{term_id}'
        """

        execute_command(update_query)

        return jsonify({
            'success': True,
            'message': 'User service term updated successfully'
        }), 200

    except Exception as e:
        print('api_update_user_service_term exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/user-service-terms/<int:term_id>', methods=['DELETE'])
def api_delete_user_service_term(term_id):
    """API endpoint to soft delete a user service term"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_user_service_terms 
            SET status = 0
            WHERE id = '{term_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'User service term deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_user_service_term exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== BRANCHES API (Helper) ====================

@application.route('/api/branches/data', methods=['GET'])
def api_get_all_branches():
    """API endpoint to get all branches"""
    try:
        if not is_login():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        branches = get_all_branches_info()
        return jsonify({
            'success': True,
            'data': branches
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== USER PRIVILEGES MASTER DATA API ====================

@application.route('/api/user-privileges-master', methods=['GET'])
def api_get_all_user_privileges_master():
    """API endpoint to get all user privileges master data"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        privileges = get_all_user_privileges()
        return jsonify({
            'success': True,
            'data': privileges
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== USER SERVICE TERMS MASTER DATA API ====================

@application.route('/api/user-service-terms-master', methods=['GET'])
def api_get_all_user_service_terms_master():
    """API endpoint to get all user service terms master data"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        terms = get_all_user_service_terms()
        return jsonify({
            'success': True,
            'data': terms
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== BRANCH ROLES API ====================

@application.route('/api/branch-roles', methods=['GET'])
def api_get_all_branch_roles():
    """API endpoint to get all branch roles"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        roles = get_all_branch_roles()
        return jsonify({
            'success': True,
            'data': roles
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500