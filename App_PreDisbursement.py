from imports import *
from application import application


@application.route('/api/pre-disbursements', methods=['GET'])
@jwt_required()
def get_pre_disbursements():
    try:
        current_user = get_jwt_identity()

        # Get all pre-disbursement data
        pre_disbursements = get_all_pre_disbursement_temp()

        # Get other required data
        occupation_list = get_all_occupations()
        experience_ranges_list = get_all_experience_ranges()
        loan_metrics = get_all_loan_metrics()

        # Get user role from session or database
        user_rights = str(get_current_user()['rights'])

        content = {
            'pre_disbursements': pre_disbursements,
            'occupation_list': occupation_list,
            'experience_ranges_list': experience_ranges_list,
            'loan_metrics': loan_metrics,
            'is_reviewer': user_rights == '1',
            'is_approver': user_rights == '2',
            'is_executive_approver': user_rights == '3',
            'is_admin': user_rights == '4',
            'user_have_sign': is_user_have_sign()
        }

        return jsonify({
            'success': True,
            'data': content
        }), 200

    except Exception as e:
        print('Get pre-disbursements exception:', str(e))
        return jsonify({
            'success': False,
            'message': 'Failed to fetch pre-disbursements'
        }), 500


@application.route('/api/loan-metrics-metadata', methods=['GET'])
@jwt_required()
def loan_metrics_metadata():
    try:

        occupation_list = get_all_occupations()
        experience_ranges_list = get_all_experience_ranges()
        loan_metrics = get_all_loan_metrics()


        return jsonify({
            'success': True,
            'occupation_list': occupation_list,
            'experience_ranges_list': experience_ranges_list,
            'loan_metrics': loan_metrics
        }), 200

    except Exception as e:
        print('Get loan_metrics_metadata exception:', str(e))
        return jsonify({
            'success': False,
            'message': 'Failed to fetch loan_metrics_metadata'
        }), 500



@application.route('/view-rejected-applications')
def view_rejected_applications():
    try:
        if is_login():
            content = {
                'get_temp_pre_disbursement': view_all_rejected_application(),
                'is_user_have_sign': is_user_have_sign(),
                'occupation_list': get_all_occupations(),
                'experience_ranges_list': get_all_experience_ranges(),
                'get_all_loan_metrics': get_all_loan_metrics(),
                'is_reviewer': is_reviewer(),
                'is_approver': is_approver(),
                'is_executive_approver': is_executive_approver(),
                'is_admin': is_admin()
            }
            return render_template('view_rejected_applications.html', result=content)
    except Exception as e:
        print('view-rejected-applications exception:- ', str(e.__dict__))
        print('view-rejected-applications exception:- ', str(e))

    return redirect(url_for('login'))



