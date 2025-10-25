"""
Integrated Paystub Generation Route
Combines all utilities: tax engine, YTD continuation, PTO tracking, rewards, verification
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.models.company import Company
from src.utils.complete_tax_engine import CompleteTaxEngine
from src.utils.smart_ytd_continuation import SmartYTDContinuation
from src.utils.pto_tracker import PTOTracker
from src.utils.rewards_calculator import RewardsCalculator
from src.utils.verification_system import VerificationSystem
from src.snappt_compliant_generator import generate_snappt_compliant_paystub
from decimal import Decimal
from datetime import datetime
import boto3
import os

paystub_integrated_bp = Blueprint('paystub_integrated', __name__)

@paystub_integrated_bp.route('/api/paystubs/generate-complete', methods=['POST'])
@jwt_required()
def generate_complete_paystub():
    """
    Generate complete paystub with all features integrated
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get employee
        employee_id = data.get('employee_id')
        employee = Employee.query.get(employee_id)
        if not employee or employee.user_id != user_id:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get YTD data
        ytd_data = SmartYTDContinuation.get_ytd_summary(employee_id)
        
        # Extract pay period data
        pay_date = datetime.strptime(data.get('pay_date'), '%Y-%m-%d').date()
        period_start = datetime.strptime(data.get('period_start'), '%Y-%m-%d').date()
        period_end = datetime.strptime(data.get('period_end'), '%Y-%m-%d').date()
        
        # Extract earnings
        regular_hours = Decimal(str(data.get('regular_hours', 0)))
        overtime_hours = Decimal(str(data.get('overtime_hours', 0)))
        pay_rate = Decimal(str(data.get('pay_rate', employee.pay_rate or 0)))
        
        regular_pay = regular_hours * pay_rate
        overtime_pay = overtime_hours * pay_rate * Decimal('1.5')
        bonus = Decimal(str(data.get('bonus', 0)))
        commission = Decimal(str(data.get('commission', 0)))
        tips = Decimal(str(data.get('tips', 0)))
        
        gross_pay = regular_pay + overtime_pay + bonus + commission + tips
        
        # Calculate all taxes using complete tax engine
        taxes = CompleteTaxEngine.calculate_all_taxes(employee, gross_pay, ytd_data)
        
        # Calculate deductions
        deduction_401k = Decimal(str(data.get('deduction_401k', employee.deduction_401k_fixed or 0)))
        deduction_health = Decimal(str(data.get('deduction_health_insurance', employee.deduction_health_insurance or 0)))
        deduction_dental = Decimal(str(data.get('deduction_dental_insurance', employee.deduction_dental_insurance or 0)))
        deduction_hsa = Decimal(str(data.get('deduction_hsa', employee.deduction_hsa or 0)))
        
        total_deductions = deduction_401k + deduction_health + deduction_dental + deduction_hsa
        
        # Calculate garnishments
        garnishment_child_support = Decimal(str(data.get('garnishment_child_support', employee.garnishment_child_support or 0)))
        garnishment_wage = Decimal(str(data.get('garnishment_wage_garnishment', employee.garnishment_wage_garnishment or 0)))
        total_garnishments = garnishment_child_support + garnishment_wage
        
        # Calculate PTO
        pto_used = {
            'vacation': Decimal(str(data.get('pto_vacation_used', 0))),
            'sick': Decimal(str(data.get('pto_sick_used', 0))),
            'personal': Decimal(str(data.get('pto_personal_used', 0)))
        }
        pto_balances = PTOTracker.calculate_new_balances(employee_id, pto_used, float(regular_hours))
        
        # Calculate net pay
        net_pay = gross_pay - taxes['total_taxes'] - total_deductions - total_garnishments
        
        # Calculate YTD totals
        ytd_gross = ytd_data['ytd_gross'] + gross_pay
        ytd_federal_tax = ytd_data['ytd_federal_tax'] + taxes['federal_income_tax']
        ytd_ss_tax = ytd_data['ytd_ss_tax'] + taxes['social_security_tax']
        ytd_medicare_tax = ytd_data['ytd_medicare_tax'] + taxes['medicare_tax']
        ytd_state_tax = ytd_data['ytd_state_tax'] + taxes['state_income_tax']
        ytd_net = ytd_data['ytd_net'] + net_pay
        
        # Create paystub record
        paystub = Paystub(
            user_id=user_id,
            employee_id=employee_id,
            company_id=employee.company_id,
            pay_date=pay_date,
            period_start_date=period_start,
            period_end_date=period_end,
            paystub_number=ytd_data['paystub_count'] + 1,
            pay_frequency=employee.pay_frequency,
            
            # Hours
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            
            # Earnings
            regular_pay=regular_pay,
            overtime_pay=overtime_pay,
            bonus=bonus,
            commission=commission,
            tips=tips,
            gross_pay=gross_pay,
            
            # Federal Taxes
            federal_income_tax=taxes['federal_income_tax'],
            social_security_tax=taxes['social_security_tax'],
            medicare_tax=taxes['medicare_tax'],
            additional_medicare_tax=taxes['additional_medicare_tax'],
            
            # State Taxes
            state_income_tax=taxes['state_income_tax'],
            state_disability_tax=taxes['state_disability_tax'],
            
            # Local Taxes
            local_income_tax=taxes['local_income_tax'],
            
            # Deductions
            deduction_401k=deduction_401k,
            deduction_health_insurance=deduction_health,
            deduction_dental_insurance=deduction_dental,
            deduction_hsa=deduction_hsa,
            
            # Garnishments
            garnishment_child_support=garnishment_child_support,
            garnishment_wage_garnishment=garnishment_wage,
            
            # Totals
            total_taxes=taxes['total_taxes'],
            total_deductions=total_deductions,
            total_garnishments=total_garnishments,
            net_pay=net_pay,
            
            # YTD
            ytd_gross=ytd_gross,
            ytd_federal_income_tax=ytd_federal_tax,
            ytd_social_security_tax=ytd_ss_tax,
            ytd_medicare_tax=ytd_medicare_tax,
            ytd_state_income_tax=ytd_state_tax,
            ytd_total_taxes=ytd_data['ytd_federal_tax'] + ytd_data['ytd_ss_tax'] + ytd_data['ytd_medicare_tax'] + ytd_data['ytd_state_tax'] + taxes['total_taxes'],
            ytd_net_pay=ytd_net,
            ytd_ss_wages=ytd_data['ytd_ss_wages'] + gross_pay,
            ytd_medicare_wages=ytd_data['ytd_medicare_wages'] + gross_pay,
            
            # PTO
            pto_vacation_used_this_period=pto_used['vacation'],
            pto_sick_used_this_period=pto_used['sick'],
            pto_personal_used_this_period=pto_used['personal'],
            pto_vacation_accrued_this_period=pto_balances['vacation']['accrued'],
            pto_sick_accrued_this_period=pto_balances['sick']['accrued'],
            pto_personal_accrued_this_period=pto_balances['personal']['accrued'],
            pto_vacation_balance=pto_balances['vacation']['balance'],
            pto_sick_balance=pto_balances['sick']['balance'],
            pto_personal_balance=pto_balances['personal']['balance'],
            
            # Tax calculation metadata
            tax_calculation_method='2025_Complete_Engine',
            tax_calculation_timestamp=datetime.utcnow(),
            tax_calculation_version='1.0.0',
            
            status='draft'
        )
        
        db.session.add(paystub)
        db.session.flush()  # Get paystub ID
        
        # Generate PDF using snappt_compliant_generator
        pdf_data = {
            'employee': employee.to_dict(),
            'company': employee.company.to_dict() if employee.company else {},
            'paystub': {
                'pay_date': pay_date.isoformat(),
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'paystub_number': paystub.paystub_number,
                'gross_pay': float(gross_pay),
                'net_pay': float(net_pay),
                'total_taxes': float(taxes['total_taxes']),
                'total_deductions': float(total_deductions),
                'ytd_gross': float(ytd_gross),
                'ytd_net': float(ytd_net)
            }
        }
        
        pdf_content = generate_snappt_compliant_paystub(pdf_data)
        
        # Create verification package
        verification = VerificationSystem.create_verification_package(paystub, pdf_content)
        
        # Update paystub with verification data
        paystub.verification_id = verification['verification_id']
        paystub.document_hash = verification['document_hash']
        paystub.qr_code_data = verification['qr_code_data']
        paystub.verification_url = verification['verification_url']
        
        # Upload PDF to S3
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET_NAME', 'saurellius-paystubs')
        s3_key = f"paystubs/{user_id}/{paystub.id}.pdf"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=pdf_content,
            ContentType='application/pdf'
        )
        
        # Generate signed URL (valid for 7 days)
        pdf_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=604800  # 7 days
        )
        
        paystub.pdf_s3_bucket = bucket_name
        paystub.pdf_s3_key = s3_key
        paystub.pdf_url = pdf_url
        paystub.pdf_generated_at = datetime.utcnow()
        paystub.status = 'finalized'
        paystub.finalized_at = datetime.utcnow()
        
        # Update employee PTO balances
        PTOTracker.update_employee_balances(employee_id, pto_balances)
        
        db.session.commit()
        
        # Award rewards points
        is_first_paystub = ytd_data['paystub_count'] == 0
        if is_first_paystub:
            RewardsCalculator.award_points(user_id, 'first_paystub')
        else:
            RewardsCalculator.award_points(user_id, 'generate_paystub')
        
        # Check for milestones
        RewardsCalculator.check_milestones(user_id)
        
        return jsonify({
            'success': True,
            'paystub_id': str(paystub.id),
            'verification_id': paystub.verification_id,
            'pdf_url': pdf_url,
            'net_pay': float(net_pay),
            'gross_pay': float(gross_pay),
            'paystub_number': paystub.paystub_number
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@paystub_integrated_bp.route('/api/paystubs/continuation/<employee_id>', methods=['GET'])
@jwt_required()
def get_continuation_data(employee_id):
    """
    Get smart YTD continuation data for next paystub
    """
    try:
        user_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)
        
        if not employee or employee.user_id != user_id:
            return jsonify({'error': 'Employee not found'}), 404
        
        continuation_data = SmartYTDContinuation.generate_continuation_data(employee_id)
        
        return jsonify(continuation_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

