import datetime
from decimal import Decimal

# Helper function to safely convert to Decimal
def to_decimal(value):
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value))

def calculate_next_ytd(previous_paystub, current_paystub):
    """
    Calculates the Year-to-Date (YTD) totals for a new paystub based on the previous paystub.
    
    :param previous_paystub: The most recent Paystub object (or None if first of year).
    :param current_paystub: The current Paystub object with period values calculated.
    :return: A dictionary of updated YTD values for the current paystub.
    """
    ytd_updates = {}
    
    # Get previous YTD values, defaulting to 0 if no previous paystub exists
    if previous_paystub:
        prev_ytd = {
            'ytd_gross': to_decimal(previous_paystub.ytd_gross),
            'ytd_regular_pay': to_decimal(previous_paystub.ytd_regular_pay),
            'ytd_overtime_pay': to_decimal(previous_paystub.ytd_overtime_pay),
            'ytd_bonus': to_decimal(previous_paystub.ytd_bonus),
            'ytd_commission': to_decimal(previous_paystub.ytd_commission),
            'ytd_tips': to_decimal(previous_paystub.ytd_tips),
            'ytd_federal_income_tax': to_decimal(previous_paystub.ytd_federal_income_tax),
            'ytd_social_security_tax': to_decimal(previous_paystub.ytd_social_security_tax),
            'ytd_medicare_tax': to_decimal(previous_paystub.ytd_medicare_tax),
            'ytd_additional_medicare_tax': to_decimal(previous_paystub.ytd_additional_medicare_tax),
            'ytd_ss_wages': to_decimal(previous_paystub.ytd_ss_wages),
            'ytd_medicare_wages': to_decimal(previous_paystub.ytd_medicare_wages),
            'ytd_state_income_tax': to_decimal(previous_paystub.ytd_state_income_tax),
            'ytd_state_disability_tax': to_decimal(previous_paystub.ytd_state_disability_tax),
            'ytd_state_wages': to_decimal(previous_paystub.ytd_state_wages),
            'ytd_local_income_tax': to_decimal(previous_paystub.ytd_local_income_tax),
            'ytd_local_wages': to_decimal(previous_paystub.ytd_local_wages),
            'ytd_401k': to_decimal(previous_paystub.ytd_401k),
            'ytd_403b': to_decimal(previous_paystub.ytd_403b),
            'ytd_roth_401k': to_decimal(previous_paystub.ytd_roth_401k),
            'ytd_health_insurance': to_decimal(previous_paystub.ytd_health_insurance),
            'ytd_dental_insurance': to_decimal(previous_paystub.ytd_dental_insurance),
            'ytd_vision_insurance': to_decimal(previous_paystub.ytd_vision_insurance),
            'ytd_hsa': to_decimal(previous_paystub.ytd_hsa),
            'ytd_fsa': to_decimal(previous_paystub.ytd_fsa),
            'ytd_child_support': to_decimal(previous_paystub.ytd_child_support),
            'ytd_wage_garnishment': to_decimal(previous_paystub.ytd_wage_garnishment),
            'ytd_tax_levy': to_decimal(previous_paystub.ytd_tax_levy),
            'ytd_total_taxes': to_decimal(previous_paystub.ytd_total_taxes),
            'ytd_total_deductions': to_decimal(previous_paystub.ytd_total_deductions),
            'ytd_total_garnishments': to_decimal(previous_paystub.ytd_total_garnishments),
            'ytd_net_pay': to_decimal(previous_paystub.ytd_net_pay),
            'pto_vacation_ytd_used': to_decimal(previous_paystub.pto_vacation_ytd_used),
            'pto_sick_ytd_used': to_decimal(previous_paystub.pto_sick_ytd_used),
            'pto_personal_ytd_used': to_decimal(previous_paystub.pto_personal_ytd_used),
        }
    else:
        # Default to zero for all YTD fields if no previous paystub exists
        prev_ytd = {field: Decimal('0.00') for field in current_paystub.__table__.columns.keys() if field.startswith('ytd_') or field.startswith('pto_') and 'ytd' in field}
        # Explicitly set the few non-ytd fields that are part of the calculation
        prev_ytd['pto_vacation_ytd_used'] = Decimal('0.00')
        prev_ytd['pto_sick_ytd_used'] = Decimal('0.00')
        prev_ytd['pto_personal_ytd_used'] = Decimal('0.00')
        
    # --- Earnings ---
    ytd_updates['ytd_gross'] = prev_ytd.get('ytd_gross', Decimal('0.00')) + to_decimal(current_paystub.gross_pay)
    ytd_updates['ytd_regular_pay'] = prev_ytd.get('ytd_regular_pay', Decimal('0.00')) + to_decimal(current_paystub.regular_pay)
    ytd_updates['ytd_overtime_pay'] = prev_ytd.get('ytd_overtime_pay', Decimal('0.00')) + to_decimal(current_paystub.overtime_pay)
    ytd_updates['ytd_bonus'] = prev_ytd.get('ytd_bonus', Decimal('0.00')) + to_decimal(current_paystub.bonus)
    ytd_updates['ytd_commission'] = prev_ytd.get('ytd_commission', Decimal('0.00')) + to_decimal(current_paystub.commission)
    ytd_updates['ytd_tips'] = prev_ytd.get('ytd_tips', Decimal('0.00')) + to_decimal(current_paystub.tips)

    # --- Federal Taxes ---
    ytd_updates['ytd_federal_income_tax'] = prev_ytd.get('ytd_federal_income_tax', Decimal('0.00')) + to_decimal(current_paystub.federal_income_tax)
    ytd_updates['ytd_social_security_tax'] = prev_ytd.get('ytd_social_security_tax', Decimal('0.00')) + to_decimal(current_paystub.social_security_tax)
    ytd_updates['ytd_medicare_tax'] = prev_ytd.get('ytd_medicare_tax', Decimal('0.00')) + to_decimal(current_paystub.medicare_tax)
    ytd_updates['ytd_additional_medicare_tax'] = prev_ytd.get('ytd_additional_medicare_tax', Decimal('0.00')) + to_decimal(current_paystub.additional_medicare_tax)
    
    # Wage Bases (YTD wages for tax limits)
    ytd_updates['ytd_ss_wages'] = prev_ytd.get('ytd_ss_wages', Decimal('0.00')) + to_decimal(current_paystub.gross_pay) # Assuming gross is the SS wage base
    ytd_updates['ytd_medicare_wages'] = prev_ytd.get('ytd_medicare_wages', Decimal('0.00')) + to_decimal(current_paystub.gross_pay) # Assuming gross is the Medicare wage base

    # --- State Taxes ---
    ytd_updates['ytd_state_income_tax'] = prev_ytd.get('ytd_state_income_tax', Decimal('0.00')) + to_decimal(current_paystub.state_income_tax)
    ytd_updates['ytd_state_disability_tax'] = prev_ytd.get('ytd_state_disability_tax', Decimal('0.00')) + to_decimal(current_paystub.state_disability_tax)
    ytd_updates['ytd_state_wages'] = prev_ytd.get('ytd_state_wages', Decimal('0.00')) + to_decimal(current_paystub.gross_pay) # Assuming gross is the state wage base

    # --- Local Taxes ---
    ytd_updates['ytd_local_income_tax'] = prev_ytd.get('ytd_local_income_tax', Decimal('0.00')) + to_decimal(current_paystub.local_income_tax)
    ytd_updates['ytd_local_wages'] = prev_ytd.get('ytd_local_wages', Decimal('0.00')) + to_decimal(current_paystub.gross_pay) # Assuming gross is the local wage base

    # --- Deductions ---
    ytd_updates['ytd_401k'] = prev_ytd.get('ytd_401k', Decimal('0.00')) + to_decimal(current_paystub.deduction_401k)
    ytd_updates['ytd_403b'] = prev_ytd.get('ytd_403b', Decimal('0.00')) + to_decimal(current_paystub.deduction_403b)
    ytd_updates['ytd_roth_401k'] = prev_ytd.get('ytd_roth_401k', Decimal('0.00')) + to_decimal(current_paystub.deduction_roth_401k)
    ytd_updates['ytd_health_insurance'] = prev_ytd.get('ytd_health_insurance', Decimal('0.00')) + to_decimal(current_paystub.deduction_health_insurance)
    ytd_updates['ytd_dental_insurance'] = prev_ytd.get('ytd_dental_insurance', Decimal('0.00')) + to_decimal(current_paystub.deduction_dental_insurance)
    ytd_updates['ytd_vision_insurance'] = prev_ytd.get('ytd_vision_insurance', Decimal('0.00')) + to_decimal(current_paystub.deduction_vision_insurance)
    ytd_updates['ytd_hsa'] = prev_ytd.get('ytd_hsa', Decimal('0.00')) + to_decimal(current_paystub.deduction_hsa)
    ytd_updates['ytd_fsa'] = prev_ytd.get('ytd_fsa', Decimal('0.00')) + to_decimal(current_paystub.deduction_fsa)

    # --- Garnishments ---
    ytd_updates['ytd_child_support'] = prev_ytd.get('ytd_child_support', Decimal('0.00')) + to_decimal(current_paystub.garnishment_child_support)
    ytd_updates['ytd_wage_garnishment'] = prev_ytd.get('ytd_wage_garnishment', Decimal('0.00')) + to_decimal(current_paystub.garnishment_wage_garnishment)
    ytd_updates['ytd_tax_levy'] = prev_ytd.get('ytd_tax_levy', Decimal('0.00')) + to_decimal(current_paystub.garnishment_tax_levy)

    # --- Totals ---
    ytd_updates['ytd_total_taxes'] = prev_ytd.get('ytd_total_taxes', Decimal('0.00')) + to_decimal(current_paystub.total_taxes)
    ytd_updates['ytd_total_deductions'] = prev_ytd.get('ytd_total_deductions', Decimal('0.00')) + to_decimal(current_paystub.total_deductions)
    ytd_updates['ytd_total_garnishments'] = prev_ytd.get('ytd_total_garnishments', Decimal('0.00')) + to_decimal(current_paystub.total_garnishments)
    ytd_updates['ytd_net_pay'] = prev_ytd.get('ytd_net_pay', Decimal('0.00')) + to_decimal(current_paystub.net_pay)
    
    # --- PTO Used (YTD) ---
    ytd_updates['pto_vacation_ytd_used'] = prev_ytd.get('pto_vacation_ytd_used', Decimal('0.00')) + to_decimal(current_paystub.pto_vacation_used_this_period)
    ytd_updates['pto_sick_ytd_used'] = prev_ytd.get('pto_sick_ytd_used', Decimal('0.00')) + to_decimal(current_paystub.pto_sick_used_this_period)
    ytd_updates['pto_personal_ytd_used'] = prev_ytd.get('pto_personal_ytd_used', Decimal('0.00')) + to_decimal(current_paystub.pto_personal_used_this_period)


    return ytd_updates


