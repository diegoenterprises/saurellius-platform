from flask import Blueprint, jsonify, request, send_file
from src.models.database import db
from src.models.user import User, Employee, Paystub, Company
from src.routes.auth import token_required
from src.utils.ytd_calculator import (
    calculate_ytd_from_previous,
    get_last_paystub_for_employee,
    calculate_next_pay_date,
    calculate_pay_period_dates,
    calculate_pto_balances,
    update_employee_ytd_cache
)
from src.utils.rewards import award_points, check_and_award_milestones
from src.tax_calculator import (
    calculate_federal_income_tax,
    calculate_federal_payroll_taxes,
    calculate_state_income_tax
)
from datetime import datetime, date
from decimal import Decimal
import uuid
import hashlib
import json
import os
from src.snappt_compliant_generator import generate_snappt_compliant_paystub

paystub_complete_bp = Blueprint('paystub_complete', __name__)


def calculate_all_deductions(employee, gross_pay, ytd_ss_wages, ytd_medicare_wages):
    """Calculate all tax withholdings and deductions"""
    deductions = {}
    
    # Federal Income Tax
    federal_tax_result = calculate_federal_income_tax(
        gross_pay=float(gross_pay),
        filing_status=employee.federal_filing_status,
        allowances=employee.federal_allowances,
        additional_withholding=float(employee.federal_additional_withholding) if employee.federal_additional_withholding else 0,
        pay_frequency=employee.pay_frequency
    )
    deductions['federal_income_tax'] = Decimal(str(federal_tax_result))
    
    # Federal Payroll Taxes (FICA)
    payroll_taxes = calculate_federal_payroll_taxes(
        gross_pay=float(gross_pay),
        ytd_ss_wages=float(ytd_ss_wages),
        ytd_medicare_wages=float(ytd_medicare_wages),
        filing_status=employee.federal_filing_status
    )
    deductions['social_security_tax'] = Decimal(str(payroll_taxes['social_security']))
    deductions['medicare_tax'] = Decimal(str(payroll_taxes['medicare']))
    deductions['additional_medicare_tax'] = Decimal(str(payroll_taxes.get('additional_medicare', 0)))
    
    # State Income Tax
    state_tax_result = calculate_state_income_tax(
        gross_pay=float(gross_pay),
        state=employee.address_state,
        filing_status=employee.state_filing_status or employee.federal_filing_status,
        allowances=employee.state_allowances,
        pay_frequency=employee.pay_frequency
    )
    deductions['state_income_tax'] = Decimal(str(state_tax_result))
    
    # State Disability (if applicable - CA, NY, NJ, RI, HI)
    state_disability_states = ['CA', 'NY', 'NJ', 'RI', 'HI']
    if employee.address_state in state_disability_states:
        # California SDI is 1.1% of gross (2025)
        if employee.address_state == 'CA':
            deductions['state_disability_tax'] = Decimal(str(float(gross_pay) * 0.011))
        else:
            deductions['state_disability_tax'] = Decimal('0')
    else:
        deductions['state_disability_tax'] = Decimal('0')
    
    # Local Income Tax (if applicable)
    deductions['local_income_tax'] = Decimal('0')  # TODO: Implement local tax calculation
    
    # Pre-Tax Deductions
    deductions['retirement_401k'] = Decimal(str(employee.retirement_401k_flat_amount or 0))
    if employee.retirement_401k_percent and employee.retirement_401k_percent > 0:
        deductions['retirement_401k'] += Decimal(str(float(gross_pay) * float(employee.retirement_401k_percent) / 100))
    
    deductions['health_insurance'] = Decimal(str(employee.health_insurance_employee_cost or 0))
    deductions['dental_insurance'] = Decimal(str(employee.dental_insurance_employee_cost or 0))
    deductions['vision_insurance'] = Decimal(str(employee.vision_insurance_employee_cost or 0))
    deductions['hsa_contribution'] = Decimal(str(employee.hsa_contribution_per_pay or 0))
    deductions['fsa_contribution'] = Decimal(str(employee.fsa_contribution_per_pay or 0))
    
    # Post-Tax Deductions
    deductions['life_insurance'] = Decimal(str(employee.life_insurance_employee_cost or 0))
    deductions['disability_insurance'] = Decimal(str(employee.disability_insurance_employee_cost or 0))
    
    # Garnishments
    deductions['child_support'] = Decimal(str(employee.child_support_amount or 0))
    if employee.child_support_percentage and employee.child_support_percentage > 0:
        deductions['child_support'] += Decimal(str(float(gross_pay) * float(employee.child_support_percentage) / 100))
    
    deductions['wage_garnishment'] = Decimal(str(employee.wage_garnishment_amount or 0))
    deductions['tax_levy'] = Decimal(str(employee.tax_levy_amount or 0))
    
    # Union Dues
    deductions['union_dues'] = Decimal(str(employee.union_dues_amount or 0)) if employee.union_member else Decimal('0')
    
    # Calculate total deductions
    total_deductions = sum([
        deductions['federal_income_tax'],
        deductions['social_security_tax'],
        deductions['medicare_tax'],
        deductions['additional_medicare_tax'],
        deductions['state_income_tax'],
        deductions['state_disability_tax'],
        deductions['local_income_tax'],
        deductions['retirement_401k'],
        deductions['health_insurance'],
        deductions['dental_insurance'],
        deductions['vision_insurance'],
        deductions['hsa_contribution'],
        deductions['fsa_contribution'],
        deductions['life_insurance'],
        deductions['disability_insurance'],
        deductions['child_support'],
        deductions['wage_garnishment'],
        deductions['tax_levy'],
        deductions['union_dues']
    ])
    
    deductions['total_deductions'] = total_deductions
    deductions['net_pay'] = gross_pay - total_deductions
    
    # SS and Medicare wages (gross minus pre-tax deductions)
    pre_tax_deductions = (
        deductions['retirement_401k'] +
        deductions['health_insurance'] +
        deductions['dental_insurance'] +
        deductions['vision_insurance'] +
        deductions['hsa_contribution'] +
        deductions['fsa_contribution']
    )
    deductions['ss_wages'] = gross_pay - pre_tax_deductions
    deductions['medicare_wages'] = gross_pay - pre_tax_deductions
    
    return deductions


