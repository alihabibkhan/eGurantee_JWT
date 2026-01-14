from imports import *


# ────────────────────────────────────────────────────────────────
#   JWT-based helpers (replace old session versions)
# ────────────────────────────────────────────────────────────────

def get_current_user_id():
    """Returns the authenticated user_id from JWT or None"""
    identity = get_jwt_identity()
    if identity is not None:
        return str(identity)  # usually stored as string or int
    return None


def get_current_user():
    """Fetch full current user data from DB using JWT identity"""
    user_id = get_current_user_id()
    if not user_id or user_id == '-1':
        return None

    query = f"""
        SELECT user_id, name, email, rights, volunteer_id, gender, dob, phone,
               country_of_residence, date_of_joining, orientation_completed_on,
               manager_id, assigned_branch, signature
        FROM tbl_users
        WHERE user_id = '{str(user_id)}'
    """
    result = fetch_records(query)
    if result:
        return result[0]
    return None


def is_login():
    """Check if request has valid JWT"""
    try:
        verify_jwt_in_request(optional=True)

        identity = get_jwt_identity()

        return identity is not None
    except Exception as e:
        print('is login exception:- ', str(e))
        return False


def get_current_user_role():
    user = get_current_user()
    if user:
        return str(user.get('rights', '-1'))
    return '-1'


def is_admin():
    return get_current_user_role() == '4'


def is_reviewer():
    return get_current_user_role() == '1'


def is_approver():
    return get_current_user_role() == '2'


def is_executive_approver():
    return get_current_user_role() == '3'


def is_user_have_sign():
    user_data = get_current_user()
    print('user_data')
    print(user_data)

    if user_data:
        have_signature = True if str(user_data.get('signature')) == '1' else False
        print('have_signature:- ', have_signature)

        if have_signature:
            return True

    return False
