import datetime
import json

# 2026 Federal Tax Data (from IRS News Release IR-2025-103, Oct. 9, 2025)
FEDERAL_TAX_DATA_2026 = {
    "standard_deductions": {
        "single": 16100,
        "married_filing_jointly": 32200,
        "married_filing_separately": 16100,
        "head_of_household": 24150
    },
    "tax_brackets": {
        "single": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 12400},
            {"rate": 0.22, "threshold": 50400},
            {"rate": 0.24, "threshold": 105700},
            {"rate": 0.32, "threshold": 201775},
            {"rate": 0.35, "threshold": 256225},
            {"rate": 0.37, "threshold": 640600}
        ],
        "married_filing_jointly": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 24800},
            {"rate": 0.22, "threshold": 100800},
            {"rate": 0.24, "threshold": 211400},
            {"rate": 0.32, "threshold": 403550},
            {"rate": 0.35, "threshold": 512450},
            {"rate": 0.37, "threshold": 768700}
        ],
        "married_filing_separately": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 12400},
            {"rate": 0.22, "threshold": 50400},
            {"rate": 0.24, "threshold": 105700},
            {"rate": 0.32, "threshold": 201775},
            {"rate": 0.35, "threshold": 256225},
            {"rate": 0.37, "threshold": 384350} # Half of MFJ for MFS
        ],
        "head_of_household": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 17700},
            {"rate": 0.22, "threshold": 67000},
            {"rate": 0.24, "threshold": 105700},
            {"rate": 0.32, "threshold": 201775},
            {"rate": 0.35, "threshold": 256225},
            {"rate": 0.37, "threshold": 640600} # Same as single for top bracket
        ]
    }
}

# 2025 Federal Tax Data (from 2025ComprehensiveTaxDataforPaystubGenerator.md)
FEDERAL_TAX_DATA_2025 = {
    "standard_deductions": {
        "single": 15000,
        "married_filing_jointly": 30000,
        "married_filing_separately": 15000,
        "head_of_household": 22500,
        "qualifying_widow": 30000
    },
    "tax_brackets": {
        "single": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 11951},
            {"rate": 0.22, "threshold": 48476},
            {"rate": 0.24, "threshold": 103351},
            {"rate": 0.32, "threshold": 197301},
            {"rate": 0.35, "threshold": 250526},
            {"rate": 0.37, "threshold": 626351}
        ],
        "married_filing_jointly": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 23901},
            {"rate": 0.22, "threshold": 96951},
            {"rate": 0.24, "threshold": 206701},
            {"rate": 0.32, "threshold": 394601},
            {"rate": 0.35, "threshold": 501051},
            {"rate": 0.37, "threshold": 751601}
        ],
        "married_filing_separately": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 11951},
            {"rate": 0.22, "threshold": 48476},
            {"rate": 0.24, "threshold": 103351},
            {"rate": 0.32, "threshold": 197301},
            {"rate": 0.35, "threshold": 250526},
            {"rate": 0.37, "threshold": 375801}
        ],
        "head_of_household": [
            {"rate": 0.10, "threshold": 0},
            {"rate": 0.12, "threshold": 17001},
            {"rate": 0.22, "threshold": 64851},
            {"rate": 0.24, "threshold": 103351},
            {"rate": 0.32, "threshold": 197301},
            {"rate": 0.35, "threshold": 250501},
            {"rate": 0.37, "threshold": 626351}
        ]
    }
}

# 2025 Federal Payroll Tax Rates (from 2025ComprehensiveTaxDataforPaystubGenerator.md)
FEDERAL_PAYROLL_TAX_DATA_2025 = {
    "social_security": {
        "employee_rate": 0.062,
        "employer_rate": 0.062,
        "wage_base_limit": 176100
    },
    "medicare": {
        "employee_rate": 0.0145,
        "employer_rate": 0.0145,
        "wage_base_limit": float("inf") # No limit
    },
    "additional_medicare_tax": {
        "rate": 0.009,
        "single_threshold": 200000,
        "mfj_threshold": 250000,
        "mfs_threshold": 125000
    }
}