@paystub_complete_bp.route('/generate', methods=['POST'])
@token_required
def generate_paystub(current_user):
    """Generate a complete paystub with YTD tracking and rewards"""
    data = request.get_json()
    
    # Required fields
    required_fields = ['employee_id', 'gross_pay', 'pay_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Get employee
    employee = Employee.query.filter_by(
        id=data['employee_id'],
        user_id=current_user.id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    # Get company
    company = Company.query.filter_by(id=employee.company_id).first()
    if not company:
        return jsonify({'message': 'Company not found'}), 404
    
    # Parse pay date
    pay_date = datetime.strptime(data['pay_date'], '%Y-%m-%d').date()
    
    # Calculate pay period dates
    period_start, period_end = calculate_pay_period_dates(pay_date, employee.pay_frequency)
    
    # Get gross pay
    gross_pay = Decimal(str(data['gross_pay']))
    
    # Get last paystub for YTD continuation
    last_paystub = get_last_paystub_for_employee(employee.id, pay_date.year)
    
    # Calculate YTD values for tax calculations
    ytd_ss_wages = float(last_paystub.ytd_ss_wages) if last_paystub else 0.0
    ytd_medicare_wages = float(last_paystub.ytd_medicare_wages) if last_paystub else 0.0
    
    # Calculate all deductions
    deductions = calculate_all_deductions(employee, gross_pay, ytd_ss_wages, ytd_medicare_wages)
    
    # Calculate YTD totals with smart continuation
    ytd_totals = calculate_ytd_from_previous(employee.id, gross_pay, deductions, pay_date.year)
    
    # Calculate PTO balances
    hours_used = {
        'vacation': data.get('vacation_hours_used', 0),
        'sick': data.get('sick_hours_used', 0),
        'personal': data.get('personal_hours_used', 0)
    }
    pto_balances = calculate_pto_balances(employee, last_paystub, hours_used)
    
    # Generate verification data
    verification_id = str(uuid.uuid4())[:8].upper()
    document_serial = f"PS-{pay_date.year}-{ytd_totals['paystub_number']:04d}-{verification_id}"
    
    # Create paystub record
    paystub = Paystub(
        employee_id=employee.id,
        company_id=company.id,
        user_id=current_user.id,
        
        # Pay Period Info
        period_start_date=period_start,
        period_end_date=period_end,
        pay_date=pay_date,
        check_number=data.get('check_number'),
        paystub_number=ytd_totals['paystub_number'],
        pay_frequency=employee.pay_frequency,
        
        # Hours
        regular_hours=Decimal(str(data.get('regular_hours', 0))),
        overtime_hours=Decimal(str(data.get('overtime_hours', 0))),
        vacation_hours=Decimal(str(data.get('vacation_hours', 0))),
        sick_hours=Decimal(str(data.get('sick_hours', 0))),
        
        # Earnings
        regular_earnings=Decimal(str(data.get('regular_earnings', gross_pay))),
        overtime_earnings=Decimal(str(data.get('overtime_earnings', 0))),
        bonus=Decimal(str(data.get('bonus', 0))),
        commission=Decimal(str(data.get('commission', 0))),
        gross_pay=gross_pay,
        
        # Current Period Deductions
        federal_income_tax=deductions['federal_income_tax'],
        social_security_tax=deductions['social_security_tax'],
        medicare_tax=deductions['medicare_tax'],
        additional_medicare_tax=deductions['additional_medicare_tax'],
        state_income_tax=deductions['state_income_tax'],
        state_disability_tax=deductions['state_disability_tax'],
        local_income_tax=deductions['local_income_tax'],
        
        retirement_401k=deductions['retirement_401k'],
        health_insurance=deductions['health_insurance'],
        dental_insurance=deductions['dental_insurance'],
        vision_insurance=deductions['vision_insurance'],
        hsa_contribution=deductions['hsa_contribution'],
        fsa_contribution=deductions['fsa_contribution'],
        
        life_insurance=deductions['life_insurance'],
        disability_insurance=deductions['disability_insurance'],
        
        child_support=deductions['child_support'],
        wage_garnishment=deductions['wage_garnishment'],
        tax_levy=deductions['tax_levy'],
        union_dues=deductions['union_dues'],
        
        net_pay=deductions['net_pay'],
        
        # YTD Totals
        ytd_gross_pay=ytd_totals['ytd_gross_pay'],
        ytd_net_pay=ytd_totals['ytd_net_pay'],
        ytd_federal_income_tax=ytd_totals['ytd_federal_income_tax'],
        ytd_social_security_tax=ytd_totals['ytd_social_security_tax'],
        ytd_medicare_tax=ytd_totals['ytd_medicare_tax'],
        ytd_additional_medicare_tax=ytd_totals['ytd_additional_medicare_tax'],
        ytd_state_income_tax=ytd_totals['ytd_state_income_tax'],
        ytd_state_disability_tax=ytd_totals['ytd_state_disability_tax'],
        ytd_local_income_tax=ytd_totals['ytd_local_income_tax'],
        ytd_retirement_401k=ytd_totals['ytd_retirement_401k'],
        ytd_health_insurance=ytd_totals['ytd_health_insurance'],
        ytd_dental_insurance=ytd_totals['ytd_dental_insurance'],
        ytd_vision_insurance=ytd_totals['ytd_vision_insurance'],
        ytd_hsa_contribution=ytd_totals['ytd_hsa_contribution'],
        
        ytd_ss_wages=ytd_totals['ytd_ss_wages'],
        ytd_medicare_wages=ytd_totals['ytd_medicare_wages'],
        ss_wage_base_reached=ytd_totals['ss_wage_base_reached'],
        additional_medicare_threshold_reached=ytd_totals['additional_medicare_threshold_reached'],
        
        # PTO Balances
        vacation_accrued_this_period=Decimal(str(pto_balances['vacation_accrued_this_period'])),
        vacation_used_this_period=Decimal(str(pto_balances['vacation_used_this_period'])),
        vacation_balance=Decimal(str(pto_balances['vacation_balance'])),
        sick_accrued_this_period=Decimal(str(pto_balances['sick_accrued_this_period'])),
        sick_used_this_period=Decimal(str(pto_balances['sick_used_this_period'])),
        sick_balance=Decimal(str(pto_balances['sick_balance'])),
        personal_accrued_this_period=Decimal(str(pto_balances['personal_accrued_this_period'])),
        personal_used_this_period=Decimal(str(pto_balances['personal_used_this_period'])),
        personal_balance=Decimal(str(pto_balances['personal_balance'])),
        
        # Verification
        verification_id=verification_id,
        document_serial=document_serial,
        document_hash=hashlib.sha256(document_serial.encode()).hexdigest(),
        
        # Tax Calculation Details
        tax_calculation_method='Percentage',
        tax_engine_version='2025.1',
        
        # Metadata
        generated_by_user_id=current_user.id,
        is_void=False
    )
    
    db.session.add(paystub)
    db.session.flush()
    
    # Generate PDF using the perfect snappt_compliant_generator
    pdf_filename = f"paystub_{paystub.id}_{paystub.paystub_number}_{pay_date.strftime('%Y%m%d')}.pdf"
    pdf_output_path = f"/tmp/{pdf_filename}"
    
    # Prepare data for PDF generator
    paystub_pdf_data = {
        'company': {
            'name': company.legal_name,
            'address': f"{company.address_street}, {company.address_city}, {company.address_state} {company.address_zip}" if company.address_street else 'N/A',
            'ein': company.ein
        },
        'employee': {
            'name': employee.get_full_name().upper(),
            'address': f"{employee.address_street}, {employee.address_city}, {employee.address_state} {employee.address_zip}" if employee.address_street else 'N/A',
            'state': employee.address_state,
            'ssn_masked': f"XXX-XX-{employee.ssn_last_four}"
        },
        'pay_info': {
            'period_start': period_start.strftime('%m/%d/%Y'),
            'period_end': period_end.strftime('%m/%d/%Y'),
            'pay_date': pay_date.strftime('%m/%d/%Y'),
            'check_number': paystub.check_number or f"CHK{paystub.paystub_number:06d}"
        },
        'earnings': [
            {'description': 'Regular Pay', 'hours': float(paystub.regular_hours), 'rate': float(employee.hourly_rate) if employee.hourly_rate else 0, 'current': float(paystub.regular_earnings), 'ytd': float(paystub.ytd_gross_pay)},
        ],
        'deductions': [
            {'description': 'Federal Income Tax', 'current': float(paystub.federal_income_tax), 'ytd': float(paystub.ytd_federal_income_tax)},
            {'description': 'Social Security', 'current': float(paystub.social_security_tax), 'ytd': float(paystub.ytd_social_security_tax)},
            {'description': 'Medicare', 'current': float(paystub.medicare_tax), 'ytd': float(paystub.ytd_medicare_tax)},
            {'description': 'State Income Tax', 'current': float(paystub.state_income_tax), 'ytd': float(paystub.ytd_state_income_tax)},
        ],
        'summary': {
            'gross_pay': float(paystub.gross_pay),
            'total_deductions': float(paystub.federal_income_tax + paystub.social_security_tax + paystub.medicare_tax + paystub.state_income_tax),
            'net_pay': float(paystub.net_pay),
            'ytd_gross': float(paystub.ytd_gross_pay),
            'ytd_net': float(paystub.ytd_net_pay)
        },
        'verification': {
            'verification_id': paystub.verification_id,
            'document_serial': paystub.document_serial,
            'document_hash': paystub.document_hash
        }
    }
    
    # Generate the PDF
    try:
        pdf_path = generate_snappt_compliant_paystub(
            paystub_data=paystub_pdf_data,
            template_id="eusotrip_original",
            output_path=pdf_output_path
        )
        
        # Update paystub with PDF info
        paystub.pdf_url = f"/api/paystubs/{paystub.id}/download"
        paystub.pdf_generated_at = datetime.utcnow()
        if os.path.exists(pdf_path):
            paystub.pdf_file_size_bytes = os.path.getsize(pdf_path)
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Continue even if PDF generation fails
    
    # Update employee YTD cache
    update_employee_ytd_cache(employee.id)
    
    # Update user lifetime paystubs
    current_user.lifetime_paystubs_generated += 1
    
    # Award rewards points
    award_points(current_user.id, 'paystub_generated', f'Generated paystub #{paystub.paystub_number}')
    
    # Check for milestones
    check_and_award_milestones(current_user.id, current_user.lifetime_paystubs_generated)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Paystub generated successfully',
        'paystub': {
            'id': paystub.id,
            'uuid': paystub.uuid,
            'paystub_number': paystub.paystub_number,
            'pay_date': paystub.pay_date.isoformat(),
            'gross_pay': float(paystub.gross_pay),
            'net_pay': float(paystub.net_pay),
            'ytd_gross_pay': float(paystub.ytd_gross_pay),
            'ytd_net_pay': float(paystub.ytd_net_pay),
            'verification_id': paystub.verification_id,
            'document_serial': paystub.document_serial
        },
        'rewards': {
            'points_earned': 50,
            'total_points': current_user.reward_points,
            'tier': current_user.reward_tier
        }
    }), 201


