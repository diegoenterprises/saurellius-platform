"""
Complete Employee Model - All 61 Fields from Deployment Guide
"""
from src.models.database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Employee(db.Model):
    __tablename__ = 'employees'
    
    # Primary identification
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    ssn_encrypted = db.Column(db.Text, nullable=False)  # Encrypted SSN
    ssn_last_four = db.Column(db.String(4), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    employee_id = db.Column(db.String(50))  # Company employee ID
    
    # Contact Information
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # Address Information
    address_street = db.Column(db.String(255))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2))
    address_zip = db.Column(db.String(10))
    address_county = db.Column(db.String(100))
    
    # Work Location (if different from residence)
    work_state = db.Column(db.String(2))
    work_city = db.Column(db.String(100))
    work_county = db.Column(db.String(100))
    local_jurisdiction_code = db.Column(db.String(20))  # For local taxes
    local_resident = db.Column(db.Boolean, default=True)
    local_work_location = db.Column(db.String(100))
    
    # Employment Details
    employment_type = db.Column(db.String(50))  # W2, 1099, Self-Employed
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Compensation
    pay_frequency = db.Column(db.String(20))  # Weekly, BiWeekly, SemiMonthly, Monthly
    pay_rate = db.Column(db.Numeric(10, 2))
    pay_rate_type = db.Column(db.String(20))  # Hourly, Salary, Commission
    annual_salary = db.Column(db.Numeric(12, 2))
    
    # Federal Tax Information
    federal_filing_status = db.Column(db.String(50))  # Single, Married, Head of Household
    federal_allowances = db.Column(db.Integer, default=0)
    federal_extra_withholding = db.Column(db.Numeric(10, 2), default=0)
    w4_year = db.Column(db.Integer)  # Year of W-4 form
    w4_step2_checkbox = db.Column(db.Boolean, default=False)  # Multiple jobs
    w4_dependents_amount = db.Column(db.Numeric(10, 2), default=0)
    w4_other_income = db.Column(db.Numeric(10, 2), default=0)
    w4_deductions = db.Column(db.Numeric(10, 2), default=0)
    
    # State Tax Information
    state_filing_status = db.Column(db.String(50))
    state_allowances = db.Column(db.Integer, default=0)
    state_extra_withholding = db.Column(db.Numeric(10, 2), default=0)
    state_exempt = db.Column(db.Boolean, default=False)
    
    # Pre-Tax Deductions
    deduction_401k_percent = db.Column(db.Numeric(5, 2), default=0)
    deduction_401k_fixed = db.Column(db.Numeric(10, 2), default=0)
    deduction_health_insurance = db.Column(db.Numeric(10, 2), default=0)
    deduction_dental_insurance = db.Column(db.Numeric(10, 2), default=0)
    deduction_vision_insurance = db.Column(db.Numeric(10, 2), default=0)
    deduction_hsa = db.Column(db.Numeric(10, 2), default=0)
    deduction_fsa = db.Column(db.Numeric(10, 2), default=0)
    
    # Post-Tax Deductions
    deduction_roth_401k_percent = db.Column(db.Numeric(5, 2), default=0)
    deduction_roth_401k_fixed = db.Column(db.Numeric(10, 2), default=0)
    deduction_life_insurance = db.Column(db.Numeric(10, 2), default=0)
    deduction_disability_insurance = db.Column(db.Numeric(10, 2), default=0)
    
    # Garnishments
    garnishment_child_support = db.Column(db.Numeric(10, 2), default=0)
    garnishment_child_support_percent = db.Column(db.Numeric(5, 2), default=0)
    garnishment_wage_garnishment = db.Column(db.Numeric(10, 2), default=0)
    garnishment_tax_levy = db.Column(db.Numeric(10, 2), default=0)
    garnishment_student_loan = db.Column(db.Numeric(10, 2), default=0)
    
    # PTO Accrual Rates (hours per pay period)
    pto_vacation_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    pto_vacation_balance = db.Column(db.Numeric(8, 4), default=0)

    pto_sick_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    pto_sick_balance = db.Column(db.Numeric(8, 4), default=0)
    pto_personal_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    pto_personal_balance = db.Column(db.Numeric(8, 4), default=0)

    
    # Union Information
    union_member = db.Column(db.Boolean, default=False)
    union_name = db.Column(db.String(200))
    union_dues = db.Column(db.Numeric(10, 2), default=0)
    union_local_number = db.Column(db.String(50))
    
    # Payment Method
    payment_method = db.Column(db.String(50))  # Direct Deposit, Check, Cash
    bank_name = db.Column(db.String(100))
    bank_account_type = db.Column(db.String(20))  # Checking, Savings
    bank_routing_number = db.Column(db.String(9))
    bank_account_number_encrypted = db.Column(db.Text)
    bank_account_last_four = db.Column(db.String(4))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    custom_fields = db.Column(JSONB)  # For additional custom data
    
    # Relationships
    paystubs = db.relationship('Paystub', backref='employee', lazy='dynamic')
    
    def __repr__(self):
        return f'<Employee {self.first_name} {self.last_name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': f"{self.first_name} {self.last_name}",
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'ssn_last_four': self.ssn_last_four,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'employee_id': self.employee_id,
            'email': self.email,
            'phone': self.phone,
            'address': {
                'street': self.address_street,
                'city': self.address_city,
                'state': self.address_state,
                'zip': self.address_zip,
                'county': self.address_county
            },
            'work_location': {
                'state': self.work_state,
                'city': self.work_city,
                'county': self.work_county,
                'local_jurisdiction': self.local_jurisdiction_code
            },
            'employment': {
                'type': self.employment_type,
                'job_title': self.job_title,
                'department': self.department,
                'hire_date': self.hire_date.isoformat() if self.hire_date else None,
                'is_active': self.is_active
            },
            'compensation': {
                'pay_frequency': self.pay_frequency,
                'pay_rate': float(self.pay_rate) if self.pay_rate else 0,
                'pay_rate_type': self.pay_rate_type,
                'annual_salary': float(self.annual_salary) if self.annual_salary else 0
            },
            'tax_info': {
                'federal_filing_status': self.federal_filing_status,
                'federal_allowances': self.federal_allowances,
                'state_filing_status': self.state_filing_status,
                'state_allowances': self.state_allowances
            },
            'pto': {
                'vacation_balance': float(self.pto_vacation_balance) if self.pto_vacation_balance else 0,
                'sick_balance': float(self.pto_sick_balance) if self.pto_sick_balance else 0,
                'personal_balance': float(self.pto_personal_balance) if self.pto_personal_balance else 0
            },
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