# @application.route('/update-pre-disbursement-temp', methods=['POST'])
# def update_pre_disbursement_temp():
#     """
#     Update pre-disbursement temporary record based on status using f-strings.
#     """
#     try:
#         # Check if user is authenticated
#         if not is_login():
#             print("Unauthorized access attempt")
#             return jsonify({'success': False, 'error': 'Unauthorized'}), 401
# 
#         # Get JSON data from request
#         data = request.get_json()
#         print(f"Received data: {data}")
# 
#         # Extract required fields
#         pre_disb_temp_id = data.get('pre_disb_temp_id')
#         status = str(data.get('status'))
#         notes = data.get('Notes')
#         amount_accepted = data.get('amount_accepted')
#         print(f"Extracted: id={pre_disb_temp_id}, status={status}, notes={notes}, amount={amount_accepted}")
# 
#         # Validate required fields
#         if not pre_disb_temp_id or not status:
#             print("Missing required fields")
#             return jsonify({'success': False, 'error': 'Missing required fields'}), 400
# 
#         # Get current user and timestamp
#         approved_by = str(get_current_user_id())
#         approved_date = str(datetime.now())
#         print(f"User: {approved_by}, Date: {approved_date}")
# 
#         # Define status-to-field mapping
#         status_fields = {
#             '2': ('approved_by', 'approved_date'),
#             '5': ('reviewed_by', 'reviewed_date'),
#             '6': ('reviewed_by', 'reviewed_date'),
#             '3': ('rejected_by', 'rejected_date')
#         }
# 
#         # Validate status
#         if status not in status_fields:
#             print(f"Invalid status: {status}")
#             return jsonify({'success': False, 'error': 'Invalid status'}), 400
# 
#         # Prepare update query with f-strings
#         update_field, date_field = status_fields[status]
#         query = f"""
#             UPDATE tbl_pre_disbursement_temp
#             SET status = '{status}', Notes = '{notes}', KFT_Approved_Loan_Limit = '{amount_accepted}',
#                 {update_field} = '{approved_by}', {date_field} = '{approved_date}'
#             WHERE pre_disb_temp_id = '{pre_disb_temp_id}'
#         """
# 
#         # Execute update query
#         execute_command(query)
#         print(f"Executed update query for pre_disb_temp_id: {pre_disb_temp_id}")
# 
#         # Handle rejected status (status = '3')
#         if status == '3':
#             insert_query = f"""
#                 INSERT INTO tbl_pre_disb_rejected_app (
#                     post_disb_id,
#                     application_status,
#                     status,
#                     created_by,
#                     created_date,
#                     modified_by,
#                     modified_date
#                 )
#                 SELECT
#                     '{pre_disb_temp_id}',
#                     '{status}',
#                     1,
#                     '{approved_by}',
#                     '{approved_date}',
#                     '{approved_by}',
#                     '{approved_date}'
#                 WHERE NOT EXISTS (
#                     SELECT 1 FROM tbl_pre_disb_rejected_app WHERE post_disb_id = '{pre_disb_temp_id}'
#                 )
#             """
#             execute_command(insert_query)
#             print(f"Inserted rejected app record for post_disb_id: {pre_disb_temp_id}")
# 
#         # Return success response
#         print("Update completed successfully")
#         return jsonify({'success': True, 'status': str(status)}), 200
# 
#     except Exception as e:
#         # Log error and return failure response
#         print(f"Error occurred: {str(e)}")
#         return jsonify({'success': False, 'error': str(e)}), 500
# 
# 
# @application.route('/approval-letter/<app_no>')
# @jwt_required()
# def approval_letter(app_no):
#     print('app_no:- ', app_no)
#     try:
#         # query = f"""
#         #     SELECT Borrower_Name, Application_No, Loan_Amount, ApplicationDate, Father_Husband_Name, CNIC, approved_date
#         #     FROM tbl_pre_disbursement_temp
#         #     WHERE pre_disb_temp_id = '{str(app_no)}' AND status = '2'
#         # """
# 
#         query = f"""
#             SELECT "Borrower_Name", "Application_No", "Loan_Amount", KFT_Approved_Loan_Limit, "ApplicationDate", "Father_Husband_Name", "CNIC", "approved_date", "email_status" 
#             FROM tbl_pre_disbursement_temp 
#             WHERE "pre_disb_temp_id" = '{str(app_no)}' AND "status" = '2'
#         """
#         record = fetch_records(query)
#         print(record)
# 
#         if not record:
#             abort(404, description="Approved record not found")
# 
# 
# 
#         # Convert logo image to base64
#         image_path = os.path.join(application.root_path, 'static', 'images', 'hbl_logo-removebg-preview.png')
#         with open(image_path, 'rb') as image_file:
#             base64_image = base64.b64encode(image_file.read()).decode('utf-8')
#         logo_base64 = f'data:image/png;base64,{base64_image}'
# 
#         # Convert User sign to base64
#         query = f"""
#             SELECT u.name, u.email, u.signature, u.scan_sign 
#             FROM tbl_users u 
#             WHERE u.active = '1' AND u.user_id = '{get_current_user_id()}'
#         """
#         user = fetch_records(query)
# 
#         # Convert scan_sign BLOB to base64 for display if it exists
#         sign_base64 = None
#         if user[0]['scan_sign']:
#             sign_base64 = base64.b64encode(user[0]['scan_sign']).decode('utf-8')
#             # print(sign_base64)
# 
# 
#         return render_template('approval_letter.html', result=record[0], logo_base64=logo_base64,
#                                sign_base64=sign_base64)
#     except Exception as e:
#         print('approval_letter exception:- ', str(e))
#         abort(500, description=str(e))
# 
# 
# @application.route('/get_application_images')
# def get_application_images():
#     application_no = request.args.get('application_no')
#     if not application_no:
#         return jsonify({'success': False, 'error': 'Missing application_no'}), 400
# 
#     # Using f-string as requested (but note: not ideal for security)
#     # In production, strongly prefer parameterized queries
#     images = fetch_records(f"""
#         SELECT 
#             pd_ai_id,
#             cnic,
#             customer_name,
#             created_date
#         FROM tbl_pre_disbursement_application_images
#         WHERE application_no = '{application_no}'
#         ORDER BY created_date DESC
#     """)
# 
#     result = []
#     for img in images or []:
#         result.append({
#             'url': url_for('serve_pre_image', image_id=img['pd_ai_id']),
#             'filename': f"{img['customer_name'] or 'Customer'}_{img['cnic'] or 'Unknown'}_{img['pd_ai_id']}.jpg",
#             'uploaded': img['created_date'].strftime('%Y-%m-%d %H:%M') if img.get('created_date') else None,
#             'cnic': img.get('cnic'),
#             'customer_name': img.get('customer_name')
#         })
# 
#     return jsonify({
#         'success': True,
#         'images': result
#     })
# 
# 
# @application.route('/pre_image/<int:image_id>')
# def serve_pre_image(image_id):
#     # Again using f-string as requested
#     rows = fetch_records(f"""
#         SELECT image_data
#         FROM tbl_pre_disbursement_application_images
#         WHERE pd_ai_id = {image_id}
#     """)
# 
#     if not rows or not rows[0].get('image_data'):
#         return "Image not found", 404
# 
#     image_data = rows[0]['image_data']
# 
#     # Handle possible memoryview (common when bytea is fetched)
#     if isinstance(image_data, memoryview):
#         image_data = image_data.tobytes()
# 
#     # Or if it's already bytes, use directly
#     if not isinstance(image_data, bytes):
#         return "Invalid image data format", 500
# 
#     return send_file(
#         io.BytesIO(image_data),
#         mimetype='image/jpeg',          # Adjust if you know the actual format
#         as_attachment=False,
#         download_name=f"pre_image_{image_id}.jpg"
#     )


