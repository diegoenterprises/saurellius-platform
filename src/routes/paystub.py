from flask import Blueprint, request, jsonify
from src.tax_calculator import calculate_federal_income_tax, calculate_federal_payroll_taxes, calculate_state_income_tax, calculate_american_samoa_income_tax, calculate_puerto_rico_income_tax
import datetime
import os
import subprocess
import json

paystub_bp = Blueprint("paystub_bp", __name__)

# Placeholder for gamification logic (to be integrated later)
def award_points_for_paystub_generation(user_id):
    print(f"Awarding points to user {user_id} for paystub generation.")
    # In a real scenario, this would interact with a database or a user service
    pass

@paystub_bp.route("/generate-paystub", methods=["POST"])
def generate_paystub():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # Extract required data for paystub generation
    user_id = data.get("user_id")
    gross_income = data.get("gross_income")
    filing_status = data.get("filing_status")
    state = data.get("state")
    dependents = data.get("dependents", 0)
    pay_date_str = data.get("pay_date", datetime.date.today().isoformat())

    if not all([user_id, gross_income, filing_status, state]):
        return jsonify({"error": "Missing required fields: user_id, gross_income, filing_status, state"}), 400

    try:
        gross_income = float(gross_income)
        pay_date = datetime.date.fromisoformat(pay_date_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid gross_income or pay_date format"}), 400

    # Calculate Federal Income Tax
    federal_income_tax = calculate_federal_income_tax(gross_income, filing_status, pay_date)

    # Calculate Federal Payroll Taxes
    federal_payroll_taxes = calculate_federal_payroll_taxes(gross_income, filing_status, pay_date.year)

    # Calculate State Income Tax
    state_income_tax = 0
    if state.lower() == "american_samoa":
        state_income_tax = calculate_american_samoa_income_tax(gross_income, filing_status, pay_date)
    elif state.lower() == "puerto_rico":
        state_income_tax = calculate_puerto_rico_income_tax(gross_income, filing_status, dependents, pay_date)
    elif state.lower() in ["guam", "usvi", "cnmi"]:
        # Mirror federal for these territories as per comprehensive guide
        state_income_tax = calculate_federal_income_tax(gross_income, filing_status, pay_date)
    else:
        state_income_tax = calculate_state_income_tax(gross_income, filing_status, state, pay_date)

    # Total deductions
    total_deductions = federal_income_tax + federal_payroll_taxes["total_payroll_tax"] + state_income_tax
    net_pay = gross_income - total_deductions

    # Prepare data for PDF generation
    pdf_data = {
        "employee_name": data.get("employee_name", "John Doe"),
        "employer_name": data.get("employer_name", "Acme Corp"),
        "gross_pay": f"{gross_income:.2f}",
        "federal_income_tax": f"{federal_income_tax:.2f}",
        "social_security_tax": f"{federal_payroll_taxes["social_security"]:.2f}",
        "medicare_tax": f"{federal_payroll_taxes["medicare"]:.2f}",
        "state_income_tax": f"{state_income_tax:.2f}",
        "total_deductions": f"{total_deductions:.2f}",
        "net_pay": f"{net_pay:.2f}",
        "pay_period_start": data.get("pay_period_start", "N/A"),
        "pay_period_end": data.get("pay_period_end", "N/A"),
        "pay_date": pay_date_str,
        "filing_status": filing_status,
        "state": state,
        "dependents": dependents
    }

    # Call snappt_compliant_generator.py to create the PDF
    try:
        # Ensure the script is executable and in the path, or provide full path
        pdf_output_path = f"/tmp/{user_id}_paystub_{pay_date_str}.pdf"
        # Pass data as JSON string to the generator script
        command = ["python3", "snappt_compliant_generator.py", json.dumps(pdf_data), pdf_output_path]
        # Assuming snappt_compliant_generator.py is in the same directory or accessible via PATH
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"PDF Generator Output: {result.stdout}")
        print(f"PDF Generator Error: {result.stderr}")

        # In a real app, you would upload this PDF to S3 and return a URL
        # For now, we'll just indicate success and the path
        pdf_url = f"/downloads/{os.path.basename(pdf_output_path)}" # Placeholder URL

        # Award points for gamification
        award_points_for_paystub_generation(user_id)

        return jsonify({
            "message": "Paystub generated successfully",
            "pdf_url": pdf_url,
            "taxes_calculated": {
                "federal_income_tax": f"{federal_income_tax:.2f}",
                "federal_payroll_taxes": federal_payroll_taxes,
                "state_income_tax": f"{state_income_tax:.2f}"
            }
        }), 200
    except subprocess.CalledProcessError as e:
        print(f"PDF Generation Failed: {e.stderr}")
        return jsonify({"error": "Failed to generate PDF", "details": e.stderr}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

@paystub_bp.route("/calculate-taxes", methods=["POST"])
def calculate_taxes():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    gross_income = data.get("gross_income")
    filing_status = data.get("filing_status")
    state = data.get("state")
    dependents = data.get("dependents", 0)
    calculation_date_str = data.get("calculation_date", datetime.date.today().isoformat())

    if not all([gross_income, filing_status, state]):
        return jsonify({"error": "Missing required fields: gross_income, filing_status, state"}), 400

    try:
        gross_income = float(gross_income)
        calculation_date = datetime.date.fromisoformat(calculation_date_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid gross_income or calculation_date format"}), 400

    federal_income_tax = calculate_federal_income_tax(gross_income, filing_status, calculation_date)
    federal_payroll_taxes = calculate_federal_payroll_taxes(gross_income, filing_status, calculation_date.year)

    state_income_tax = 0
    if state.lower() == "american_samoa":
        state_income_tax = calculate_american_samoa_income_tax(gross_income, filing_status, calculation_date)
    elif state.lower() == "puerto_rico":
        state_income_tax = calculate_puerto_rico_income_tax(gross_income, filing_status, dependents, calculation_date)
    elif state.lower() in ["guam", "usvi", "cnmi"]:
        state_income_tax = calculate_federal_income_tax(gross_income, filing_status, calculation_date)
    else:
        state_income_tax = calculate_state_income_tax(gross_income, filing_status, state, calculation_date)

    return jsonify({
        "federal_income_tax": f"{federal_income_tax:.2f}",
        "federal_payroll_taxes": federal_payroll_taxes,
        "state_income_tax": f"{state_income_tax:.2f}",
        "total_deductions": f"{federal_income_tax + federal_payroll_taxes["total_payroll_tax"] + state_income_tax:.2f}",
        "net_pay": f"{gross_income - (federal_income_tax + federal_payroll_taxes["total_payroll_tax"] + state_income_tax):.2f}"
    }), 200

