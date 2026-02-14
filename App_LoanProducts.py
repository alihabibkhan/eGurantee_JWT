from imports import *
from application import application


@application.route('/api/loan-products', methods=['GET'])
@jwt_required()
def api_get_all_loan_products():
    """API endpoint to get all loan products"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        products = get_all_loan_products()
        return jsonify({
            'success': True,
            'data': products
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-products/<int:product_id>', methods=['GET'])
@jwt_required()
def api_get_loan_product(product_id):
    """API endpoint to get a single loan product by ID"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        query = f"""
            SELECT product_id, product_code, name, gender, description, status, 
                   created_by, created_date, modified_by, modified_date
            FROM tbl_loan_products 
            WHERE product_id = '{product_id}' AND status = '1'
        """
        product = fetch_records(query)
        product = product[0] if product else None

        if product:
            return jsonify({
                'success': True,
                'data': {'loan_product': product}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Loan product not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-products', methods=['POST'])
@application.route('/api/loan-products/<int:product_id>', methods=['POST'])
@jwt_required()
def api_save_loan_product(product_id=None):
    """API endpoint to create or update a loan product"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()

        name = data.get('name')
        product_code = data.get('product_code')
        gender = data.get('gender', 'Male')
        description = data.get('description', '')

        current_user_id = str(get_current_user_id())
        current_timestamp = str(datetime.now())

        if product_id:  # UPDATE
            update_query = f"""
                UPDATE tbl_loan_products 
                SET name = '{name}', 
                    product_code = '{product_code}', 
                    gender = '{gender}', 
                    description = '{description}', 
                    status = '1', 
                    modified_by = '{current_user_id}', 
                    modified_date = '{current_timestamp}'
                WHERE product_id = '{product_id}'
            """
            execute_command(update_query)
            message = 'Loan product updated successfully'
        else:  # INSERT
            insert_query = f"""
                INSERT INTO tbl_loan_products (
                    name, product_code, gender, description, status, 
                    created_by, created_date, modified_by, modified_date
                ) VALUES (
                    '{name}', '{product_code}', '{gender}', '{description}', '1', 
                    '{current_user_id}', '{current_timestamp}', 
                    '{current_user_id}', '{current_timestamp}'
                )
            """
            execute_command(insert_query)
            message = 'Loan product added successfully'

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print('api_save_loan_product exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@application.route('/api/loan-products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def api_delete_loan_product(product_id):
    """API endpoint to delete a loan product (soft delete)"""
    try:
        if not is_login() or not (is_admin() or is_executive_approver()):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        delete_query = f"""
            UPDATE tbl_loan_products 
            SET status = '0'
            WHERE product_id = '{product_id}'
        """
        execute_command(delete_query)

        return jsonify({
            'success': True,
            'message': 'Loan product deleted successfully'
        }), 200

    except Exception as e:
        print('api_delete_loan_product exception:- ', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500