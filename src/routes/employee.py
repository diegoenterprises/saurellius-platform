from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User\nfrom src.models.employee import Employee\nfrom src.models.company import Company\nfrom src.models.paystub import Paystub
from src.routes.auth import token_required
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64

employee_bp = Blueprint('employee', __name__)

# SSN Encryption Key (should be in environment variable in production)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY if isinstance(ENCRYPTION_KEY, bytes) else ENCRYPTION_KEY.encode())


def encrypt_ssn(ssn):
    """Encrypt SSN using Fernet symmetric encryption"""
    return cipher_suite.encrypt(ssn.encode()).decode()


def decrypt_ssn(encrypted_ssn):
    """Decrypt SSN"""
    return cipher_suite.decrypt(encrypted_ssn.encode()).decode()


@employee_bp.route('/', methods=['POST'])
@token_required
def create_employee(current_user):
    """Create a new employee"""
    data = request.get_json()
    
    # Required fields
    required_fields = ['first_name', 'last_name', 'ssn', 'address_state', 
                      'federal_filing_status', 'employment_type', 'pay_structure', 'pay_frequency']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Get or create default company for user
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        # Create default company
        company = Company(
            user_id=current_user.id,
            legal_name=data.get('company_name', f"{current_user.username}'s Company"),
            ein=data.get('ein', '00-0000000'),
            address_state=data.get('address_state', 'CA')
        )
        db.session.add(company)
        db.session.flush()
    
    # Encrypt SSN
    ssn = data['ssn'].replace('-', '')
    ssn_last_four = ssn[-4:]
    encrypted_ssn = encrypt_ssn(ssn)
    
    # Create employee
    employee = Employee(
        company_id=company.id,
        user_id=current_user.id,
        first_name=data['first_name'],
        middle_name=data.get('middle_name'),
        last_name=data['last_name'],
        ssn_encrypted=encrypted_ssn,
        ssn_last_four=ssn_last_four,
        date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
        employee_id=data.get('employee_id'),
        hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date() if data.get('hire_date') else None,
        
        # Contact
        address_street=data.get('address_street'),
        address_city=data.get('address_city'),
        address_state=data['address_state'],
        address_zip=data.get('address_zip'),
        address_county=data.get('address_county'),
        email=data.get('email'),
        phone=data.get('phone'),
        
        # Tax Filing Status
        federal_filing_status=data['federal_filing_status'],
        federal_allowances=data.get('federal_allowances', 0),
        federal_additional_withholding=data.get('federal_additional_withholding', 0),
        federal_extra_withholding_per_pay=data.get('federal_extra_withholding_per_pay', 0),
        federal_w4_year=data.get('federal_w4_year', datetime.now().year),
        
        state_filing_status=data.get('state_filing_status'),
        state_allowances=data.get('state_allowances', 0),
        state_additional_withholding=data.get('state_additional_withholding', 0),
        
        # Local Tax
        local_jurisdiction_code=data.get('local_jurisdiction_code'),
        local_resident=data.get('local_resident', True),
        local_work_location=data.get('local_work_location'),
        
        # Employment Classification
        employment_type=data['employment_type'],
        pay_structure=data['pay_structure'],
        exempt_from_overtime=data.get('exempt_from_overtime', False),
        
        # Compensation
        hourly_rate=data.get('hourly_rate'),
        overtime_rate=data.get('overtime_rate'),
        double_time_rate=data.get('double_time_rate'),
        annual_salary=data.get('annual_salary'),
        pay_frequency=data['pay_frequency'],
        
        # PTO Accrual Rates
        vacation_accrual_rate=data.get('vacation_accrual_rate', 0),
        sick_accrual_rate=data.get('sick_accrual_rate', 0),
        personal_accrual_rate=data.get('personal_accrual_rate', 0),
        
        # Deduction Elections
        retirement_401k_percent=data.get('retirement_401k_percent', 0),
        retirement_401k_flat_amount=data.get('retirement_401k_flat_amount', 0),
        retirement_type=data.get('retirement_type'),
        
        health_insurance_employee_cost=data.get('health_insurance_employee_cost', 0),
        dental_insurance_employee_cost=data.get('dental_insurance_employee_cost', 0),
        vision_insurance_employee_cost=data.get('vision_insurance_employee_cost', 0),
        
        hsa_contribution_per_pay=data.get('hsa_contribution_per_pay', 0),
        fsa_contribution_per_pay=data.get('fsa_contribution_per_pay', 0),
        
        life_insurance_employee_cost=data.get('life_insurance_employee_cost', 0),
        disability_insurance_employee_cost=data.get('disability_insurance_employee_cost', 0),
        
        # Garnishments
        child_support_amount=data.get('child_support_amount', 0),
        child_support_percentage=data.get('child_support_percentage', 0),
        wage_garnishment_amount=data.get('wage_garnishment_amount', 0),
        tax_levy_amount=data.get('tax_levy_amount', 0),
        
        # Union
        union_member=data.get('union_member', False),
        union_dues_amount=data.get('union_dues_amount', 0),
        
        is_active=True
    )
    
    db.session.add(employee)
    db.session.commit()
    
    return jsonify({
        'message': 'Employee created successfully',
        'employee': {
            'id': employee.id,
            'uuid': employee.uuid,
            'name': employee.get_full_name(),
            'email': employee.email,
            'state': employee.address_state
        }
    }), 201


