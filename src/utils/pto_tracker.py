"""
PTO Tracking System - Accrual and Balance Calculations
Implements PTO management from deployment guide
"""
from decimal import Decimal
from datetime import datetime
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.models.user import db

class PTOTracker:
    """
    Handle PTO accrual, usage, and balance tracking
    """
    
    # Standard accrual rates (hours per pay period)
    STANDARD_ACCRUAL_RATES = {
        'Weekly': {
            'vacation': Decimal('1.54'),  # ~80 hours/year
            'sick': Decimal('0.77'),      # ~40 hours/year
            'personal': Decimal('0.38')   # ~20 hours/year
        },
        'BiWeekly': {
            'vacation': Decimal('3.08'),  # ~80 hours/year
            'sick': Decimal('1.54'),      # ~40 hours/year
            'personal': Decimal('0.77')   # ~20 hours/year
        },
        'SemiMonthly': {
            'vacation': Decimal('3.33'),  # ~80 hours/year
            'sick': Decimal('1.67'),      # ~40 hours/year
            'personal': Decimal('0.83')   # ~20 hours/year
        },
        'Monthly': {
            'vacation': Decimal('6.67'),  # ~80 hours/year
            'sick': Decimal('3.33'),      # ~40 hours/year
            'personal': Decimal('1.67')   # ~20 hours/year
        }
    }
    
    @staticmethod
    def get_accrual_rate(employee, pto_type):
        """
        Get PTO accrual rate for employee
        """
        # Check if employee has custom accrual rate
        if pto_type == 'vacation' and employee.pto_vacation_accrual_rate:
            return employee.pto_vacation_accrual_rate
        elif pto_type == 'sick' and employee.pto_sick_accrual_rate:
            return employee.pto_sick_accrual_rate
        elif pto_type == 'personal' and employee.pto_personal_accrual_rate:
            return employee.pto_personal_accrual_rate
        
        # Use standard rate based on pay frequency
        pay_frequency = employee.pay_frequency or 'BiWeekly'
        rates = PTOTracker.STANDARD_ACCRUAL_RATES.get(pay_frequency, PTOTracker.STANDARD_ACCRUAL_RATES['BiWeekly'])
        
        return rates.get(pto_type, Decimal('0'))
    
    @staticmethod
    def calculate_accrual(employee, hours_worked=None):
        """
        Calculate PTO accrual for this pay period
        Can be based on hours worked or standard per-period accrual
        """
        # Get accrual rates
        vacation_rate = PTOTracker.get_accrual_rate(employee, 'vacation')
        sick_rate = PTOTracker.get_accrual_rate(employee, 'sick')
        personal_rate = PTOTracker.get_accrual_rate(employee, 'personal')
        
        # If hours-based accrual (optional)
        if hours_worked is not None:
            # Prorate based on full-time hours (40 hours/week)
            full_time_hours = {
                'Weekly': 40,
                'BiWeekly': 80,
                'SemiMonthly': 86.67,
                'Monthly': 173.33
            }
            expected_hours = full_time_hours.get(employee.pay_frequency, 80)
            prorate_factor = min(Decimal(str(hours_worked)) / Decimal(str(expected_hours)), Decimal('1.0'))
            
            vacation_rate = vacation_rate * prorate_factor
            sick_rate = sick_rate * prorate_factor
            personal_rate = personal_rate * prorate_factor
        
        return {
            'vacation': vacation_rate,
            'sick': sick_rate,
            'personal': personal_rate
        }
    
    @staticmethod
    def get_current_balances(employee_id):
        """
        Get current PTO balances from last paystub
        """
        last_paystub = Paystub.query.filter_by(
            employee_id=employee_id,
            is_void=False
        ).order_by(Paystub.paystub_number.desc()).first()
        
        if last_paystub:
            return {
                'vacation': last_paystub.pto_vacation_balance or Decimal('0'),
                'sick': last_paystub.pto_sick_balance or Decimal('0'),
                'personal': last_paystub.pto_personal_balance or Decimal('0')
            }
        else:
            # Get from employee record
            employee = Employee.query.get(employee_id)
            return {
                'vacation': employee.pto_vacation_balance or Decimal('0'),
                'sick': employee.pto_sick_balance or Decimal('0'),
                'personal': employee.pto_personal_balance or Decimal('0')
            }
    
    @staticmethod
    def calculate_new_balances(employee_id, pto_used, hours_worked=None):
        """
        Calculate new PTO balances after accrual and usage
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        # Get current balances
        current = PTOTracker.get_current_balances(employee_id)
        
        # Calculate accrual
        accrual = PTOTracker.calculate_accrual(employee, hours_worked)
        
        # Calculate new balances
        new_balances = {
            'vacation': {
                'previous': current['vacation'],
                'accrued': accrual['vacation'],
                'used': pto_used.get('vacation', Decimal('0')),
                'balance': current['vacation'] + accrual['vacation'] - pto_used.get('vacation', Decimal('0'))
            },
            'sick': {
                'previous': current['sick'],
                'accrued': accrual['sick'],
                'used': pto_used.get('sick', Decimal('0')),
                'balance': current['sick'] + accrual['sick'] - pto_used.get('sick', Decimal('0'))
            },
            'personal': {
                'previous': current['personal'],
                'accrued': accrual['personal'],
                'used': pto_used.get('personal', Decimal('0')),
                'balance': current['personal'] + accrual['personal'] - pto_used.get('personal', Decimal('0'))
            }
        }
        
        # Ensure balances don't go negative
        for pto_type in ['vacation', 'sick', 'personal']:
            if new_balances[pto_type]['balance'] < 0:
                new_balances[pto_type]['balance'] = Decimal('0')
        
        return new_balances
    
    @staticmethod
    def get_ytd_pto_usage(employee_id, current_year=None):
        """
        Get YTD PTO usage for employee
        """
        if current_year is None:
            current_year = datetime.now().year
        
        from sqlalchemy import extract, func
        
        ytd = db.session.query(
            func.sum(Paystub.pto_vacation_used_this_period).label('vacation_used'),
            func.sum(Paystub.pto_sick_used_this_period).label('sick_used'),
            func.sum(Paystub.pto_personal_used_this_period).label('personal_used')
        ).filter(
            Paystub.employee_id == employee_id,
            extract('year', Paystub.pay_date) == current_year,
            Paystub.is_void == False
        ).first()
        
        return {
            'vacation_used': ytd.vacation_used or Decimal('0'),
            'sick_used': ytd.sick_used or Decimal('0'),
            'personal_used': ytd.personal_used or Decimal('0')
        }
    
    @staticmethod
    def format_pto_hours(hours):
        """
        Format PTO hours for display (e.g., "40.5 hours" or "5 days, 0.5 hours")
        """
        if hours is None:
            return "0 hours"
        
        hours = float(hours)
        
        if hours >= 8:
            days = int(hours // 8)
            remaining_hours = hours % 8
            if remaining_hours > 0:
                return f"{days} days, {remaining_hours:.1f} hours"
            else:
                return f"{days} days"
        else:
            return f"{hours:.1f} hours"
    
    @staticmethod
    def get_pto_summary(employee_id):
        """
        Get complete PTO summary for dashboard/reports
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        current_balances = PTOTracker.get_current_balances(employee_id)
        ytd_usage = PTOTracker.get_ytd_pto_usage(employee_id)
        accrual_rates = {
            'vacation': PTOTracker.get_accrual_rate(employee, 'vacation'),
            'sick': PTOTracker.get_accrual_rate(employee, 'sick'),
            'personal': PTOTracker.get_accrual_rate(employee, 'personal')
        }
        
        return {
            'balances': {
                'vacation': {
                    'hours': float(current_balances['vacation']),
                    'formatted': PTOTracker.format_pto_hours(current_balances['vacation'])
                },
                'sick': {
                    'hours': float(current_balances['sick']),
                    'formatted': PTOTracker.format_pto_hours(current_balances['sick'])
                },
                'personal': {
                    'hours': float(current_balances['personal']),
                    'formatted': PTOTracker.format_pto_hours(current_balances['personal'])
                }
            },
            'ytd_usage': {
                'vacation': float(ytd_usage['vacation_used']),
                'sick': float(ytd_usage['sick_used']),
                'personal': float(ytd_usage['personal_used'])
            },
            'accrual_rates': {
                'vacation': float(accrual_rates['vacation']),
                'sick': float(accrual_rates['sick']),
                'personal': float(accrual_rates['personal']),
                'frequency': employee.pay_frequency
            }
        }
    
    @staticmethod
    def update_employee_balances(employee_id, new_balances):
        """
        Update employee PTO balances in database
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return False
        
        employee.pto_vacation_balance = new_balances['vacation']['balance']
        employee.pto_sick_balance = new_balances['sick']['balance']
        employee.pto_personal_balance = new_balances['personal']['balance']
        
        db.session.commit()
        return True