# 2025 American Samoa Tax Data (from iCalculator™ AS)
AMERICAN_SAMOA_TAX_DATA_2025 = {
    "standard_deductions": {
        "resident_single": 14600,
        "resident_married_filing_jointly": 29200,
        "non_resident_single": 14600, # Same as resident
        "non_resident_married_filing_jointly": 29200 # Same as resident
    },
    "tax_brackets": {
        "resident_single": {
            "federal_tier": [
                {"rate": 0.10, "threshold": 0},
                {"rate": 0.12, "threshold": 11600},
                {"rate": 0.22, "threshold": 47150},
                {"rate": 0.24, "threshold": 100525} # Max threshold for federal tier
            ],
            "as_tier": [
                {"rate": 0.15, "threshold": 0},
                {"rate": 0.18, "threshold": 26250},
                {"rate": 0.31, "threshold": 63550},
                {"rate": 0.36, "threshold": 132600},
                {"rate": 0.396, "threshold": 288350}
            ]
        },
        "resident_married_filing_jointly": {
            "federal_tier": [
                {"rate": 0.10, "threshold": 0},
                {"rate": 0.12, "threshold": 23200},
                {"rate": 0.22, "threshold": 94300},
                {"rate": 0.24, "threshold": 201050} # Max threshold for federal tier
            ],
            "as_tier": [
                {"rate": 0.15, "threshold": 0},
                {"rate": 0.18, "threshold": 43850},
                {"rate": 0.31, "threshold": 105950},
                {"rate": 0.36, "threshold": 161450},
                {"rate": 0.396, "threshold": 288350}
            ]
        }
        # Non-resident brackets would mirror resident, but need to be explicitly defined if used
    },
    "minimum_tax_agi_rate": 0.04,
    "federal_tier_max_income": 100000
}

# 2025 Puerto Rico Tax Data (from PwC Tax Summaries, last reviewed 30 June 2025)
PUERTO_RICO_TAX_DATA_2025 = {
    "personal_exemptions": {
        "individual": 3500,
        "married": 7000
    },
    "tax_brackets": [
        {"rate": 0.00, "threshold": 0},
        {"rate": 0.07, "threshold": 9000},
        {"rate": 0.14, "threshold": 25000},
        {"rate": 0.25, "threshold": 41500},
        {"rate": 0.33, "threshold": 61500}
    ]
    # Note: Puerto Rico has no standard deduction. Other complex taxes (Gradual Adjustment Tax, ABT, Optional Tax for Self-Employed)
    # are not implemented here due to complexity and the agreed-upon revised approach.
}

# 2025 US Territories Mirror-Code Tax Data (from 2025ComprehensiveTaxDataforPaystubGenerator.md)
US_TERRITORIES_MIRROR_CODE_DATA_2025 = {
    "Guam": "mirror_federal",
    "USVI": "mirror_federal",
    "CNMI": "mirror_federal" # CNMI also has local taxes like Wage and Salary Tax (Chapter 2 tax) and Chapter 7 tax (NMTIT) not implemented here.
}

# Load 2025 State Tax Data from JSON
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
state_tax_data_path = os.path.join(current_dir, "extracted_state_tax_data.json")
with open(state_tax_data_path, "r") as f:
    STATE_TAX_DATA_2025 = json.load(f)

ACTIVATION_DATE_2026 = datetime.date(2026, 1, 1)

def get_tax_data(calculation_date, jurisdiction="federal"):
    if jurisdiction == "federal":
        if calculation_date >= ACTIVATION_DATE_2026:
            return FEDERAL_TAX_DATA_2026
        else:
            return FEDERAL_TAX_DATA_2025
    elif jurisdiction == "american_samoa":
        return AMERICAN_SAMOA_TAX_DATA_2025
    elif jurisdiction == "puerto_rico":
        return PUERTO_RICO_TAX_DATA_2025
    elif jurisdiction in US_TERRITORIES_MIRROR_CODE_DATA_2025:
        # For mirror-code territories, use federal tax data
        return get_tax_data(calculation_date, jurisdiction="federal")
    elif jurisdiction in STATE_TAX_DATA_2025:
        return STATE_TAX_DATA_2025[jurisdiction]
    else:
        raise ValueError(f"Tax data not found for jurisdiction: {jurisdiction}")

def calculate_federal_income_tax(income, filing_status, calculation_date=None):
    if calculation_date is None:
        calculation_date = datetime.date.today()

    current_tax_data = get_tax_data(calculation_date, jurisdiction="federal")
    standard_deduction = current_tax_data["standard_deductions"].get(filing_status, 0)
    taxable_income = max(0, income - standard_deduction)

    tax_brackets = current_tax_data["tax_brackets"].get(filing_status)
    if not tax_brackets:
        raise ValueError(f"Federal tax brackets not found for filing status: {filing_status}")

    total_tax = 0
    for i in range(len(tax_brackets)):
        bracket = tax_brackets[i]
        next_threshold = tax_brackets[i+1]["threshold"] if i + 1 < len(tax_brackets) else float("inf")

        if taxable_income > bracket["threshold"]:
            income_in_bracket = min(taxable_income, next_threshold) - bracket["threshold"]
            total_tax += income_in_bracket * bracket["rate"]
        else:
            break

    return total_tax

