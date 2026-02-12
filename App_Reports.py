from imports import *
from application import application


@application.route('/api/fund-projection/filters', methods=['GET'])
@jwt_required()
def api_get_fund_projection_filters():
    print("→ ENTER api_get_fund_projection_filters")
    try:
        current_user = get_jwt_identity()
        print(f"  current_user from JWT: {current_user}")

        if not (is_admin() or is_executive_approver()):
            print("  → Unauthorized - not admin or executive approver")
            return jsonify({'error': 'Unauthorized access'}), 403

        print("  → User authorized → fetching data")

        banks = get_all_bank_details()
        print(f"  get_all_bank_details() returned {len(banks) if isinstance(banks, (list, tuple)) else 'non-list'} items")
        print('banks records:- ')
        print(banks)

        last_entries = get_all_banks_last_entry_records()
        print(f"  get_all_banks_last_entry_records() returned {len(last_entries) if isinstance(last_entries, (list, tuple)) else 'non-list'} items")
        print('banks last entries:- ')
        print(last_entries)

        outstanding_loans = get_outstanding_loans()
        print(f"  get_outstanding_loans() returned {len(outstanding_loans) if isinstance(outstanding_loans, (list, tuple)) else 'non-list'} items")

        post_disb = post_disbursement_by_booked_on()
        print(f"  post_disbursement_by_booked_on() returned {len(post_disb) if isinstance(post_disb, (list, tuple)) else 'non-list'} items")

        print("  → Preparing response payload")
        response_data = {
            'success': True,
            'data': {
                'banks': banks,
                'last_entry_records': last_entries,
                'outstanding_loans': outstanding_loans,
                'post_disbursement_by_booked_on': post_disb
            }
        }
        print("  → Returning 200 OK")
        return jsonify(response_data), 200

    except Exception as e:
        print('!!! EXCEPTION in api_get_fund_projection_filters:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server error'}), 500


@application.route('/api/fund-projection/save', methods=['POST'])
@jwt_required()
def api_save_fund_projection():
    print("→ ENTER api_save_fund_projection")
    try:
        current_user = get_jwt_identity()
        print(f"  current_user: {current_user}")

        if not (is_admin() or is_executive_approver()):
            print("  → Unauthorized access attempt")
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()
        print(f"  request.get_json() keys: {list(data.keys()) if data else 'None or empty body'}")

        bank_id = data.get('bank_id')
        print(f"  bank_id extracted: {bank_id}")
        if not bank_id:
            print("  → Missing bank_id → returning 400")
            return jsonify({'success': False, 'error': 'Bank ID is required'}), 400

        def parse_number(value, default='NULL'):
            orig = value
            if value is None or value == '':
                print(f"    parse_number({orig!r}) → empty/None → {default}")
                return default
            try:
                cleaned = str(value).replace(',', '').strip()
                print(f"    parse_number({orig!r}) → cleaned → {cleaned!r}")
                if cleaned == '':
                    return default
                # You can add float(cleaned) here if you want early validation
                return cleaned
            except Exception as ex:
                print(f"    parse_number failed on {orig!r}: {ex} → returning {default}")
                return default

        # ────────────────────────────────────────
        # Parse all fields with debug output
        # ────────────────────────────────────────
        account_balance              = parse_number(data.get('account_balance'))
        actual_data_date             = data.get('actual_data_date', 'NULL') or 'NULL'
        report_date                  = data.get('report_date', 'NULL') or 'NULL'
        actual_portfolio             = parse_number(data.get('actual_portfolio'))
        ten_percent_lien             = parse_number(data.get('ten_percent_lien'))
        total_lien_amount            = parse_number(data.get('total_lien_amount'))
        actual_collateral_balance    = parse_number(data.get('actual_collateral_balance'))
        surplus_shortfall            = parse_number(data.get('surplus_shortfall'))
        projected_disbursement       = parse_number(data.get('projected_disbursement'))
        seasonal_affects             = parse_number(data.get('seasonal_affects'))
        new_product_affects          = parse_number(data.get('new_product_affects'))
        total_projected_disbursement = parse_number(data.get('total_projected_disbursement'))
        projected_recoveries         = parse_number(data.get('projected_recoveries'))
        projected_monthly_change     = parse_number(data.get('projected_monthly_change'))
        actual_portfolio_opening     = parse_number(data.get('actual_portfolio_opening'))
        add_projected_monthly_change = parse_number(data.get('add_projected_monthly_change'))
        projected_portfolio_closing  = parse_number(data.get('projected_portfolio_closing'))
        cushion_ten_percent          = parse_number(data.get('cushion_ten_percent'))
        projected_collateral_balance = parse_number(data.get('projected_collateral_balance'))
        actual_collateral_balance_req = parse_number(data.get('actual_collateral_balance_req'))
        surplus_shortfall_req        = parse_number(data.get('surplus_shortfall_req'))

        print("  All fields parsed successfully")

        created_by = get_current_user_id()
        print(f"  created_by = {created_by}")

        # ────────────────────────────────────────
        # SQL Query (was missing in previous snippet)
        # ────────────────────────────────────────
        query = """
        INSERT INTO tbl_fund_projection_reports (
            bank_id, account_balance, actual_data_date, report_date,
            actual_portfolio, ten_percent_lien, total_lien_amount, actual_collateral_balance,
            surplus_shortfall, projected_disbursement, seasonal_affects, new_product_affects,
            total_projected_disbursement, projected_recoveries, projected_monthly_change,
            actual_portfolio_opening, add_projected_monthly_change, projected_portfolio_closing,
            cushion_ten_percent, projected_collateral_balance,
            actual_collateral_balance_req, surplus_shortfall_req,
            created_by, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, NOW()
        )
        """

        params = (
            bank_id, account_balance, actual_data_date, report_date, actual_portfolio,
            ten_percent_lien, total_lien_amount, actual_collateral_balance, surplus_shortfall,
            projected_disbursement, seasonal_affects, new_product_affects,
            total_projected_disbursement, projected_recoveries, projected_monthly_change,
            actual_portfolio_opening, add_projected_monthly_change, projected_portfolio_closing,
            cushion_ten_percent, projected_collateral_balance,
            actual_collateral_balance_req, surplus_shortfall_req,
            created_by
        )

        print(f"  → About to execute INSERT with {len(params)} parameters")
        # Optional: print("  SQL params:", params)   # ← uncomment only if values are small/safe

        execute_command(query, params)
        print("  → INSERT executed → success")

        return jsonify({
            'success': True,
            'message': 'Fund projection report saved successfully'
        }), 201

    except Exception as e:
        print('!!! EXCEPTION in api_save_fund_projection:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/api/fund-projection/report-dates', methods=['GET'])
