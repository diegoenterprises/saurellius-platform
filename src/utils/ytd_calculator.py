"""
YTD (Year-to-Date) Calculator and Smart Continuation Logic
This module handles automatic YTD tracking and continuation from previous paystubs
"""

from src.models.paystub import Paystub
from src.models.employee import Employee
from sqlalchemy import func, extract, desc
from datetime import datetime, date, timedelta
from decimal import Decimal


def get_last_paystub_for_employee(employee_id, year=None):
    """Get the most recent paystub for an employee in a given year"""
    if year is None:
        year = datetime.now().year
    
    last_paystub = Paystub.query.filter_by(
        employee_id=employee_id,
        is_void=False
    ).filter(
        extract('year', Paystub.pay_date) == year
    ).order_by(desc(Paystub.pay_date)).first()
    
    return last_paystub


def calculate_ytd_from_previous(employee_id, current_gross, current_deductions, year=None):
    """
    Calculate YTD totals by adding current period to previous YTD
    This is the SMART CONTINUATION logic
    """
    if year is None:
        year = datetime.now().year
    
    last_paystub = get_last_paystub_for_employee(employee_id, year)
    
    if last_paystub:
        # Continue from last paystub
        ytd_totals = {
            'ytd_gross_pay': Decimal(str(last_paystub.ytd_gross_pay)) + Decimal(str(current_gross)),
            'ytd_net_pay': Decimal(str(last_paystub.ytd_net_pay)) + Decimal(str(current_deductions['net_pay'])),
            'ytd_federal_income_tax': Decimal(str(last_paystub.ytd_federal_income_tax)) + Decimal(str(current_deductions.get('federal_income_tax', 0))),
            'ytd_social_security_tax': Decimal(str(last_paystub.ytd_social_security_tax)) + Decimal(str(current_deductions.get('social_security_tax', 0))),
            'ytd_medicare_tax': Decimal(str(last_paystub.ytd_medicare_tax)) + Decimal(str(current_deductions.get('medicare_tax', 0))),
            'ytd_additional_medicare_tax': Decimal(str(last_paystub.ytd_additional_medicare_tax)) + Decimal(str(current_deductions.get('additional_medicare_tax', 0))),
            'ytd_state_income_tax': Decimal(str(last_paystub.ytd_state_income_tax)) + Decimal(str(current_deductions.get('state_income_tax', 0))),
            'ytd_state_disability_tax': Decimal(str(last_paystub.ytd_state_disability_tax)) + Decimal(str(current_deductions.get('state_disability_tax', 0))),
            'ytd_local_income_tax': Decimal(str(last_paystub.ytd_local_income_tax)) + Decimal(str(current_deductions.get('local_income_tax', 0))),
            'ytd_retirement_401k': Decimal(str(last_paystub.ytd_retirement_401k)) + Decimal(str(current_deductions.get('retirement_401k', 0))),
            'ytd_health_insurance': Decimal(str(last_paystub.ytd_health_insurance)) + Decimal(str(current_deductions.get('health_insurance', 0))),
            'ytd_dental_insurance': Decimal(str(last_paystub.ytd_dental_insurance)) + Decimal(str(current_deductions.get('dental_insurance', 0))),
            'ytd_vision_insurance': Decimal(str(last_paystub.ytd_vision_insurance)) + Decimal(str(current_deductions.get('vision_insurance', 0))),
            'ytd_hsa_contribution': Decimal(str(last_paystub.ytd_hsa_contribution)) + Decimal(str(current_deductions.get('hsa_contribution', 0))),
            'ytd_ss_wages': Decimal(str(last_paystub.ytd_ss_wages)) + Decimal(str(current_deductions.get('ss_wages', current_gross))),
            'ytd_medicare_wages': Decimal(str(last_paystub.ytd_medicare_wages)) + Decimal(str(current_deductions.get('medicare_wages', current_gross))),
            'paystub_number': last_paystub.paystub_number + 1,
            'previous_paystub_id': last_paystub.id
        }
        
        # Check Social Security wage base limit (2025: $168,600)
        ss_wage_base_limit = Decimal('168600.00')
        ytd_totals['ss_wage_base_reached'] = ytd_totals['ytd_ss_wages'] >= ss_wage_base_limit
        
        # Check Additional Medicare threshold (2025: $200,000 single, $250,000 married)
        additional_medicare_threshold = Decimal('200000.00')
        ytd_totals['additional_medicare_threshold_reached'] = ytd_totals['ytd_medicare_wages'] >= additional_medicare_threshold
        
    else:
        # First paystub of the year - start fresh
        ytd_totals = {
            'ytd_gross_pay': Decimal(str(current_gross)),
            'ytd_net_pay': Decimal(str(current_deductions['net_pay'])),
            'ytd_federal_income_tax': Decimal(str(current_deductions.get('federal_income_tax', 0))),
            'ytd_social_security_tax': Decimal(str(current_deductions.get('social_security_tax', 0))),
            'ytd_medicare_tax': Decimal(str(current_deductions.get('medicare_tax', 0))),
            'ytd_additional_medicare_tax': Decimal(str(current_deductions.get('additional_medicare_tax', 0))),
            'ytd_state_income_tax': Decimal(str(current_deductions.get('state_income_tax', 0))),
            'ytd_state_disability_tax': Decimal(str(current_deductions.get('state_disability_tax', 0))),
            'ytd_local_income_tax': Decimal(str(current_deductions.get('local_income_tax', 0))),
            'ytd_retirement_401k': Decimal(str(current_deductions.get('retirement_401k', 0))),
            'ytd_health_insurance': Decimal(str(current_deductions.get('health_insurance', 0))),
            'ytd_dental_insurance': Decimal(str(current_deductions.get('dental_insurance', 0))),
            'ytd_vision_insurance': Decimal(str(current_deductions.get('vision_insurance', 0))),
            'ytd_hsa_contribution': Decimal(str(current_deductions.get('hsa_contribution', 0))),
            'ytd_ss_wages': Decimal(str(current_deductions.get('ss_wages', current_gross))),
            'ytd_medicare_wages': Decimal(str(current_deductions.get('medicare_wages', current_gross))),
            'paystub_number': 1,
            'ss_wage_base_reached': False,
            'additional_medicare_threshold_reached': False,
            'previous_paystub_id': None
        }
    
    return ytd_totals