def calculate_federal_payroll_taxes(gross_income, filing_status, year=2025):
    if year != 2025: # Only 2025 data is available for now
        raise ValueError("Only 2025 federal payroll tax data is currently available.")

    payroll_data = FEDERAL_PAYROLL_TAX_DATA_2025

    # Social Security (OASDI)
    social_security_tax = 0
    if gross_income > 0:
        ss_taxable_income = min(gross_income, payroll_data["social_security"]["wage_base_limit"])
        social_security_tax = ss_taxable_income * payroll_data["social_security"]["employee_rate"]

    # Medicare (HI)
    medicare_tax = gross_income * payroll_data["medicare"]["employee_rate"]

    # Additional Medicare Tax
    additional_medicare_tax = 0
    threshold = 0
    if filing_status == "single" or filing_status == "head_of_household":
        threshold = payroll_data["additional_medicare_tax"]["single_threshold"]
    elif filing_status == "married_filing_jointly" or filing_status == "qualifying_widow":
        threshold = payroll_data["additional_medicare_tax"]["mfj_threshold"]
    elif filing_status == "married_filing_separately":
        threshold = payroll_data["additional_medicare_tax"]["mfs_threshold"]

    if gross_income > threshold:
        additional_medicare_tax = (gross_income - threshold) * payroll_data["additional_medicare_tax"]["rate"]

    return {
        "social_security": social_security_tax,
        "medicare": medicare_tax,
        "additional_medicare": additional_medicare_tax,
        "total_payroll_tax": social_security_tax + medicare_tax + additional_medicare_tax
    }


def calculate_american_samoa_income_tax(gross_income, filing_status, calculation_date=None):
    if calculation_date is None:
        calculation_date = datetime.date.today()

    as_tax_data = get_tax_data(calculation_date, jurisdiction="american_samoa")

    # Determine filing status key for AS data
    as_filing_status = "resident_single" if filing_status == "single" else "resident_married_filing_jointly"

    standard_deduction = as_tax_data["standard_deductions"].get(as_filing_status, 0)
    taxable_income = max(0, gross_income - standard_deduction)

    total_tax = 0
    if taxable_income <= as_tax_data["federal_tier_max_income"]:
        # Use Federal Tier brackets
        tax_brackets = as_tax_data["tax_brackets"][as_filing_status]["federal_tier"]
        for i in range(len(tax_brackets)):
            bracket = tax_brackets[i]
            next_threshold = tax_brackets[i+1]["threshold"] if i + 1 < len(tax_brackets) else float("inf")

            if taxable_income > bracket["threshold"]:
                income_in_bracket = min(taxable_income, next_threshold) - bracket["threshold"]
                total_tax += income_in_bracket * bracket["rate"]
            else:
                break
    else:
        # First, calculate tax up to federal_tier_max_income using federal tier
        federal_tier_taxable_income = as_tax_data["federal_tier_max_income"]
        federal_tier_brackets = as_tax_data["tax_brackets"][as_filing_status]["federal_tier"]
        federal_tier_tax_portion = 0
        for i in range(len(federal_tier_brackets)):
            bracket = federal_tier_brackets[i]
            next_threshold = federal_tier_brackets[i+1]["threshold"] if i + 1 < len(federal_tier_brackets) else float("inf")

            if federal_tier_taxable_income > bracket["threshold"]:
                income_in_bracket = min(federal_tier_taxable_income, next_threshold) - bracket["threshold"]
                federal_tier_tax_portion += income_in_bracket * bracket["rate"]
            else:
                break
        total_tax += federal_tier_tax_portion

        # Then, calculate tax for income above federal_tier_max_income using AS tier
        as_tier_taxable_income = taxable_income - as_tax_data["federal_tier_max_income"]
        as_tier_brackets = as_tax_data["tax_brackets"][as_filing_status]["as_tier"]
        for i in range(len(as_tier_brackets)):
            bracket = as_tier_brackets[i]
            next_threshold = as_tier_brackets[i+1]["threshold"] if i + 1 < len(as_tier_brackets) else float("inf")

            if as_tier_taxable_income > bracket["threshold"]:
                income_in_bracket = min(as_tier_taxable_income, next_threshold) - bracket["threshold"]
                total_tax += income_in_bracket * bracket["rate"]
            else:
                break

    # Apply minimum taxation (4% of AGI)
    minimum_tax = gross_income * as_tax_data["minimum_tax_agi_rate"]
    return max(total_tax, minimum_tax)

