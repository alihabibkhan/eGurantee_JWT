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



@application.route('/api/rejected-applications/filters', methods=['GET'])
@jwt_required()
def api_get_rejected_applications_filters():
    try:
        current_user = get_jwt_identity()

        return jsonify({
            'success': True,
            'data': {
                'occupations': get_all_occupations(),
                'experience_ranges': get_all_experience_ranges(),
                'loan_metrics': get_all_loan_metrics(),
                'user_roles': {
                    'is_reviewer': is_reviewer(),
                    'is_approver': is_approver(),
                    'is_executive_approver': is_executive_approver(),
                    'is_admin': is_admin()
                }
            }
        }), 200

    except Exception as e:
        print('API get rejected applications filters exception:', str(e))
        return jsonify({'success': False, 'error': 'Server error'}), 500


@application.route('/api/rejected-applications/list', methods=['GET'])
@jwt_required()
def api_get_rejected_applications():
    try:
        current_user = get_jwt_identity()

        # Get query parameters for filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'rejected_date')
        sort_order = request.args.get('sort_order', 'desc')

        # Call your existing function
        applications = view_all_rejected_application()

        # Apply filters
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            applications = [app for app in applications
                            if app.get('rejected_date') and
                            datetime.strptime(app['rejected_date'].split()[0], '%Y-%m-%d') >= start_date_obj]

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            applications = [app for app in applications
                            if app.get('rejected_date') and
                            datetime.strptime(app['rejected_date'].split()[0], '%Y-%m-%d') <= end_date_obj]

        # Apply sorting
        if sort_by == 'ApplicationDate':
            applications.sort(key=lambda x: x.get('ApplicationDate') or '',
                              reverse=(sort_order == 'desc'))
        elif sort_by == 'Loan_Amount':
            applications.sort(key=lambda x: float(x.get('Loan_Amount') or 0),
                              reverse=(sort_order == 'desc'))
        elif sort_by == 'rejected_by':
            applications.sort(key=lambda x: x.get('rejected_by') or '',
                              reverse=(sort_order == 'desc'))
        elif sort_by == 'notes':
            applications.sort(key=lambda x: x.get('notes') or '',
                              reverse=(sort_order == 'desc'))
        else:  # Default sort by rejected_date
            applications.sort(key=lambda x: x.get('rejected_date') or '',
                              reverse=(sort_order == 'desc'))

        return jsonify({
            'success': True,
            'applications': applications,
            'total_count': len(applications)
        }), 200

    except Exception as e:
        print('API get rejected applications exception:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/api/rejected-applications/<int:application_id>', methods=['GET'])
@jwt_required()
def api_get_rejected_application_detail(application_id):
    try:
        current_user = get_jwt_identity()

        # Get application details
        applications = view_all_rejected_application()
        application = next((app for app in applications if app.get('pre_disb_temp_id') == application_id), None)

        if not application:
            return jsonify({'success': False, 'error': 'Application not found'}), 404

        # Get loan history if CNIC exists
        loan_history = []
        if application.get('CNIC'):
            # Query to fetch on-going loan details
            query = f"""
                        SELECT loan_no, cnic, loan_closed_on, mis_date, disbursed_amount, product_code,
                        booked_on, markup_outstanding, principal_outstanding, loan_closed_on, overdue_days,
                        loan_status, purpose
                        FROM tbl_post_disbursement
                        WHERE CNIC = '{application.get('CNIC')}' ORDER BY mis_date DESC LIMIT 3
                    """
            result = fetch_records(query)
            print(result)

            loan_history = result

        return jsonify({
            'success': True,
            'application': application,
            'loan_history': loan_history
        }), 200

    except Exception as e:
        print('API get application detail exception:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/api/rejected-applications/export', methods=['GET'])