@employee_bp.route('/<int:employee_id>', methods=['GET'])
@token_required
def get_employee(current_user, employee_id):
    """Get employee details"""
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    return jsonify({
        'employee': {
            'id': employee.id,
            'uuid': employee.uuid,
            'first_name': employee.first_name,
            'middle_name': employee.middle_name,
            'last_name': employee.last_name,
            'full_name': employee.get_full_name(),
            'ssn_last_four': employee.ssn_last_four,
            'date_of_birth': employee.date_of_birth.isoformat() if employee.date_of_birth else None,
            'employee_id': employee.employee_id,
            'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
            
            'address_street': employee.address_street,
            'address_city': employee.address_city,
            'address_state': employee.address_state,
            'address_zip': employee.address_zip,
            'address_county': employee.address_county,
            'email': employee.email,
            'phone': employee.phone,
            
            'federal_filing_status': employee.federal_filing_status,
            'federal_allowances': employee.federal_allowances,
            'state_filing_status': employee.state_filing_status,
            
            'employment_type': employee.employment_type,
            'pay_structure': employee.pay_structure,
            'hourly_rate': float(employee.hourly_rate) if employee.hourly_rate else None,
            'annual_salary': float(employee.annual_salary) if employee.annual_salary else None,
            'pay_frequency': employee.pay_frequency,
            
            'is_active': employee.is_active,
            'ytd_gross': float(employee.ytd_gross) if employee.ytd_gross else 0.0,
            'ytd_net': float(employee.ytd_net) if employee.ytd_net else 0.0
        }
    }), 200


@employee_bp.route('/<int:employee_id>', methods=['PUT'])
@token_required
def update_employee(current_user, employee_id):
    """Update employee details"""
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'first_name' in data:
        employee.first_name = data['first_name']
    if 'middle_name' in data:
        employee.middle_name = data['middle_name']
    if 'last_name' in data:
        employee.last_name = data['last_name']
    if 'email' in data:
        employee.email = data['email']
    if 'phone' in data:
        employee.phone = data['phone']
    if 'address_street' in data:
        employee.address_street = data['address_street']
    if 'address_city' in data:
        employee.address_city = data['address_city']
    if 'address_state' in data:
        employee.address_state = data['address_state']
    if 'address_zip' in data:
        employee.address_zip = data['address_zip']
    if 'hourly_rate' in data:
        employee.hourly_rate = data['hourly_rate']
    if 'annual_salary' in data:
        employee.annual_salary = data['annual_salary']
    if 'federal_filing_status' in data:
        employee.federal_filing_status = data['federal_filing_status']
    if 'is_active' in data:
        employee.is_active = data['is_active']
    
    employee.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Employee updated successfully',
        'employee': {
            'id': employee.id,
            'name': employee.get_full_name()
        }
    }), 200


@employee_bp.route('/<int:employee_id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, employee_id):
    """Delete (deactivate) employee"""
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    # Soft delete - just mark as inactive
    employee.is_active = False
    employee.termination_date = datetime.now().date()
    employee.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Employee deactivated successfully'}), 200


@employee_bp.route('/<int:employee_id>/paystubs', methods=['GET'])
@token_required
def get_employee_paystubs(current_user, employee_id):
    """Get all paystubs for an employee"""
    employee = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    paystubs = Paystub.query.filter_by(
        employee_id=employee_id,
        is_void=False
    ).order_by(Paystub.pay_date.desc()).all()
    
    paystub_list = []
    for ps in paystubs:
        paystub_list.append({
            'id': ps.id,
            'uuid': ps.uuid,
            'paystub_number': ps.paystub_number,
            'pay_date': ps.pay_date.isoformat(),
            'period_start_date': ps.period_start_date.isoformat(),
            'period_end_date': ps.period_end_date.isoformat(),
            'gross_pay': float(ps.gross_pay),
            'net_pay': float(ps.net_pay),
            'ytd_gross_pay': float(ps.ytd_gross_pay),
            'ytd_net_pay': float(ps.ytd_net_pay),
            'pdf_url': ps.pdf_url,
            'created_at': ps.created_at.isoformat()
        })
    
    return jsonify({
        'employee': {
            'id': employee.id,
            'name': employee.get_full_name()
        },
        'paystubs': paystub_list,
        'total_count': len(paystub_list)
    }), 200