def calculate_puerto_rico_income_tax(gross_income, filing_status, dependents=0, calculation_date=None):
    if calculation_date is None:
        calculation_date = datetime.date.today()

    pr_tax_data = get_tax_data(calculation_date, jurisdiction="puerto_rico")

    # Calculate personal exemptions
    personal_exemption = pr_tax_data["personal_exemptions"].get("individual", 0) * (1 + dependents) # Assuming individual exemption applies per dependent
    if filing_status == "married_filing_jointly":
        personal_exemption = pr_tax_data["personal_exemptions"].get("married", 0)

    taxable_income = max(0, gross_income - personal_exemption)

    tax_brackets = pr_tax_data["tax_brackets"]
    if not tax_brackets:
        raise ValueError("Puerto Rico tax brackets not found.")

    total_tax = 0
    for i in range(len(tax_brackets)):
        bracket = tax_brackets[i]
        next_threshold = tax_brackets[i+1]["threshold"] if i + 1 < len(tax_brackets) else float("inf")

        if taxable_income > bracket["threshold"]:
            if bracket["rate"] > 0:
                income_in_bracket = min(taxable_income, next_threshold) - bracket["threshold"]
                total_tax += income_in_bracket * bracket["rate"]
        else:
            break

    return total_tax

def calculate_state_income_tax(income, filing_status, state, calculation_date=None):
    if calculation_date is None:
        calculation_date = datetime.date.today()

    state_tax_data = get_tax_data(calculation_date, jurisdiction=state)

    # Handle states with no income tax
    if not state_tax_data["tax_brackets"]["single"] and not state_tax_data["tax_brackets"]["married_filing_jointly"]:
        return 0

    # Determine filing status key for state data
    state_filing_status = "single" if filing_status == "single" else "married_filing_jointly"

    standard_deduction = state_tax_data["standard_deductions"].get(state_filing_status, 0)
    personal_exemption = state_tax_data["personal_exemptions"].get(state_filing_status, 0)

    # Handle credits vs. deductions for personal exemptions
    tax_credit = 0
    if isinstance(personal_exemption, str) and "credit" in personal_exemption:
        tax_credit = int(personal_exemption.replace("credit", "").strip())
        personal_exemption = 0

    taxable_income = max(0, income - (standard_deduction or 0) - (personal_exemption or 0))

    tax_brackets = state_tax_data["tax_brackets"].get(state_filing_status)
    if not tax_brackets:
        # If specific filing status brackets are not available, try single as a fallback
        tax_brackets = state_tax_data["tax_brackets"].get("single")
        if not tax_brackets:
            raise ValueError(f"Tax brackets not found for state: {state} and filing status: {filing_status}")

    total_tax = 0
    for i in range(len(tax_brackets)):
        bracket = tax_brackets[i]
        next_threshold = tax_brackets[i+1]["threshold"] if i + 1 < len(tax_brackets) else float("inf")

        if taxable_income > bracket["threshold"]:
            income_in_bracket = min(taxable_income, next_threshold) - bracket["threshold"]
            total_tax += income_in_bracket * bracket["rate"]
        else:
            break

    return max(0, total_tax - tax_credit)

