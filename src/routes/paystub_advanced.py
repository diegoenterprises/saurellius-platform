from flask import Blueprint, jsonify, request, send_file
from src.models.database import db
from src.models.user import User, RewardActivity
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.routes.auth import token_required
    paystubs = Paystub.query.filter_by(employee_id=employee_id).all()
    ytd_gross = sum(p.gross_pay for p in paystubs)
    ytd_net = sum(p.net_pay for p in paystubs)
    return ytd_gross, ytd_net

@paystub_advanced_bp.route("/employee", methods=["POST"])
@token_required
def add_employee(current_user):
    data = request.get_json()
    name = data.get("name")
    
    if not name:
        return jsonify({"message": "Employee name is required"}), 400
    
    employee = Employee(user_id=current_user.id, name=name)
    db.session.add(employee)
    db.session.commit()
    
    return jsonify({"message": "Employee added successfully", "employee": {"id": employee.id, "name": employee.name}}), 201

@paystub_advanced_bp.route("/employee/<int:employee_id>", methods=["GET"])
@token_required
def get_employee(current_user, employee_id):
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    if not employee:
        return jsonify({"message": "Employee not found"}), 404
        
    ytd_gross, ytd_net = calculate_ytd_for_employee(employee_id)
    
    return jsonify({
        "id": employee.id,
        "name": employee.name,
        "ytd_gross": f"{ytd_gross:.2f}",
        "ytd_net": f"{ytd_net:.2f}"
    }), 200

@paystub_advanced_bp.route("/employees", methods=["GET"])
@token_required
def get_employees(current_user):
    employees = Employee.query.filter_by(user_id=current_user.id).all()
    
    employee_list = []
    for employee in employees:
        ytd_gross, ytd_net = calculate_ytd_for_employee(employee.id)
        employee_list.append({
            "id": employee.id,
            "name": employee.name,
            "ytd_gross": f"{ytd_gross:.2f}",
            "ytd_net": f"{ytd_net:.2f}"
        })
        
    return jsonify(employee_list), 200


@paystub_advanced_bp.route("/generate", methods=["POST"])
@token_required
def generate_paystub_pdf(current_user):
    data = request.get_json()
    
    # 1. Input Validation and Subscription Check
    if not current_user.is_active_subscriber:
        return jsonify({"message": "Subscription required to generate paystubs"}), 403
    
    # Basic required fields
    employee_id = data.get("employee_id")
    gross_income = data.get("gross_income")
    pay_date_str = data.get("pay_date")
    filing_status = data.get("filing_status", "single")
    state = data.get("state", "Calif")
    
    if not all([employee_id, gross_income, pay_date_str]):
        return jsonify({"message": "Missing required fields: employee_id, gross_income, pay_date"}), 400

    try:
        gross_income = float(gross_income)
        pay_date = datetime.strptime(pay_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid format for gross_income or pay_date"}), 400
        
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    if not employee:
        return jsonify({"message": "Employee not found"}), 404
        
    # 2. Tax Calculation
    federal_income_tax = calculate_federal_income_tax(gross_income, filing_status, pay_date)
    federal_payroll_taxes = calculate_federal_payroll_taxes(gross_income, filing_status, pay_date.year)
    state_income_tax = calculate_state_income_tax(gross_income, filing_status, state, pay_date)
    
    total_deductions = federal_income_tax + federal_payroll_taxes["total_payroll_tax"] + state_income_tax
    net_pay = gross_income - total_deductions

    # 3. YTD Calculation and Update
    current_ytd_gross, current_ytd_net = calculate_ytd_for_employee(employee_id)
    new_ytd_gross = current_ytd_gross + gross_income
    new_ytd_net = current_ytd_net + net_pay
    
    # 4. Prepare Paystub Data for PDF Generator
    paystub_data = {
        "company": data.get("company_info", {"name": "SAURELLIUS PAYSTUB", "address": "123 Main St, Anytown, USA"}),
        "employee": {
            "name": employee.name,
            "state": state,
            "ssn_masked": data.get("ssn_masked", "XXX-XX-XXXX")
        },
        "pay_info": {
            "period_start": data.get("period_start", "N/A"),
            "period_end": data.get("period_end", "N/A"),
            "pay_date": pay_date_str
        },
        "earnings": [
            {"description": "Regular Earnings", "rate": "—", "hours": "—", "current": gross_income, "ytd": new_ytd_gross}
        ],
        "deductions": [
            {"description": "Federal Income Tax", "type": "Statutory", "current": federal_income_tax, "ytd": current_ytd_gross + federal_income_tax},
            {"description": "Social Security", "type": "Statutory", "current": federal_payroll_taxes["social_security"], "ytd": current_ytd_gross + federal_payroll_taxes["social_security"]},
            {"description": "Medicare", "type": "Statutory", "current": federal_payroll_taxes["medicare"], "ytd": current_ytd_gross + federal_payroll_taxes["medicare"]},
            {"description": f"{state} Income Tax", "type": "Statutory", "current": state_income_tax, "ytd": current_ytd_gross + state_income_tax},
        ],
        "totals": {
            "gross_pay": gross_income,
            "gross_pay_ytd": new_ytd_gross,
            "net_pay": net_pay,
            "net_pay_ytd": new_ytd_net,
            "amount_words": "AMOUNT IN WORDS PLACEHOLDER" # Requires a number-to-words library, which is a future feature
        },
        "check_info": {
            "number": data.get("check_number", "DIRECT DEPOSIT")
        }
    }
    
    # 5. Generate PDF
    pdf_buffer = generate_snappt_compliant_paystub(paystub_data, output_path=None) # Returns a BytesIO buffer
    
    # 6. Record Paystub and Reward User
    paystub_record = Paystub(
        user_id=current_user.id,
        employee_id=employee_id,
        pay_date=pay_date,
        gross_pay=gross_income,
        net_pay=net_pay,
        tax_details=json.dumps(paystub_data["deductions"])
    )
    db.session.add(paystub_record)
    
    # Update user and employee YTD
    current_user.lifetime_paystubs_generated += 1
    current_user.reward_points += PAYSTUB_REWARD_POINTS
    
    reward_activity = RewardActivity(
        user_id=current_user.id,
        type="paystub_generated",
        points_awarded=PAYSTUB_REWARD_POINTS
    )
    db.session.add(reward_activity)
    
    db.session.commit()
    
    # 7. Return PDF
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"paystub_{employee.name}_{pay_date_str}.pdf"
    )

@paystub_advanced_bp.route("/history", methods=["GET"])
@token_required
def paystub_history(current_user):
    paystubs = Paystub.query.filter_by(user_id=current_user.id).order_by(Paystub.pay_date.desc()).all()
    
    history = []
    for p in paystubs:
        employee = Employee.query.get(p.employee_id)
        history.append({
            "id": p.id,
            "employee_name": employee.name if employee else "N/A",
            "pay_date": p.pay_date.isoformat(),
            "gross_pay": f"{p.gross_pay:.2f}",
            "net_pay": f"{p.net_pay:.2f}",
            "tax_details": json.loads(p.tax_details)
        })
        
    return jsonify(history), 200