@paystub_complete_bp.route('/generate-next/<int:employee_id>', methods=['POST'])
@token_required
def generate_next_paystub(current_user, employee_id):
    """Smart generation of next paystub with automatic YTD continuation"""
    employee = Employee.query.filter_by(
        id=employee_id,
        user_id=current_user.id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    
    # Get last paystub
    last_paystub = get_last_paystub_for_employee(employee_id)
    
    if not last_paystub:
        return jsonify({'message': 'No previous paystub found. Please use /generate endpoint.'}), 400
    
    # Calculate next pay date
    next_pay_date = calculate_next_pay_date(last_paystub.pay_date, employee.pay_frequency)
    
    # Use same gross pay as last paystub (user can override)
    data = request.get_json() or {}
    gross_pay = data.get('gross_pay', float(last_paystub.gross_pay))
    
    # Call the main generate function
    return generate_paystub(current_user)


@paystub_complete_bp.route('/history', methods=['GET'])
@token_required
def get_paystub_history(current_user):
    """Get paystub history for the current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    employee_id = request.args.get('employee_id', type=int)
    
    query = Paystub.query.filter_by(user_id=current_user.id, is_void=False)
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    paystubs = query.order_by(Paystub.pay_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    paystub_list = []
    for ps in paystubs.items:
        employee = Employee.query.get(ps.employee_id)
        paystub_list.append({
            'id': ps.id,
            'uuid': ps.uuid,
            'paystub_number': ps.paystub_number,
            'employee_name': employee.get_full_name() if employee else None,
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
        'paystubs': paystub_list,
        'pagination': {
            'page': paystubs.page,
            'per_page': paystubs.per_page,
            'total': paystubs.total,
            'pages': paystubs.pages
        }
    }), 200


@paystub_complete_bp.route('/<int:paystub_id>', methods=['GET'])
@token_required
def get_paystub_details(current_user, paystub_id):
    """Get detailed information for a specific paystub"""
    paystub = Paystub.query.filter_by(
        id=paystub_id,
        user_id=current_user.id
    ).first()
    
    if not paystub:
        return jsonify({'message': 'Paystub not found'}), 404
    
    employee = Employee.query.get(paystub.employee_id)
    company = Company.query.get(paystub.company_id)
    
    return jsonify({
        'paystub': {
            'id': paystub.id,
            'uuid': paystub.uuid,
            'paystub_number': paystub.paystub_number,
            'pay_date': paystub.pay_date.isoformat(),
            'period_start_date': paystub.period_start_date.isoformat(),
            'period_end_date': paystub.period_end_date.isoformat(),
            'pay_frequency': paystub.pay_frequency,
            
            'employee': {
                'name': employee.get_full_name() if employee else None,
                'address': f"{employee.address_street}, {employee.address_city}, {employee.address_state} {employee.address_zip}" if employee else None
            },
            
            'company': {
                'name': company.legal_name if company else None,
                'address': f"{company.address_street}, {company.address_city}, {company.address_state} {company.address_zip}" if company else None,
                'ein': company.ein if company else None
            },
            
            'earnings': {
                'regular_hours': float(paystub.regular_hours),
                'overtime_hours': float(paystub.overtime_hours),
                'regular_earnings': float(paystub.regular_earnings),
                'overtime_earnings': float(paystub.overtime_earnings),
                'bonus': float(paystub.bonus),
                'commission': float(paystub.commission),
                'gross_pay': float(paystub.gross_pay)
            },
            
            'deductions': {
                'federal_income_tax': float(paystub.federal_income_tax),
                'social_security_tax': float(paystub.social_security_tax),
                'medicare_tax': float(paystub.medicare_tax),
                'state_income_tax': float(paystub.state_income_tax),
                'retirement_401k': float(paystub.retirement_401k),
                'health_insurance': float(paystub.health_insurance),
                'dental_insurance': float(paystub.dental_insurance),
                'vision_insurance': float(paystub.vision_insurance)
            },
            
            'net_pay': float(paystub.net_pay),
            
            'ytd_totals': {
                'gross_pay': float(paystub.ytd_gross_pay),
                'net_pay': float(paystub.ytd_net_pay),
                'federal_income_tax': float(paystub.ytd_federal_income_tax),
                'social_security_tax': float(paystub.ytd_social_security_tax),
                'medicare_tax': float(paystub.ytd_medicare_tax),
                'state_income_tax': float(paystub.ytd_state_income_tax)
            },
            
            'pto_balances': {
                'vacation': float(paystub.vacation_balance),
                'sick': float(paystub.sick_balance),
                'personal': float(paystub.personal_balance)
            },
            
            'verification': {
                'verification_id': paystub.verification_id,
                'document_serial': paystub.document_serial,
                'document_hash': paystub.document_hash
            },
            
            'pdf_url': paystub.pdf_url,
            'created_at': paystub.created_at.isoformat()
        }
    }), 200