# Example Usage (for testing)
if __name__ == "__main__":
    # Test Federal Tax Calculation
    income_2025_fed = 60000
    filing_status_2025_fed = "single"
    tax_2025_fed = calculate_federal_income_tax(income_2025_fed, filing_status_2025_fed, datetime.date(2025, 12, 31))
    print(f"2025 Federal Income Tax for {filing_status_2025_fed} with income ${income_2025_fed}: ${tax_2025_fed:.2f}")

    income_2026_fed = 60000
    filing_status_2026_fed = "single"
    tax_2026_fed = calculate_federal_income_tax(income_2026_fed, filing_status_2026_fed, datetime.date(2026, 1, 1))
    print(f"2026 Federal Income Tax for {filing_status_2026_fed} with income ${income_2026_fed}: ${tax_2026_fed:.2f}")

    income_mfj_fed = 150000
    filing_status_mfj_fed = "married_filing_jointly"
    tax_mfj_fed = calculate_federal_income_tax(income_mfj_fed, filing_status_mfj_fed, datetime.date(2026, 3, 15))
    print(f"2026 Federal Income Tax for {filing_status_mfj_fed} with income ${income_mfj_fed}: ${tax_mfj_fed:.2f}")

    print("\n--- Federal Payroll Tax Calculation ---")
    payroll_income = 180000
    payroll_filing_status = "single"
    payroll_taxes = calculate_federal_payroll_taxes(payroll_income, payroll_filing_status, year=2025)
    print(f"2025 Federal Payroll Taxes for income ${payroll_income} ({payroll_filing_status}):")
    print(f"  Social Security: ${payroll_taxes['social_security']:.2f}")
    print(f"  Medicare: ${payroll_taxes['medicare']:.2f}")
    print(f"  Additional Medicare: ${payroll_taxes['additional_medicare']:.2f}")
    print(f"  Total Payroll Tax: ${payroll_taxes['total_payroll_tax']:.2f}")

    print("\n--- American Samoa Tax Calculation ---")
    # Test American Samoa Tax Calculation
    as_income_low = 50000
    as_filing_status = "single"
    as_tax_low = calculate_american_samoa_income_tax(as_income_low, as_filing_status, datetime.date(2025, 6, 1))
    print(f"AS Tax for {as_filing_status} with income ${as_income_low}: ${as_tax_low:.2f}")

    as_income_high = 150000
    as_tax_high = calculate_american_samoa_income_tax(as_income_high, as_filing_status, datetime.date(2025, 6, 1))
    print(f"AS Tax for {as_filing_status} with income ${as_income_high}: ${as_tax_high:.2f}")

    as_income_min_tax = 10000 # AGI
    as_tax_min_tax = calculate_american_samoa_income_tax(as_income_min_tax, as_filing_status, datetime.date(2025, 6, 1))
    print(f"AS Tax for {as_filing_status} with income ${as_income_min_tax} (min tax check): ${as_tax_min_tax:.2f}")

    print("\n--- Puerto Rico Tax Calculation ---")
    # Test Puerto Rico Tax Calculation
    pr_income_single = 30000
    pr_tax_single = calculate_puerto_rico_income_tax(pr_income_single, "single", calculation_date=datetime.date(2025, 6, 1))
    print(f"PR Tax for single with income ${pr_income_single}: ${pr_tax_single:.2f}")

    pr_income_married = 70000
    pr_tax_married = calculate_puerto_rico_income_tax(pr_income_married, "married_filing_jointly", calculation_date=datetime.date(2025, 6, 1))
    print(f"PR Tax for married filing jointly with income ${pr_income_married}: ${pr_tax_married:.2f}")

    pr_income_single_with_dependents = 50000
    pr_tax_single_with_dependents = calculate_puerto_rico_income_tax(pr_income_single_with_dependents, "single", dependents=2, calculation_date=datetime.date(2025, 6, 1))
    print(f"PR Tax for single with income ${pr_income_single_with_dependents} and 2 dependents: ${pr_tax_single_with_dependents:.2f}")

    print("\n--- State Tax Calculation (Example: California) ---")
    # Test State Tax Calculation
    state_income = 80000
    state_filing_status = "single"
    state = "Calif"
    state_tax = calculate_state_income_tax(state_income, state_filing_status, state, datetime.date(2025, 6, 1))
    print(f"2025 {state} Tax for {state_filing_status} with income ${state_income}: ${state_tax:.2f}")

    print("\n--- State Tax Calculation (Example: Washington - no income tax) ---")
    state_income_no_tax = 100000
    state_filing_status_no_tax = "single"
    state_no_tax = "Wash"
    state_tax_no_tax = calculate_state_income_tax(state_income_no_tax, state_filing_status_no_tax, state_no_tax, datetime.date(2025, 6, 1))
    print(f"2025 {state_no_tax} Tax for {state_filing_status_no_tax} with income ${state_income_no_tax}: ${state_tax_no_tax:.2f}")

    print("\n--- USVI Tax Calculation (Mirror Federal) ---")
    usvi_income = 70000
    usvi_filing_status = "married_filing_jointly"
    usvi_tax = calculate_federal_income_tax(usvi_income, usvi_filing_status, datetime.date(2025, 6, 1))
    print(f"2025 USVI Tax (mirror federal) for {usvi_filing_status} with income ${usvi_income}: ${usvi_tax:.2f}")