# Update pre-disbursement temp
# Update pre-disbursement temporary record
@application.route('/api/update-pre-disbursement-temp', methods=['PUT'])
@jwt_required()
def update_pre_disbursement_temp():
    """
    Update pre-disbursement temporary record based on status using f-strings.
    """
    try:
        print("=== ENTERED update_pre_disbursement_temp ===")

        # Get current user from JWT
        current_user = get_jwt_identity()
        print(f"Current user from JWT: {current_user}")

        # Get JSON data from request
        data = request.get_json()
        print(f"Received JSON data: {data}")

        # Extract required fields
        pre_disb_temp_id = data.get('pre_disb_temp_id')
        status = str(data.get('status'))
        notes = data.get('notes')
        amount_accepted = data.get('amount_accepted')
        print(
            f"Extracted fields → id={pre_disb_temp_id}, status={status}, notes={notes}, amount_accepted={amount_accepted}")

        # Validate required fields
        if not pre_disb_temp_id or not status:
            print("Validation failed: Missing pre_disb_temp_id or status")
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        print("Required fields validation passed")

        # Get current user and timestamp
        approved_by = str(get_current_user_id())  # Adjust based on your user structure
        approved_date = str(datetime.now())
        print(f"Approver ID: {approved_by} | Timestamp: {approved_date}")

        # Define status-to-field mapping
        status_fields = {
            '2': ('approved_by', 'approved_date'),
            '5': ('reviewed_by', 'reviewed_date'),
            '6': ('reviewed_by', 'reviewed_date'),
            '3': ('rejected_by', 'rejected_date')
        }
        print(f"Status mapping dictionary: {status_fields}")

        # Validate status
        if status not in status_fields:
            print(f"Invalid status received: {status}")
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        print(f"Status {status} is valid")

        # Prepare update query with f-strings
        update_field, date_field = status_fields[status]
        print(f"Selected fields for update → update_field={update_field}, date_field={date_field}")

        query = f"""
            UPDATE tbl_pre_disbursement_temp
            SET status = '{status}', Notes = '{notes}', KFT_Approved_Loan_Limit = '{int(float(amount_accepted))}',
                {update_field} = '{approved_by}', {date_field} = '{approved_date}'
            WHERE pre_disb_temp_id = '{pre_disb_temp_id}'
        """
        print(f"Generated UPDATE query:\n{query}")

        # Execute update query
        execute_command(query)
        print(f"UPDATE query executed successfully for pre_disb_temp_id: {pre_disb_temp_id}")

        # Handle rejected status (status = '3')
        if status == '3':
            print("Status is '3' (rejected) → preparing insert into rejected table")
            insert_query = f"""
                INSERT INTO tbl_pre_disb_rejected_app (
                    post_disb_id,
                    application_status,
                    status,
                    created_by,
                    created_date,
                    modified_by,
                    modified_date
                )
                SELECT
                    '{pre_disb_temp_id}',
                    '{status}',
                    1,
                    '{approved_by}',
                    '{approved_date}',
                    '{approved_by}',
                    '{approved_date}'
                WHERE NOT EXISTS (
                    SELECT 1 FROM tbl_pre_disb_rejected_app WHERE post_disb_id = '{pre_disb_temp_id}'
                )
            """
            print(f"Generated INSERT query for rejected app:\n{insert_query}")

            execute_command(insert_query)
            print(f"Rejected record insert executed for post_disb_id: {pre_disb_temp_id}")
        else:
            print(f"Status is {status} → no rejected record insertion needed")

        # Return success response
        print("Update operation completed successfully")
        return jsonify({'success': True, 'status': str(status)}), 200

    except Exception as e:
        print(f"!!! EXCEPTION in update_pre_disbursement_temp: {str(e)}")
        import traceback
        traceback.print_exc()  # optional: shows full stack trace in console
        return jsonify({'success': False, 'error': str(e)}), 500