@jwt_required()
def api_export_rejected_applications():
    try:
        current_user = get_jwt_identity()

        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get filtered applications
        applications = view_all_rejected_application()

        # Apply date filters
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            applications = [app for app in applications
                            if app.get('rejected_date') and
                            datetime.strptime(app['rejected_date'].split()[0], '%Y-%m-%d') >= start_date_obj]

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            applications = [app for app in applications
                            if app.get('rejected_date') and
                            datetime.strptime(app['rejected_date'].split()[0], '%Y-%m-%d') <= end_date_obj]

        # Prepare data for export
        export_data = []
        for app in applications:
            export_data.append({
                'application_no': app.get('Application_No', ''),
                'branch': app.get('Branch_Name', ''),
                'loan_product': app.get('LoanProductCode', ''),
                'borrower_name': app.get('Borrower_Name', ''),
                'loan_amount': app.get('Loan_Amount', ''),
                'reason': app.get('notes', ''),
                'rejected_by': app.get('rejected_by', ''),
                'rejected_date': app.get('rejected_date', ''),
            })

        return jsonify({
            'success': True,
            'data': export_data,
            'total_records': len(export_data)
        }), 200

    except Exception as e:
        print('API export rejected applications exception:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500



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

            from Model_Email import send_email
            
            query = f"""
                select pdt."Application_No", pdt."Borrower_Name", pdt."Requested_Loan_Amount", pdt."LoanProductCode", u1.email as reviewed_by_email, u2.email as rejected_by_email,
                b.email, b.branch, b.branch_name
                from tbl_pre_disbursement_temp pdt
                INNER JOIN tbl_branches b ON pdt."Branch_Name" LIKE CONCAT('%', b.branch_code, '%') AND b.live_branch = '1'
                LEFT JOIN tbl_users u1 ON u1.user_id = pdt.reviewed_by
                LEFT JOIN tbl_users u2 ON u2.user_id = pdt.rejected_by
                where pdt.pre_disb_temp_id = '{str(pre_disb_temp_id)}' and pdt.status = '3'
            """
            result = fetch_records(query)

            if len(result) > 0:
                result = result[0]
                reference_no = result.get('Application_No', None)
                Borrower_Name = result.get('Borrower_Name', None)
                Requested_Loan_Amount = result.get('Requested_Loan_Amount', None)
                LoanProductCode = result.get('LoanProductCode', None)
                reviewed_by_email = result.get('reviewed_by_email', None)
                rejected_by_email = result.get('rejected_by_email', None)
                branch_email = result.get('email', None)
                branch = result.get('branch', None)
                branch_name = result.get('branch_name', None)

                # ==================== HTML EMAIL TEMPLATE ====================
                html_body = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Query Raised - Loan Application</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
                            .header {{ background-color: #d32f2f; color: white; padding: 15px; text-align: center; }}
                            .content {{ padding: 20px; border: 1px solid #ddd; }}
                            .footer {{ text-align: center; font-size: 12px; color: #777; margin-top: 20px; }}
                            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
                            th {{ background-color: #f5f5f5; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2>Query Raised – Loan Application Review</h2>
                            </div>

                            <div class="content">
                                <p>Dear Manager <strong>{branch_name} BRANCH</strong>,</p>

                                <p>This is with reference to the subject case forwarded for our review. During the assessment, a few clarifications are required from the branch before we may proceed further with the approval process.</p>

                                <table>
                                    <tr>
                                        <th>Application Reference No</th>
                                        <td>{reference_no}</td>
                                    </tr>
                                    <tr>
                                        <th>Applicant Name</th>
                                        <td>{Borrower_Name}</td>
                                    </tr>
                                    <tr>
                                        <th>Requested Amount</th>
                                        <td>PKR {Requested_Loan_Amount}/-</td>
                                    </tr>
                                    <tr>
                                        <th>Product</th>
                                        <td>{LoanProductCode}</td>
                                    </tr>
                                </table>

                                <h3>Queries / Clarifications Required:</h3>
                                <p style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800;">
                                    {notes if notes else 'No specific notes provided.'}
                                </p>

                                <p>We request you to share the above information and supporting documents at the earliest so that we may proceed with the final evaluation of the case.</p>

                                <p>Thank you for your cooperation and continued support.</p>
                            </div>

                            <div class="footer">
                                <p>Kind regards,<br>
                                <strong>Khushali Foundation</strong><br>
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                """

                # ==================== SEND EMAIL ====================
                subject = f"Query Raised – Loan Application Review (Ref: {reference_no}, borrower name: {Borrower_Name})"

                # Prepare recipient list
                email_list = [branch_email] if branch_email else []

                # Prepare CC list
                cc_list = []
                if reviewed_by_email:
                    cc_list.append(reviewed_by_email)
                if rejected_by_email and rejected_by_email != reviewed_by_email:
                    cc_list.append(rejected_by_email)

                # Send email using your existing method
                email_sent = send_email(
                    subject=subject,
                    email_list=email_list,
                    message="",  # Plain text version (optional)
                    html_message=html_body,  # HTML version
                    add_cc_list=True,
                    cc_list=cc_list
                )

                if email_sent:
                    print(f"Rejection query email sent successfully to {branch_email}")
                else:
                    print("Failed to send rejection query email")
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
            'email_status': str(record[0].get('email_status')),
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

