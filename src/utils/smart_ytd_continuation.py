"""
Smart YTD Continuation Logic - Auto-fill next paystub from previous
Implements all features from deployment guide lines 2700-2900
"""
from datetime import datetime, timedelta
from decimal import Decimal
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.models.user import db
from sqlalchemy import extract, func

class SmartYTDContinuation:
    """
    Handles smart continuation of paystubs with automatic YTD tracking
    """
    
    # 2025 Tax Limits
    SS_WAGE_BASE_2025 = Decimal('176100.00')
    ADDITIONAL_MEDICARE_THRESHOLD = {
        'Single': Decimal('200000.00'),
        'Married': Decimal('250000.00'),
        'Head of Household': Decimal('200000.00')
    }
    
    @staticmethod
    def calculate_next_pay_date(last_pay_date, pay_frequency):
        """
        Calculate next pay date based on frequency
        """
        if not last_pay_date:
            return None
            
        if pay_frequency == 'Weekly':
            return last_pay_date + timedelta(days=7)
        elif pay_frequency == 'BiWeekly':
            return last_pay_date + timedelta(days=14)
        elif pay_frequency == 'SemiMonthly':
            # Semi-monthly: 15th and last day of month
            if last_pay_date.day == 15:
                # Next is last day of month
                next_month = last_pay_date.month
                next_year = last_pay_date.year
                if next_month == 12:
                    next_month = 1
                    next_year += 1
                else:
                    next_month += 1
                # Get last day of month
                from calendar import monthrange
                last_day = monthrange(next_year, next_month)[1]
                return datetime(next_year, next_month, last_day).date()
            else:
                # Next is 15th of next month
                next_month = last_pay_date.month + 1
                next_year = last_pay_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                return datetime(next_year, next_month, 15).date()
        elif pay_frequency == 'Monthly':
            # Same day next month
            next_month = last_pay_date.month + 1
            next_year = last_pay_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            try:
                return datetime(next_year, next_month, last_pay_date.day).date()
            except ValueError:
                # Day doesn't exist in next month (e.g., Jan 31 -> Feb 31)
                from calendar import monthrange
                last_day = monthrange(next_year, next_month)[1]
                return datetime(next_year, next_month, last_day).date()
        
        return None
    
    @staticmethod
    def get_ytd_summary(employee_id, current_year=None):
        """
        Get complete YTD summary for an employee
        """
        if current_year is None:
            current_year = datetime.now().year
        
        ytd = db.session.query(
            func.sum(Paystub.gross_pay).label('ytd_gross'),
            func.sum(Paystub.net_pay).label('ytd_net'),
            func.sum(Paystub.federal_income_tax).label('ytd_federal_tax'),
            func.sum(Paystub.social_security_tax).label('ytd_ss_tax'),
            func.sum(Paystub.medicare_tax).label('ytd_medicare_tax'),
            func.sum(Paystub.additional_medicare_tax).label('ytd_additional_medicare'),
            func.sum(Paystub.state_income_tax).label('ytd_state_tax'),
            func.sum(Paystub.state_disability_tax).label('ytd_sdi'),
            func.sum(Paystub.local_income_tax).label('ytd_local_tax'),
            func.sum(Paystub.deduction_401k).label('ytd_401k'),
            func.sum(Paystub.deduction_health_insurance).label('ytd_health'),
            func.sum(Paystub.ytd_ss_wages).label('ytd_ss_wages'),
            func.sum(Paystub.ytd_medicare_wages).label('ytd_medicare_wages'),
            func.count(Paystub.id).label('paystub_count')
        ).filter(
            Paystub.employee_id == employee_id,
            extract('year', Paystub.pay_date) == current_year,
            Paystub.is_void == False
        ).first()
        
        return {
            'ytd_gross': ytd.ytd_gross or Decimal('0'),
            'ytd_net': ytd.ytd_net or Decimal('0'),
            'ytd_federal_tax': ytd.ytd_federal_tax or Decimal('0'),
            'ytd_ss_tax': ytd.ytd_ss_tax or Decimal('0'),
            'ytd_medicare_tax': ytd.ytd_medicare_tax or Decimal('0'),
            'ytd_additional_medicare': ytd.ytd_additional_medicare or Decimal('0'),
            'ytd_state_tax': ytd.ytd_state_tax or Decimal('0'),
            'ytd_sdi': ytd.ytd_sdi or Decimal('0'),
            'ytd_local_tax': ytd.ytd_local_tax or Decimal('0'),
            'ytd_401k': ytd.ytd_401k or Decimal('0'),
            'ytd_health': ytd.ytd_health or Decimal('0'),
            'ytd_ss_wages': ytd.ytd_ss_wages or Decimal('0'),
            'ytd_medicare_wages': ytd.ytd_medicare_wages or Decimal('0'),
            'paystub_count': ytd.paystub_count or 0
        }
    
    @staticmethod
    def check_ss_wage_base_reached(ytd_ss_wages):
        """
        Check if Social Security wage base has been reached
        """
        return ytd_ss_wages >= SmartYTDContinuation.SS_WAGE_BASE_2025
    
    @staticmethod
    def check_additional_medicare_threshold(ytd_medicare_wages, filing_status):
        """
        Check if Additional Medicare threshold has been reached
        """
        threshold = SmartYTDContinuation.ADDITIONAL_MEDICARE_THRESHOLD.get(
            filing_status, 
            Decimal('200000.00')
        )
        return ytd_medicare_wages >= threshold
    
    @staticmethod
    def calculate_pto_accrual(employee, hours_worked_this_period):
        """
        Calculate PTO accrual for this pay period
        """
        # Get accrual rates from employee
        vacation_rate = employee.pto_vacation_accrual_rate or Decimal('0')
        sick_rate = employee.pto_sick_accrual_rate or Decimal('0')
        personal_rate = employee.pto_personal_accrual_rate or Decimal('0')
        
        # Calculate accrual based on hours worked
        # Typically accrual is per pay period, not per hour
        # But can be prorated if partial period
        
        return {
            'vacation_accrued': vacation_rate,
            'sick_accrued': sick_rate,
            'personal_accrued': personal_rate
        }
    
    @staticmethod
    def update_pto_balances(employee, last_paystub, pto_used_this_period):
        """
        Update PTO balances based on accrual and usage
        """
        # Get current balances
        if last_paystub:
            vacation_balance = last_paystub.pto_vacation_balance or Decimal('0')
            sick_balance = last_paystub.pto_sick_balance or Decimal('0')
            personal_balance = last_paystub.pto_personal_balance or Decimal('0')
        else:
            vacation_balance = employee.pto_vacation_balance or Decimal('0')
            sick_balance = employee.pto_sick_balance or Decimal('0')
            personal_balance = employee.pto_personal_balance or Decimal('0')
        
        # Calculate accrual for this period
        accrual = SmartYTDContinuation.calculate_pto_accrual(employee, 0)
        
        # Update balances
        new_vacation = vacation_balance + accrual['vacation_accrued'] - pto_used_this_period.get('vacation', Decimal('0'))
        new_sick = sick_balance + accrual['sick_accrued'] - pto_used_this_period.get('sick', Decimal('0'))
        new_personal = personal_balance + accrual['personal_accrued'] - pto_used_this_period.get('personal', Decimal('0'))
        
        return {
            'vacation_balance': max(new_vacation, Decimal('0')),
            'sick_balance': max(new_sick, Decimal('0')),
            'personal_balance': max(new_personal, Decimal('0')),
            'vacation_accrued': accrual['vacation_accrued'],
            'sick_accrued': accrual['sick_accrued'],
            'personal_accrued': accrual['personal_accrued']
        }
    
    @staticmethod
    def generate_continuation_data(employee_id):
        """
        Generate complete continuation data for next paystub
        This is the main function that returns all pre-filled data
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        # Get last paystub
        last_paystub = Paystub.query.filter_by(
            employee_id=employee_id,
            is_void=False
        ).order_by(Paystub.paystub_number.desc()).first()
        
        # Get YTD summary
        ytd = SmartYTDContinuation.get_ytd_summary(employee_id)
        
        # Calculate next pay date
        next_pay_date = None
        if last_paystub:
            next_pay_date = SmartYTDContinuation.calculate_next_pay_date(
                last_paystub.pay_date,
                employee.pay_frequency
            )
        
        # Calculate next paystub number
        next_paystub_number = (last_paystub.paystub_number + 1) if last_paystub else 1
        
        # Check tax thresholds
        ss_wage_base_reached = SmartYTDContinuation.check_ss_wage_base_reached(ytd['ytd_ss_wages'])
        additional_medicare_threshold_reached = SmartYTDContinuation.check_additional_medicare_threshold(
            ytd['ytd_medicare_wages'],
            employee.federal_filing_status
        )
        
        # Get PTO balances
        pto_balances = SmartYTDContinuation.update_pto_balances(employee, last_paystub, {})
        
        return {
            'employee': employee.to_dict(),
            'last_paystub': last_paystub.to_dict() if last_paystub else None,
            'ytd_summary': ytd,
            'next_pay_date': next_pay_date.isoformat() if next_pay_date else None,
            'next_paystub_number': next_paystub_number,
            'tax_status': {
                'ss_wage_base_reached': ss_wage_base_reached,
                'additional_medicare_threshold_reached': additional_medicare_threshold_reached,
                'remaining_ss_wages': max(SmartYTDContinuation.SS_WAGE_BASE_2025 - ytd['ytd_ss_wages'], Decimal('0'))
            },
            'pto_balances': pto_balances,
            'suggested_values': {
                'regular_hours': float(last_paystub.regular_hours) if last_paystub else 0,
                'pay_rate': float(employee.pay_rate) if employee.pay_rate else 0,
                'deductions': {
                    '401k': float(last_paystub.deduction_401k) if last_paystub else 0,
                    'health_insurance': float(last_paystub.deduction_health_insurance) if last_paystub else 0
                }
            }
        }