def calculate_next_pay_date(last_pay_date, pay_frequency):
    """Calculate the next suggested pay date based on frequency"""
    if not last_pay_date:
        return date.today()
    
    if pay_frequency == 'Weekly':
        return last_pay_date + timedelta(days=7)
    elif pay_frequency == 'BiWeekly':
        return last_pay_date + timedelta(days=14)
    elif pay_frequency == 'SemiMonthly':
        # Semi-monthly is typically 15th and last day of month
        if last_pay_date.day == 15:
            # Next pay date is last day of month
            next_month = last_pay_date.month + 1 if last_pay_date.month < 12 else 1
            next_year = last_pay_date.year if last_pay_date.month < 12 else last_pay_date.year + 1
            return date(next_year, next_month, 1) - timedelta(days=1)
        else:
            # Next pay date is 15th of next month
            next_month = last_pay_date.month + 1 if last_pay_date.month < 12 else 1
            next_year = last_pay_date.year if last_pay_date.month < 12 else last_pay_date.year + 1
            return date(next_year, next_month, 15)
    elif pay_frequency == 'Monthly':
        # Same day next month
        next_month = last_pay_date.month + 1 if last_pay_date.month < 12 else 1
        next_year = last_pay_date.year if last_pay_date.month < 12 else last_pay_date.year + 1
        try:
            return date(next_year, next_month, last_pay_date.day)
        except ValueError:
            # Handle months with fewer days (e.g., Jan 31 -> Feb 28)
            return date(next_year, next_month, 1) + timedelta(days=30)
    
    return last_pay_date + timedelta(days=14)  # Default to biweekly