# Get approval letter
@application.route('/api/approval-letter/<app_no>', methods=['POST', 'GET'])
@jwt_required()
def approval_letter(app_no):
    print(f"=== ENTERED approval_letter with app_no: {app_no} ===")
    try:
        query = f"""
            SELECT "Borrower_Name", "Application_No", "Loan_Amount", KFT_Approved_Loan_Limit, "ApplicationDate", "Father_Husband_Name", "CNIC", "approved_date", "email_status" 
            FROM tbl_pre_disbursement_temp 
            WHERE "pre_disb_temp_id" = '{str(app_no)}' AND "status" = '2'
        """
        print(f"Fetching approval letter with query:\n{query}")

        record = fetch_records(query)
        print(f"Database result: {record}")

        if not record:
            print("No approved record found for this app_no")
            return jsonify({'success': False, 'error': 'Approved record not found'}), 404
        print("Approved record found")

        # Convert logo image to base64
        image_path = os.path.join(application.root_path, 'static', 'images', 'hbl_logo-removebg-preview.png')
        print(f"Loading logo from path: {image_path}")

        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        logo_base64 = f'data:image/png;base64,{base64_image}'
        print(f"Logo base64 generated (length: {len(logo_base64)})")

        # Get user signature
        user_query = f"""
            SELECT u.name, u.email, u.signature, u.scan_sign 
            FROM tbl_users u 
            WHERE u.active = '1' AND u.user_id = '{get_current_user_id()}'
        """
        print(f"Fetching user signature with query:\n{user_query}")

        user = fetch_records(user_query)
        print(f"User record: {user}")

        sign_base64 = None
        if user and user[0].get('scan_sign'):
            sign_base64 = base64.b64encode(user[0]['scan_sign']).decode('utf-8')
            print(f"Signature base64 generated (length: {len(sign_base64)})")
        else:
            print("No signature found for current user")

        print('is_user_have_sign:- ', is_user_have_sign)

        # Prepare response
        letter_data = {
            'borrower_name': record[0].get('Borrower_Name'),
            'application_no': record[0].get('Application_No'),
            'loan_amount': record[0].get('Loan_Amount'),
            'kft_approved_limit': record[0].get('KFT_Approved_Loan_Limit'),
            'application_date': record[0].get('ApplicationDate'),
            'father_husband_name': record[0].get('Father_Husband_Name'),
            'cnic': record[0].get('CNIC'),
            'approved_date': record[0].get('approved_date'),
            'logo_url': '/static/images/hbl_logo-removebg-preview.png',  # Flask serves static automatically
            'signature_url': f'/api/signature/current' if is_user_have_sign() else None,
        }
        print(f"Returning letter data: {letter_data}")

        return jsonify({
            'success': True,
            'letter': letter_data
        }), 200

    except Exception as e:
        print(f"!!! EXCEPTION in approval_letter: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/api/signature/current', methods=['GET'])
@jwt_required()
def get_current_user_signature():
    try:
        user_query = f"""
            SELECT scan_sign 
            FROM tbl_users 
            WHERE active = '1' AND user_id = '{get_current_user_id()}'
        """
        user = fetch_records(user_query)

        if not user or not user[0].get('scan_sign'):
            return jsonify({'success': False, 'error': 'No signature found'}), 404

        signature_bytes = user[0]['scan_sign']  # assuming this is bytes already

        return Response(
            signature_bytes,
            mimetype='image/png',  # change to 'image/jpeg' etc. if different format
            headers={
                'Content-Disposition': 'inline',
                'Cache-Control': 'no-cache'  # optional
            }
        )

    except Exception as e:
        print(f"Error serving signature: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Get application images list
@application.route('/api/get_application_images', methods=['POST', 'GET'])
@jwt_required()
def get_application_images():
    print("=== ENTERED get_application_images ===")
    try:
        application_no = request.args.get('application_no')
        print(f"Requested application_no: {application_no}")

        if not application_no:
            print("Missing application_no parameter")
            return jsonify({'success': False, 'error': 'Missing application_no'}), 400
        print("application_no received")

        query = f"""
            SELECT 
                pd_ai_id,
                cnic,
                customer_name,
                created_date
            FROM tbl_pre_disbursement_application_images
            WHERE application_no = '{application_no}'
            ORDER BY created_date DESC
        """
        print(f"Fetching images with query:\n{query}")

        images = fetch_records(query)
        print(f"Found {len(images or [])} image records")

        result = []
        base_url = request.host_url.rstrip('/')
        print(f"Base URL for image links: {base_url}")

        for img in images or []:
            img_url = f"{base_url}/api/pre_image/{img['pd_ai_id']}"
            filename = f"{img['customer_name'] or 'Customer'}_{img['cnic'] or 'Unknown'}_{img['pd_ai_id']}.jpg"

            result.append({
                'url': img_url,
                'filename': filename,
                'uploaded': img['created_date'].strftime('%Y-%m-%d %H:%M') if img.get('created_date') else None,
                'cnic': img.get('cnic'),
                'customer_name': img.get('customer_name')
            })
            print(f"Added image: {filename} → {img_url}")

        print(f"Returning {len(result)} images")
        return jsonify({
            'success': True,
            'images': result
        }), 200

    except Exception as e:
        print(f"!!! EXCEPTION in get_application_images: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# Serve individual pre-uploaded image
@application.route('/api/pre_image/<int:image_id>', methods=['POST', 'GET'])
@jwt_required()
def serve_pre_image(image_id):
    print(f"=== ENTERED serve_pre_image for image_id: {image_id} ===")
    try:
        query = f"""
            SELECT image_data
            FROM tbl_pre_disbursement_application_images
            WHERE pd_ai_id = {image_id}
        """
        print(f"Fetching image data with query:\n{query}")

        rows = fetch_records(query)
        print(f"Query returned {len(rows or [])} rows")

        if not rows or not rows[0].get('image_data'):
            print("Image not found or image_data is empty")
            return jsonify({'success': False, 'error': 'Image not found'}), 404

        image_data = rows[0]['image_data']
        print(
            f"Image data type: {type(image_data)}, length: {len(image_data) if isinstance(image_data, (bytes, memoryview)) else 'N/A'}")

        # Handle possible memoryview (common with bytea / psycopg2)
        if isinstance(image_data, memoryview):
            image_data = image_data.tobytes()
            print("Converted memoryview → bytes")

        if not isinstance(image_data, bytes):
            print("Image data is not in bytes format")
            return jsonify({'success': False, 'error': 'Invalid image data format'}), 500

        # ────────────────────────────────────────────────
        #           Replaced imghdr with filetype
        # ────────────────────────────────────────────────
        import filetype
        kind = filetype.guess(image_data)

        if kind is None:
            print("Could not detect image type")
            return jsonify({'success': False, 'error': 'Unsupported image format'}), 415

        mime_type = kind.mime          # e.g. "image/jpeg", "image/png"
        extension = kind.extension     # e.g. "jpg", "png", "webp"

        print(f"Detected image type: {extension} ({mime_type})")

        # Use the real extension instead of hardcoding .jpg
        # This prevents broken images when someone downloads a PNG but filename says .jpg
        download_name = f"pre_image_{image_id}.{extension}"

        print("Sending image file response")
        return send_file(
            io.BytesIO(image_data),
            mimetype=mime_type,
            as_attachment=False,
            download_name=download_name
        )

    except Exception as e:
        print(f"!!! EXCEPTION in serve_pre_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500