def calculate_pto_balances(employee, paystub, pay_frequency):
    """
    Calculates the new PTO balances for the employee based on accrual and usage in the current paystub.
    
    :param employee: The Employee object with current balances and accrual rates.
    :param paystub: The current Paystub object with usage and accrual for the period.
    :param pay_frequency: The pay frequency string (e.g., 'Biweekly').
    :return: A dictionary of updated PTO balances.
    """
    
    # Get current balances and accrual rates from Employee model
    vacation_balance = to_decimal(employee.pto_vacation_balance)
    sick_balance = to_decimal(employee.pto_sick_balance)
    personal_balance = to_decimal(employee.pto_personal_balance)
    
    vacation_accrual_rate = to_decimal(employee.pto_vacation_accrual_rate)
    sick_accrual_rate = to_decimal(employee.pto_sick_accrual_rate)
    personal_accrual_rate = to_decimal(employee.pto_personal_accrual_rate)
    
    # Get usage from Paystub model (hours used this period)
    vacation_used = to_decimal(paystub.pto_vacation_used_this_period)
    sick_used = to_decimal(paystub.pto_sick_used_this_period)
    personal_used = to_decimal(paystub.pto_personal_used_this_period)
    
    # Simple accrual logic: rate * 1 (assuming rate is already per pay period)
    vacation_accrued = vacation_accrual_rate
    sick_accrued = sick_accrual_rate
    personal_accrued = personal_accrual_rate
    
    # Calculate new balances: Current Balance - Used + Accrued
    new_vacation_balance = vacation_balance - vacation_used + vacation_accrued
    new_sick_balance = sick_balance - sick_used + sick_accrued
    new_personal_balance = personal_balance - personal_used + personal_accrued
    
    # Update Paystub with calculated accrual for audit trail
    paystub.pto_vacation_accrued_this_period = vacation_accrued
    paystub.pto_sick_accrued_this_period = sick_accrued
    paystub.pto_personal_accrued_this_period = personal_accrued
    
    # Update Paystub with final balances
    paystub.pto_vacation_balance = new_vacation_balance
    paystub.pto_sick_balance = new_sick_balance
    paystub.pto_personal_balance = new_personal_balance
    
    return {
        'pto_vacation_balance': new_vacation_balance,
        'pto_sick_balance': new_sick_balance,
        'pto_personal_balance': new_personal_balance,
        'pto_vacation_accrued_this_period': vacation_accrued,
        'pto_sick_accrued_this_period': sick_accrued,
        'pto_personal_accrued_this_period': personal_accrued
    }