@jwt_required()
def api_get_fund_projection_report_dates():
    print("→ ENTER api_get_fund_projection_report_dates")
    try:
        bank_id = request.args.get('bank_id')
        print(f"  Query param bank_id = {bank_id}")

        if not bank_id:
            print("  → Missing bank_id → 400")
            return jsonify({'success': False, 'error': 'Bank ID is required'}), 400

        query = """
            SELECT DISTINCT DATE(created_at) as report_date
            FROM tbl_fund_projection_reports
            WHERE bank_id = %s
            ORDER BY report_date DESC
        """

        result = fetch_records(query, (bank_id,))
        print(f"  fetch_records returned {len(result)} rows")

        dates = [row['report_date'].strftime('%Y-%m-%d') for row in result] if result else []
        print(f"  Returning {len(dates)} report dates")

        return jsonify({'success': True, 'dates': dates}), 200

    except Exception as e:
        print('!!! EXCEPTION in api_get_fund_projection_report_dates:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/api/fund-projection/report-data', methods=['GET'])
@jwt_required()
def api_get_fund_projection_report_data():
    print("→ ENTER api_get_fund_projection_report_data")
    try:
        bank_id     = request.args.get('bank_id')
        report_date = request.args.get('report_date')
        print(f"  bank_id = {bank_id}, report_date = {report_date}")

        if not bank_id or not report_date:
            print("  → Missing required parameter(s) → 400")
            return jsonify({'success': False, 'error': 'Bank ID and report date are required'}), 400

        query = """
            SELECT *
            FROM tbl_fund_projection_reports
            WHERE bank_id = %s
              AND DATE(created_at) = %s
            ORDER BY created_at DESC
            LIMIT 1
        """

        result = fetch_records(query, (bank_id, report_date))
        print(f"  fetch_records returned {len(result)} row(s)")

        if not result:
            print("  → No record found for this bank/date → 404")
            return jsonify({'success': False, 'error': 'No report found for the selected date'}), 404

        record = result[0]
        print("  → Processing most recent record")

        def format_value(value, is_date=False):
            if value is None:
                return '0' if not is_date else ''
            if is_date:
                return value.strftime('%Y-%m-%d')
            return str(value)

        report = {
            'bank_id':                        format_value(record.get('bank_id')),
            'account_balance':                format_value(record.get('account_balance')),
            'actual_data_date':               format_value(record.get('actual_data_date'), True),
            'report_date':                    format_value(record.get('report_date'), True),
            'actual_portfolio':               format_value(record.get('actual_portfolio')),
            'ten_percent_lien':               format_value(record.get('ten_percent_lien')),
            'total_lien_amount':              format_value(record.get('total_lien_amount')),
            'actual_collateral_balance':      format_value(record.get('actual_collateral_balance')),
            'surplus_shortfall':              format_value(record.get('surplus_shortfall')),
            'projected_disbursement':         format_value(record.get('projected_disbursement')),
            'seasonal_affects':               format_value(record.get('seasonal_affects')),
            'new_product_affects':            format_value(record.get('new_product_affects')),
            'total_projected_disbursement':   format_value(record.get('total_projected_disbursement')),
            'projected_recoveries':           format_value(record.get('projected_recoveries')),
            'projected_monthly_change':       format_value(record.get('projected_monthly_change')),
            'actual_portfolio_opening':       format_value(record.get('actual_portfolio_opening')),
            'add_projected_monthly_change':   format_value(record.get('add_projected_monthly_change')),
            'projected_portfolio_closing':    format_value(record.get('projected_portfolio_closing')),
            'cushion_ten_percent':            format_value(record.get('cushion_ten_percent')),
            'projected_collateral_balance':   format_value(record.get('projected_collateral_balance')),
            'actual_collateral_balance_req':  format_value(record.get('actual_collateral_balance_req')),
            'surplus_shortfall_req':          format_value(record.get('surplus_shortfall_req')),
            'created_at':                     format_value(record.get('created_at'), True),
        }

        print("  → Report dictionary prepared → returning 200")
        return jsonify({'success': True, 'report': report}), 200

    except Exception as e:
        print('!!! EXCEPTION in api_get_fund_projection_report_data:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@application.route('/fund_projected_vs_disbursement')
def fund_projected_vs_disbursement():
    try:
        if is_login() and (is_admin() or is_executive_approver()):

            # query = """
            #     WITH LatestMonth AS (
            #         SELECT
            #             report_date,
            #             total_projected_disbursement,
            #             projected_recoveries,
            #             ROW_NUMBER() OVER (PARTITION BY TO_CHAR(report_date, 'Mon-YYYY')
            #                               ORDER BY created_at DESC) AS rn
            #         FROM tbl_fund_projection_reports
            #         WHERE TO_CHAR(report_date, 'YYYY-MM') = (
            #             SELECT TO_CHAR(MAX(report_date), 'YYYY-MM')
            #             FROM tbl_fund_projection_reports
            #         )
            #     ),
            #     Disbursement AS (
            #         SELECT
            #             SUM(disbursed_amount) AS disbursement
            #         FROM tbl_post_disbursement
            #         WHERE DATE_TRUNC('month', mis_date) = (
            #             SELECT DATE_TRUNC('month', MAX(mis_date))
            #             FROM tbl_post_disbursement
            #         )
            #     )
            #     SELECT
            #         TO_CHAR(lm.report_date, 'Mon-YYYY') AS month_year,
            #         lm.total_projected_disbursement,
            #         lm.projected_recoveries,
            #         d.disbursement
            #     FROM LatestMonth lm
            #     CROSS JOIN Disbursement d
            #     WHERE lm.rn = 1;
            # """


            # query = """
            #     WITH LatestMonth AS (
            #         SELECT
            #             report_date,
            #             total_projected_disbursement,
            #             projected_recoveries,
            #             ROW_NUMBER() OVER (PARTITION BY TO_CHAR(report_date, 'YYYY-MM')
            #                               ORDER BY created_at DESC) AS rn
            #         FROM tbl_fund_projection_reports
            #     ),
            #     Disbursement AS (
            #         SELECT
            #             SUM(disbursed_amount) AS disbursement
            #         FROM tbl_post_disbursement
            #         WHERE DATE_TRUNC('month', mis_date) = (
            #             SELECT DATE_TRUNC('month', MAX(mis_date))
            #             FROM tbl_post_disbursement
            #         )
            #     )
            #     SELECT
            #         TO_CHAR(lm.report_date, 'Mon-YYYY') AS month_year,
            #         lm.total_projected_disbursement,
            #         lm.projected_recoveries,
            #         d.disbursement
            #     FROM LatestMonth lm
            #     CROSS JOIN Disbursement d
            #     WHERE lm.rn = 1
            #     ORDER BY lm.report_date;
            # """

            query = """
                WITH LatestMonth AS (
                    SELECT 
                        report_date,
                        total_projected_disbursement,
                        projected_recoveries,
                        ROW_NUMBER() OVER (PARTITION BY TO_CHAR(report_date, 'YYYY-MM') 
                                          ORDER BY created_at DESC) AS rn
                    FROM tbl_fund_projection_reports
                ),
                Disbursement AS (
                    SELECT 
                        SUM(disbursed_amount) AS disbursement,
                        DATE_TRUNC('month', booked_on) AS booked_month
                    FROM tbl_post_disbursement
                    GROUP BY DATE_TRUNC('month', booked_on)
                )
                SELECT 
                    TO_CHAR(lm.report_date, 'Mon-YYYY') AS month_year,
                    lm.total_projected_disbursement,
                    lm.projected_recoveries,
                    d.disbursement
                FROM LatestMonth lm
                LEFT JOIN Disbursement d
                    ON DATE_TRUNC('month', lm.report_date) = d.booked_month
                WHERE lm.rn = 1
                ORDER BY lm.report_date;
            """

            result = fetch_records(query)

            content = {
                'fund_projection_data': result,
            }
            return render_template('fund_projected_vs_disbursement.html', result=content)
    except Exception as e:
        print('fund projected vs disbursement exception:- ', str(e))
    return redirect(url_for('login'))


# --------------------------------------------------------------
# 1. Render the page (same as before)
# --------------------------------------------------------------
@application.route('/loan_projection_report')
def loan_projection_report():
    try:
        if not (is_login() and (is_admin() or is_executive_approver())):
            return redirect(url_for('login'))

        # Product list
        prod_sql = "SELECT DISTINCT product_code FROM tbl_post_disbursement ORDER BY product_code"
        product_list = fetch_records(prod_sql)

        return render_template(
            'loan_projection_report.html',
            result={'product_list': product_list}
        )
    except Exception as e:
        print('loan_projection_report error:', e)
        return redirect(url_for('login'))


@application.route('/get_loan_projection_report_data', methods=['POST'])
def get_loan_projection_report_data():
    try:
        filters = request.get_json() or {}

        # ------------------------------------------------------------------
        # Base CTE – PostgreSQL (with fixes)
        # ------------------------------------------------------------------
        query = """
            WITH monthly_data AS (
                SELECT
                    TO_CHAR(booked_on, 'Mon-YYYY') AS "Month",
                    SUM(disbursed_amount) AS "Actual Disbursement",
                    COUNT(DISTINCT cnic)::INTEGER AS "Actual No of Beneficiaries",
                    MIN(booked_on) AS month_start
                FROM tbl_post_disbursement
                WHERE 1=1
        """

        # ------------------ FILTER: Product ------------------
        product_codes = [code for code in filters.get('product_code', []) if code]
        if product_codes:
            safe_codes = "', '".join(code.replace("'", "''") for code in product_codes)
            query += f" AND product_code IN ('{safe_codes}')"

        # ------------------ FILTER: Historical Growth ------------------
        growth = filters.get('historical_growth')
        if growth and growth != 'all':
            months_map = {
                'last_3_months': 3, 'last_6_months': 6,
                'last_9_months': 9, 'last_12_months': 12
            }
            months = months_map[growth]
            query += f" AND booked_on >= CURRENT_DATE - INTERVAL '{months} months'"

        # ------------------ FILTER: Projection For ------------------
        proj = filters.get('projection_for')
        if proj == 'current_month':
            query += " AND DATE_TRUNC('month', booked_on) = DATE_TRUNC('month', CURRENT_DATE)"
        elif proj == 'current_year':
            query += " AND DATE_PART('year', booked_on) = DATE_PART('year', CURRENT_DATE)"

        # ------------------ Complete monthly_data ------------------
        query += """
                GROUP BY TO_CHAR(booked_on, 'Mon-YYYY'), DATE_TRUNC('month', booked_on)
            ),
            ranked_data AS (
                SELECT
                    "Month",
                    "Actual Disbursement",
                    "Actual No of Beneficiaries",
                    month_start,
                    LAG("Actual Disbursement") OVER (ORDER BY month_start) AS prev_disbursement,
                    LAG("Actual No of Beneficiaries") OVER (ORDER BY month_start) AS prev_beneficiaries
                FROM monthly_data
            )
            SELECT
                "Month",
                "Actual Disbursement",
                "Actual No of Beneficiaries",
                CASE WHEN prev_disbursement IS NOT NULL
                     THEN "Actual Disbursement" - prev_disbursement
                     ELSE NULL END AS growth_disbursement_amount,
                CASE WHEN prev_disbursement IS NOT NULL AND prev_disbursement > 0
                     THEN ROUND((("Actual Disbursement" - prev_disbursement) * 100.0 / prev_disbursement), 2)
                     ELSE NULL END AS growth_disbursement_percentage,
                CASE WHEN prev_beneficiaries IS NOT NULL
                     THEN ("Actual No of Beneficiaries" - prev_beneficiaries)::INTEGER
                     ELSE NULL END AS growth_beneficiaries_count,
                CASE WHEN prev_beneficiaries IS NOT NULL AND prev_beneficiaries > 0
                     THEN ROUND((("Actual No of Beneficiaries" - prev_beneficiaries) * 100.0 / prev_beneficiaries), 2)
                     ELSE NULL END AS growth_beneficiaries_percentage
            FROM ranked_data
            ORDER BY month_start;  -- Chronological order
        """

        print("Final Query:\n", query)
        rows = fetch_records(query)

        return jsonify({'success': True, 'records': rows})

    except Exception as e:
        print("Error:", str(e))

        return jsonify({'success': False, 'error': str(e)})
