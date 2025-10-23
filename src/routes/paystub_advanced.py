"""
Advanced Paystub Routes with YTD Tracking and Intelligent Continuation
Handles paystub generation, management, and history
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import os
from src.models.database import User, Employee, Paystub, RewardActivity, db
from src.routes.auth import token_required
from src.tax_calculator import (
    calculate_federal_income_tax,
    calculate_federal_payroll_taxes,
    calculate_state_income_tax
)
from src.snappt_compliant_generator import generate_snappt_compliant_paystub
import uuid

paystub_advanced_bp = Blueprint('paystub_advanced', __name__)


@paystub_advanced_bp.route('/employees', methods=['GET'])
@token_required
def get_employees(current_user):
    """Get all employees for current user"""
    try:
        employees = Employee.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'employees': [emp.to_dict() for emp in employees]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/employees', methods=['POST'])
@token_required
def create_employee(current_user):
    """
    Create a new employee/payee
    
    Expected JSON:
    {
        "name": "John Doe",
        "ssn_last_four": "6789",
        "date_of_birth": "1990-01-15",
        "address": "123 Main St",
        "employer_name": "ACME Corp",
        "employer_address": "456 Business Ave",
        "employer_ein": "12-3456789",
        "pay_frequency": "biweekly",
        "filing_status": "single",
        "state": "CA",
        "dependents": 0
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        new_employee = Employee(
            user_id=current_user.id,
            name=data['name'],
            ssn_last_four=data.get('ssn_last_four'),
            date_of_birth=datetime.fromisoformat(data['date_of_birth']).date() if 'date_of_birth' in data else None,
            address=data.get('address'),
            employer_name=data.get('employer_name'),
            employer_address=data.get('employer_address'),
            employer_ein=data.get('employer_ein'),
            pay_frequency=data.get('pay_frequency', 'biweekly'),
            filing_status=data.get('filing_status'),
            state=data.get('state'),
            dependents=int(data.get('dependents', 0))
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee created successfully',
            'employee': new_employee.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/employees/<int:employee_id>', methods=['GET'])
@token_required
def get_employee(current_user, employee_id):
    """Get specific employee details"""
    try:
        employee = Employee.query.filter_by(
            id=employee_id,
            user_id=current_user.id
        ).first()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify({
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@token_required
def update_employee(current_user, employee_id):
    """Update employee information"""
    try:
        employee = Employee.query.filter_by(
            id=employee_id,
            user_id=current_user.id
        ).first()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            employee.name = data['name']
        if 'employer_name' in data:
            employee.employer_name = data['employer_name']
        if 'pay_frequency' in data:
            employee.pay_frequency = data['pay_frequency']
        if 'filing_status' in data:
            employee.filing_status = data['filing_status']
        if 'state' in data:
            employee.state = data['state']
        if 'dependents' in data:
            employee.dependents = int(data['dependents'])
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Employee updated successfully',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/generate', methods=['POST'])
@token_required
def generate_paystub(current_user):
    """
    Generate a new paystub with intelligent YTD continuation
    
    Expected JSON:
    {
        "employee_id": 1,
        "gross_pay": 5000.00,
        "pay_period_start": "2025-01-01",
        "pay_period_end": "2025-01-15",
        "pay_date": "2025-01-20",
        "regular_hours": 80,
        "regular_rate": 50.00,
        "overtime_hours": 0,
        "overtime_rate": 75.00,
        "health_insurance": 0,
        "retirement_401k": 0,
        "other_deductions": 0
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'employee_id' not in data or 'gross_pay' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get employee
        employee = Employee.query.filter_by(
            id=data['employee_id'],
            user_id=current_user.id
        ).first()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Parse dates
        pay_period_start = datetime.fromisoformat(data['pay_period_start']).date()
        pay_period_end = datetime.fromisoformat(data['pay_period_end']).date()
        pay_date = datetime.fromisoformat(data['pay_date']).date()
        
        # Get values
        gross_pay = Decimal(str(data['gross_pay']))
        regular_hours = Decimal(str(data.get('regular_hours', 0)))
        regular_rate = Decimal(str(data.get('regular_rate', 0)))
        overtime_hours = Decimal(str(data.get('overtime_hours', 0)))
        overtime_rate = Decimal(str(data.get('overtime_rate', 0)))
        health_insurance = Decimal(str(data.get('health_insurance', 0)))
        retirement_401k = Decimal(str(data.get('retirement_401k', 0)))
        other_deductions = Decimal(str(data.get('other_deductions', 0)))
        
        # Calculate taxes
        federal_income_tax = Decimal(str(calculate_federal_income_tax(
            float(gross_pay),
            employee.filing_status,
            pay_date
        )))
        
        federal_payroll_taxes = calculate_federal_payroll_taxes(
            float(gross_pay),
            employee.filing_status,
            pay_date.year
        )
        
        social_security_tax = Decimal(str(federal_payroll_taxes['social_security']))
        medicare_tax = Decimal(str(federal_payroll_taxes['medicare']))
        additional_medicare_tax = Decimal(str(federal_payroll_taxes.get('additional_medicare', 0)))
        
        state_income_tax = Decimal(str(calculate_state_income_tax(
            float(gross_pay),
            employee.filing_status,
            employee.state,
            pay_date
        )))
        
        # Calculate totals
        total_deductions = (
            federal_income_tax + social_security_tax + medicare_tax +
            additional_medicare_tax + state_income_tax + health_insurance +
            retirement_401k + other_deductions
        )
        
        net_pay = gross_pay - total_deductions
        
        # Update YTD values
        ytd_gross = employee.ytd_gross + gross_pay
        ytd_federal_tax = employee.ytd_federal_tax + federal_income_tax
        ytd_state_tax = employee.ytd_state_tax + state_income_tax
        ytd_social_security = employee.ytd_social_security + social_security_tax
        ytd_medicare = employee.ytd_medicare + medicare_tax
        ytd_net = employee.ytd_net + net_pay
        
        # Create paystub record
        paystub_number = employee.last_paystub_number + 1
        verification_id = f"SAU{pay_date.strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        new_paystub = Paystub(
            user_id=current_user.id,
            employee_id=employee.id,
            paystub_number=paystub_number,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_date,
            gross_pay=gross_pay,
            regular_hours=regular_hours,
            regular_rate=regular_rate,
            overtime_hours=overtime_hours,
            overtime_rate=overtime_rate,
            federal_income_tax=federal_income_tax,
            social_security_tax=social_security_tax,
            medicare_tax=medicare_tax,
            additional_medicare_tax=additional_medicare_tax,
            state_income_tax=state_income_tax,
            health_insurance=health_insurance,
            retirement_401k=retirement_401k,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            net_pay=net_pay,
            ytd_gross=ytd_gross,
            ytd_federal_tax=ytd_federal_tax,
            ytd_state_tax=ytd_state_tax,
            ytd_social_security=ytd_social_security,
            ytd_medicare=ytd_medicare,
            ytd_net=ytd_net,
            verification_id=verification_id
        )
        
        # Generate PDF
        paystub_data = {
            'company': {
                'name': employee.employer_name or 'EMPLOYER NAME',
                'address': employee.employer_address or 'ADDRESS'
            },
            'employee': {
                'name': employee.name,
                'state': employee.state,
                'ssn_masked': f"XXX-XX-{employee.ssn_last_four}" if employee.ssn_last_four else 'XXX-XX-XXXX'
            },
            'pay_info': {
                'period_start': pay_period_start.strftime('%m/%d/%Y'),
                'period_end': pay_period_end.strftime('%m/%d/%Y'),
                'pay_date': pay_date.strftime('%m/%d/%Y')
            },
            'earnings': [
                {'description': 'Regular Earnings', 'rate': str(regular_rate) if regular_rate else '—', 'hours': str(regular_hours) if regular_hours else '—', 'current': float(gross_pay), 'ytd': float(ytd_gross)}
            ],
            'deductions': [
                {'description': 'Federal Tax', 'type': 'Statutory', 'current': float(federal_income_tax), 'ytd': float(ytd_federal_tax)},
                {'description': 'Social Security', 'type': 'Statutory', 'current': float(social_security_tax), 'ytd': float(ytd_social_security)},
                {'description': 'Medicare', 'type': 'Statutory', 'current': float(medicare_tax), 'ytd': float(ytd_medicare)},
                {'description': f'{employee.state} Income Tax', 'type': 'Statutory', 'current': float(state_income_tax), 'ytd': float(ytd_state_tax)}
            ],
            'totals': {
                'gross_pay': float(gross_pay),
                'gross_pay_ytd': float(ytd_gross),
                'net_pay': float(net_pay),
                'net_pay_ytd': float(ytd_net),
                'amount_words': self._amount_to_words(float(net_pay))
            },
            'check_info': {
                'number': str(paystub_number)
            }
        }
        
        # Save PDF
        pdf_path = f"/tmp/paystub_{new_paystub.uuid}.pdf"
        generate_snappt_compliant_paystub(paystub_data, output_path=pdf_path)
        
        # Upload to S3 (placeholder - would need S3 setup)
        new_paystub.pdf_url = f"/downloads/paystub_{new_paystub.uuid}.pdf"
        
        # Update employee YTD
        employee.ytd_gross = ytd_gross
        employee.ytd_federal_tax = ytd_federal_tax
        employee.ytd_state_tax = ytd_state_tax
        employee.ytd_social_security = ytd_social_security
        employee.ytd_medicare = ytd_medicare
        employee.ytd_net = ytd_net
        employee.last_paystub_number = paystub_number
        employee.last_paystub_date = pay_date
        
        db.session.add(new_paystub)
        db.session.commit()
        
        # Award points for gamification
        reward_activity = RewardActivity(
            user_id=current_user.id,
            activity_type='paystub_generated',
            points_earned=50,
            description=f'Generated paystub #{paystub_number}',
            metadata={'paystub_id': new_paystub.id, 'gross_pay': float(gross_pay)}
        )
        
        current_user.reward_points += 50
        current_user.total_lifetime_points += 50
        
        db.session.add(reward_activity)
        db.session.commit()
        
        return jsonify({
            'message': 'Paystub generated successfully',
            'paystub': new_paystub.to_dict(),
            'reward_points_earned': 50
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/history/<int:employee_id>', methods=['GET'])
@token_required
def get_paystub_history(current_user, employee_id):
    """Get paystub history for an employee"""
    try:
        employee = Employee.query.filter_by(
            id=employee_id,
            user_id=current_user.id
        ).first()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        limit = request.args.get('limit', 10, type=int)
        paystubs = Paystub.query.filter_by(
            employee_id=employee_id
        ).order_by(Paystub.pay_date.desc()).limit(limit).all()
        
        return jsonify({
            'paystubs': [p.to_dict() for p in paystubs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/<int:paystub_id>', methods=['GET'])
@token_required
def get_paystub(current_user, paystub_id):
    """Get specific paystub details"""
    try:
        paystub = Paystub.query.filter_by(
            id=paystub_id,
            user_id=current_user.id
        ).first()
        
        if not paystub:
            return jsonify({'error': 'Paystub not found'}), 404
        
        return jsonify({
            'paystub': paystub.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@paystub_advanced_bp.route('/<int:paystub_id>/download', methods=['GET'])
@token_required
def download_paystub(current_user, paystub_id):
    """Download paystub PDF"""
    try:
        paystub = Paystub.query.filter_by(
            id=paystub_id,
            user_id=current_user.id
        ).first()
        
        if not paystub or not paystub.pdf_url:
            return jsonify({'error': 'Paystub not found'}), 404
        
        # Return PDF URL or file
        return jsonify({
            'pdf_url': paystub.pdf_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _amount_to_words(amount):
    """Convert amount to words for paystub"""
    # Simplified version - would need proper implementation
    dollars = int(amount)
    cents = int((amount - dollars) * 100)
    
    ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE']
    teens = ['TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
    tens = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY']
    
    def convert_hundreds(num):
        result = ''
        if num >= 100:
            result += ones[num // 100] + ' HUNDRED '
            num %= 100
        if num >= 20:
            result += tens[num // 10] + ' '
            num %= 10
        if num >= 10:
            result += teens[num - 10] + ' '
        elif num > 0:
            result += ones[num] + ' '
        return result.strip()
    
    if dollars == 0:
        words = 'ZERO'
    elif dollars < 1000:
        words = convert_hundreds(dollars)
    else:
        words = convert_hundreds(dollars // 1000) + ' THOUSAND ' + convert_hundreds(dollars % 1000)
    
    return f"{words.strip()} DOLLARS AND {cents:02d}/100"