# Example Usage (for testing) - Requires mock objects for Employee and Paystub
if __name__ == "__main__":
    from collections import namedtuple

    # Mock Employee and Paystub objects
    MockEmployee = namedtuple('MockEmployee', [
        'pto_vacation_balance', 'pto_sick_balance', 'pto_personal_balance',
        'pto_vacation_accrual_rate', 'pto_sick_accrual_rate', 'pto_personal_accrual_rate'
    ])

    MockPaystub = namedtuple('MockPaystub', [
        # Period values
        'gross_pay', 'regular_pay', 'overtime_pay', 'bonus', 'commission', 'tips',
        'federal_income_tax', 'social_security_tax', 'medicare_tax', 'additional_medicare_tax',
        'state_income_tax', 'state_disability_tax', 'local_income_tax',
        'deduction_401k', 'deduction_403b', 'deduction_roth_401k', 'deduction_health_insurance',
        'deduction_dental_insurance', 'deduction_vision_insurance', 'deduction_hsa', 'deduction_fsa',
        'garnishment_child_support', 'garnishment_wage_garnishment', 'garnishment_tax_levy',
        'total_taxes', 'total_deductions', 'total_garnishments', 'net_pay',
        'pto_vacation_used_this_period', 'pto_sick_used_this_period', 'pto_personal_used_this_period',
        
        # YTD values (for previous paystub)
        'ytd_gross', 'ytd_regular_pay', 'ytd_overtime_pay', 'ytd_bonus', 'ytd_commission', 'ytd_tips',
        'ytd_federal_income_tax', 'ytd_social_security_tax', 'ytd_medicare_tax', 'ytd_additional_medicare_tax',
        'ytd_ss_wages', 'ytd_medicare_wages', 'ytd_state_income_tax', 'ytd_state_disability_tax',
        'ytd_state_wages', 'ytd_local_income_tax', 'ytd_local_wages', 'ytd_401k', 'ytd_403b',
        'ytd_roth_401k', 'ytd_health_insurance', 'ytd_dental_insurance', 'ytd_vision_insurance',
        'ytd_hsa', 'ytd_fsa', 'ytd_child_support', 'ytd_wage_garnishment', 'ytd_tax_levy',
        'ytd_total_taxes', 'ytd_total_deductions', 'ytd_total_garnishments', 'ytd_net_pay',
        'pto_vacation_ytd_used', 'pto_sick_ytd_used', 'pto_personal_ytd_used',
        
        # Accrual/Balance fields (for current paystub to be updated)
        'pto_vacation_accrued_this_period', 'pto_sick_accrued_this_period', 'pto_personal_accrued_this_period',
        'pto_vacation_balance', 'pto_sick_balance', 'pto_personal_balance'
    ])
    
    # Mock Paystub 1 (Previous)
    prev_paystub = MockPaystub(
        # Period values (irrelevant for previous paystub in YTD calculation)
        gross_pay=Decimal('2000.00'), regular_pay=Decimal('2000.00'), overtime_pay=Decimal('0.00'), bonus=Decimal('0.00'), commission=Decimal('0.00'), tips=Decimal('0.00'),
        federal_income_tax=Decimal('200.00'), social_security_tax=Decimal('124.00'), medicare_tax=Decimal('29.00'), additional_medicare_tax=Decimal('0.00'),
        state_income_tax=Decimal('50.00'), state_disability_tax=Decimal('10.00'), local_income_tax=Decimal('5.00'),
        deduction_401k=Decimal('100.00'), deduction_403b=Decimal('0.00'), deduction_roth_401k=Decimal('0.00'), deduction_health_insurance=Decimal('50.00'),
        deduction_dental_insurance=Decimal('10.00'), deduction_vision_insurance=Decimal('0.00'), deduction_hsa=Decimal('0.00'), deduction_fsa=Decimal('0.00'),
        garnishment_child_support=Decimal('0.00'), garnishment_wage_garnishment=Decimal('0.00'), garnishment_tax_levy=Decimal('0.00'),
        total_taxes=Decimal('418.00'), total_deductions=Decimal('160.00'), total_garnishments=Decimal('0.00'), net_pay=Decimal('1422.00'),
        pto_vacation_used_this_period=Decimal('0.00'), pto_sick_used_this_period=Decimal('0.00'), pto_personal_used_this_period=Decimal('0.00'),
        
        # YTD values
        ytd_gross=Decimal('10000.00'), ytd_regular_pay=Decimal('9000.00'), ytd_overtime_pay=Decimal('1000.00'), ytd_bonus=Decimal('0.00'), ytd_commission=Decimal('0.00'), ytd_tips=Decimal('0.00'),
        ytd_federal_income_tax=Decimal('1000.00'), ytd_social_security_tax=Decimal('620.00'), ytd_medicare_tax=Decimal('145.00'), ytd_additional_medicare_tax=Decimal('0.00'),
        ytd_ss_wages=Decimal('10000.00'), ytd_medicare_wages=Decimal('10000.00'), ytd_state_income_tax=Decimal('250.00'), ytd_state_disability_tax=Decimal('50.00'),
        ytd_state_wages=Decimal('10000.00'), ytd_local_income_tax=Decimal('25.00'), ytd_local_wages=Decimal('10000.00'), ytd_401k=Decimal('500.00'), ytd_403b=Decimal('0.00'),
        ytd_roth_401k=Decimal('0.00'), ytd_health_insurance=Decimal('250.00'), ytd_dental_insurance=Decimal('50.00'), ytd_vision_insurance=Decimal('0.00'),
        ytd_hsa=Decimal('0.00'), ytd_fsa=Decimal('0.00'), ytd_child_support=Decimal('0.00'), ytd_wage_garnishment=Decimal('0.00'), ytd_tax_levy=Decimal('0.00'),
        ytd_total_taxes=Decimal('1815.00'), ytd_total_deductions=Decimal('800.00'), ytd_total_garnishments=Decimal('0.00'), ytd_net_pay=Decimal('7385.00'),
        pto_vacation_ytd_used=Decimal('8.00'), pto_sick_ytd_used=Decimal('0.00'), pto_personal_ytd_used=Decimal('0.00'),
        
        # Accrual/Balance fields (irrelevant for previous paystub in YTD calculation)
        pto_vacation_accrued_this_period=Decimal('0.00'), pto_sick_accrued_this_period=Decimal('0.00'), pto_personal_accrued_this_period=Decimal('0.00'),
        pto_vacation_balance=Decimal('40.00'), pto_sick_balance=Decimal('24.00'), pto_personal_balance=Decimal('8.00')
    )
    
    # Mock Paystub 2 (Current period values)
    current_paystub_period = MockPaystub(
        # Period values
        gross_pay=Decimal('2500.00'), regular_pay=Decimal('2500.00'), overtime_pay=Decimal('0.00'), bonus=Decimal('0.00'), commission=Decimal('0.00'), tips=Decimal('0.00'),
        federal_income_tax=Decimal('250.00'), social_security_tax=Decimal('155.00'), medicare_tax=Decimal('36.25'), additional_medicare_tax=Decimal('0.00'),
        state_income_tax=Decimal('60.00'), state_disability_tax=Decimal('12.50'), local_income_tax=Decimal('6.25'),
        deduction_401k=Decimal('125.00'), deduction_403b=Decimal('0.00'), deduction_roth_401k=Decimal('0.00'), deduction_health_insurance=Decimal('50.00'),
        deduction_dental_insurance=Decimal('10.00'), deduction_vision_insurance=Decimal('0.00'), deduction_hsa=Decimal('0.00'), deduction_fsa=Decimal('0.00'),
        garnishment_child_support=Decimal('0.00'), garnishment_wage_garnishment=Decimal('0.00'), garnishment_tax_levy=Decimal('0.00'),
        total_taxes=Decimal('519.75'), total_deductions=Decimal('185.00'), total_garnishments=Decimal('0.00'), net_pay=Decimal('1795.25'),
        pto_vacation_used_this_period=Decimal('4.00'), pto_sick_used_this_period=Decimal('0.00'), pto_personal_used_this_period=Decimal('0.00'),
        
        # YTD values (will be calculated)
        ytd_gross=Decimal('0.00'), ytd_regular_pay=Decimal('0.00'), ytd_overtime_pay=Decimal('0.00'), ytd_bonus=Decimal('0.00'), ytd_commission=Decimal('0.00'), ytd_tips=Decimal('0.00'),
        ytd_federal_income_tax=Decimal('0.00'), ytd_social_security_tax=Decimal('0.00'), ytd_medicare_tax=Decimal('0.00'), ytd_additional_medicare_tax=Decimal('0.00'),
        ytd_ss_wages=Decimal('0.00'), ytd_medicare_wages=Decimal('0.00'), ytd_state_income_tax=Decimal('0.00'), ytd_state_disability_tax=Decimal('0.00'),
        ytd_state_wages=Decimal('0.00'), ytd_local_income_tax=Decimal('0.00'), ytd_local_wages=Decimal('0.00'), ytd_401k=Decimal('0.00'), ytd_403b=Decimal('0.00'),
        ytd_roth_401k=Decimal('0.00'), ytd_health_insurance=Decimal('0.00'), ytd_dental_insurance=Decimal('0.00'), ytd_vision_insurance=Decimal('0.00'),
        ytd_hsa=Decimal('0.00'), ytd_fsa=Decimal('0.00'), ytd_child_support=Decimal('0.00'), ytd_wage_garnishment=Decimal('0.00'), ytd_tax_levy=Decimal('0.00'),
        ytd_total_taxes=Decimal('0.00'), ytd_total_deductions=Decimal('0.00'), ytd_total_garnishments=Decimal('0.00'), ytd_net_pay=Decimal('0.00'),
        pto_vacation_ytd_used=Decimal('0.00'), pto_sick_ytd_used=Decimal('0.00'), pto_personal_ytd_used=Decimal('0.00'),
        
        # Accrual/Balance fields (will be calculated)
        pto_vacation_accrued_this_period=Decimal('0.00'), pto_sick_accrued_this_period=Decimal('0.00'), pto_personal_accrued_this_period=Decimal('0.00'),
        pto_vacation_balance=Decimal('0.00'), pto_sick_balance=Decimal('0.00'), pto_personal_balance=Decimal('0.00')
    )
    
    # Mock Employee
    employee_data = MockEmployee(
        pto_vacation_balance=Decimal('40.00'), pto_sick_balance=Decimal('24.00'), pto_personal_balance=Decimal('8.00'),
        pto_vacation_accrual_rate=Decimal('4.00'), pto_sick_accrual_rate=Decimal('2.00'), pto_personal_accrual_rate=Decimal('0.00')
    )

    print("--- YTD Continuation Test ---")
    next_ytd = calculate_next_ytd(prev_paystub, current_paystub_period)
    print(f"New YTD Gross: ${next_ytd['ytd_gross']:.2f} (Expected: $12500.00)")
    print(f"New YTD Federal Tax: ${next_ytd['ytd_federal_income_tax']:.2f} (Expected: $1250.00)")
    print(f"New YTD SS Wages: ${next_ytd['ytd_ss_wages']:.2f} (Expected: $12500.00)")
    print(f"New YTD Vacation Used: {next_ytd['pto_vacation_ytd_used']:.2f} (Expected: 12.00)")

    print("\n--- PTO Tracking Test ---")
    # Need a mutable object for paystub to test the update
    class MutablePaystub:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def __getattr__(self, name):
            # Fallback for fields not explicitly set in the mock
            return Decimal('0.00')

    mutable_paystub = MutablePaystub(**current_paystub_period._asdict())
    
    pto_updates = calculate_pto_balances(employee_data, mutable_paystub, "Biweekly")
    
    print(f"Vacation Accrued: {pto_updates['pto_vacation_accrued_this_period']:.2f} (Expected: 4.00)")
    print(f"Sick Accrued: {pto_updates['pto_sick_accrued_this_period']:.2f} (Expected: 2.00)")
    print(f"New Vacation Balance: {pto_updates['pto_vacation_balance']:.2f} (Expected: 40.00 - 4.00 + 4.00 = 40.00)")
    print(f"New Sick Balance: {pto_updates['pto_sick_balance']:.2f} (Expected: 24.00 - 0.00 + 2.00 = 26.00)")
    
    # Verify the mutable paystub object was updated
    print(f"Paystub Vacation Balance (Verification): {mutable_paystub.pto_vacation_balance:.2f}")
    print(f"Paystub Sick Balance (Verification): {mutable_paystub.pto_sick_balance:.2f}")