def calculate_pay_period_dates(pay_date, pay_frequency):
    """Calculate period start and end dates based on pay date and frequency"""
    if pay_frequency == 'Weekly':
        period_end = pay_date - timedelta(days=1)
        period_start = period_end - timedelta(days=6)
    elif pay_frequency == 'BiWeekly':
        period_end = pay_date - timedelta(days=1)
        period_start = period_end - timedelta(days=13)
    elif pay_frequency == 'SemiMonthly':
        if pay_date.day <= 15:
            period_start = date(pay_date.year, pay_date.month, 1)
            period_end = date(pay_date.year, pay_date.month, 15)
        else:
            period_start = date(pay_date.year, pay_date.month, 16)
            # Last day of month
            next_month = pay_date.month + 1 if pay_date.month < 12 else 1
            next_year = pay_date.year if pay_date.month < 12 else pay_date.year + 1
            period_end = date(next_year, next_month, 1) - timedelta(days=1)
    elif pay_frequency == 'Monthly':
        period_start = date(pay_date.year, pay_date.month, 1)
        next_month = pay_date.month + 1 if pay_date.month < 12 else 1
        next_year = pay_date.year if pay_date.month < 12 else pay_date.year + 1
        period_end = date(next_year, next_month, 1) - timedelta(days=1)
    else:
        # Default to biweekly
        period_end = pay_date - timedelta(days=1)
        period_start = period_end - timedelta(days=13)
    
    return period_start, period_end


def calculate_pto_balances(employee, last_paystub, hours_used_this_period):
    """Calculate PTO accrual and balances"""
    # Get accrual rates from employee
    vacation_accrued = float(employee.vacation_accrual_rate) if employee.vacation_accrual_rate else 0.0
    sick_accrued = float(employee.sick_accrual_rate) if employee.sick_accrual_rate else 0.0
    personal_accrued = float(employee.personal_accrual_rate) if employee.personal_accrual_rate else 0.0
    
    # Get previous balances
    if last_paystub:
        vacation_balance = float(last_paystub.vacation_balance) + vacation_accrued - hours_used_this_period.get('vacation', 0)
        sick_balance = float(last_paystub.sick_balance) + sick_accrued - hours_used_this_period.get('sick', 0)
        personal_balance = float(last_paystub.personal_balance) + personal_accrued - hours_used_this_period.get('personal', 0)
    else:
        vacation_balance = vacation_accrued
        sick_balance = sick_accrued
        personal_balance = personal_accrued
    
    return {
        'vacation_accrued_this_period': vacation_accrued,
        'vacation_used_this_period': hours_used_this_period.get('vacation', 0),
        'vacation_balance': vacation_balance,
        'sick_accrued_this_period': sick_accrued,
        'sick_used_this_period': hours_used_this_period.get('sick', 0),
        'sick_balance': sick_balance,
        'personal_accrued_this_period': personal_accrued,
        'personal_used_this_period': hours_used_this_period.get('personal', 0),
        'personal_balance': personal_balance
    }


def update_employee_ytd_cache(employee_id):
    """Update the cached YTD values on the employee record for quick dashboard access"""
    from src.models.database import db
    
    current_year = datetime.now().year
    
    ytd_data = db.session.query(
        func.sum(Paystub.gross_pay).label('ytd_gross'),
        func.sum(Paystub.net_pay).label('ytd_net')
    ).filter(
        Paystub.employee_id == employee_id,
        extract('year', Paystub.pay_date) == current_year,
        Paystub.is_void == False
    ).first()
    
    employee = Employee.query.get(employee_id)
    if employee:
        employee.ytd_gross = ytd_data.ytd_gross if ytd_data.ytd_gross else 0
        employee.ytd_net = ytd_data.ytd_net if ytd_data.ytd_net else 0
        db.session.commit()

