from src.models.database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import CheckConstraint

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(__import__('uuid').uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    profile_picture_url = db.Column(db.Text)
    
    # Subscription
    subscription_tier = db.Column(db.String(50), default='starter')
    subscription_status = db.Column(db.String(50), default='active')
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(255), unique=True, index=True)
    stripe_subscription_id = db.Column(db.String(255))
    
    # Rewards
    reward_points = db.Column(db.Integer, default=0)
    reward_tier = db.Column(db.String(50), default='bronze')
    total_lifetime_points = db.Column(db.Integer, default=0)
    
    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.Text)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.Text)
    password_reset_token = db.Column(db.Text)
    password_reset_expires = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    login_streak = db.Column(db.Integer, default=0)
    last_login_streak_date = db.Column(db.Date)
    lifetime_paystubs_generated = db.Column(db.Integer, default=0)
    
    # Relationships
    companies = relationship("Company", back_populates="user", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="user", cascade="all, delete-orphan")
    paystubs = relationship("Paystub", back_populates="user", cascade="all, delete-orphan")
    rewards = relationship("RewardActivity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'reward_points': self.reward_points,
            'reward_tier': self.reward_tier,
            'total_lifetime_points': self.total_lifetime_points,
            'lifetime_paystubs_generated': self.lifetime_paystubs_generated,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Company Info
    legal_name = db.Column(db.String(255), nullable=False)
    dba_name = db.Column(db.String(255))
    ein = db.Column(db.String(10), nullable=False, index=True)
    state_tax_id = db.Column(db.String(50))
    
    # Address
    address_street = db.Column(db.String(255))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2))
    address_zip = db.Column(db.String(10))
    
    # Contact
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    
    # Business Details
    industry_type = db.Column(db.String(100))
    business_structure = db.Column(db.String(50))
    
    # Branding
    company_logo_url = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="companies")
    employees = relationship("Employee", back_populates="company", cascade="all, delete-orphan")
    paystubs = relationship("Paystub", back_populates="company", cascade="all, delete-orphan")


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(__import__('uuid').uuid4()))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Personal Info
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    ssn_encrypted = db.Column(db.Text, nullable=False)
    ssn_last_four = db.Column(db.String(4), nullable=False)
    date_of_birth = db.Column(db.Date)
    employee_id = db.Column(db.String(50))
    hire_date = db.Column(db.Date)
    
    # Contact
    address_street = db.Column(db.String(255))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2), nullable=False, index=True)
    address_zip = db.Column(db.String(10))
    address_county = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # Tax Filing Status
    federal_filing_status = db.Column(db.String(50), nullable=False)
    federal_allowances = db.Column(db.Integer, default=0)
    federal_additional_withholding = db.Column(db.Numeric(10, 2), default=0)
    federal_extra_withholding_per_pay = db.Column(db.Numeric(10, 2), default=0)
    federal_w4_year = db.Column(db.Integer)
    
    state_filing_status = db.Column(db.String(50))
    state_allowances = db.Column(db.Integer, default=0)
    state_additional_withholding = db.Column(db.Numeric(10, 2), default=0)
    
    # Local Tax
    local_jurisdiction_code = db.Column(db.String(50))
    local_resident = db.Column(db.Boolean, default=True)
    local_work_location = db.Column(db.String(100))
    
    # Employment Classification
    employment_type = db.Column(db.String(50), nullable=False)
    pay_structure = db.Column(db.String(50), nullable=False)
    exempt_from_overtime = db.Column(db.Boolean, default=False)
    
    # Compensation
    hourly_rate = db.Column(db.Numeric(10, 2))
    overtime_rate = db.Column(db.Numeric(10, 2))
    double_time_rate = db.Column(db.Numeric(10, 2))
    annual_salary = db.Column(db.Numeric(12, 2))
    pay_frequency = db.Column(db.String(20), nullable=False)
    
    # PTO Accrual Rates
    vacation_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    sick_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    personal_accrual_rate = db.Column(db.Numeric(8, 4), default=0)
    
    # Deduction Elections
    retirement_401k_percent = db.Column(db.Numeric(5, 2), default=0)
    retirement_401k_flat_amount = db.Column(db.Numeric(10, 2), default=0)
    retirement_type = db.Column(db.String(50))
    
    health_insurance_employee_cost = db.Column(db.Numeric(10, 2), default=0)
    dental_insurance_employee_cost = db.Column(db.Numeric(10, 2), default=0)
    vision_insurance_employee_cost = db.Column(db.Numeric(10, 2), default=0)
    
    hsa_contribution_per_pay = db.Column(db.Numeric(10, 2), default=0)
    fsa_contribution_per_pay = db.Column(db.Numeric(10, 2), default=0)
    
    life_insurance_employee_cost = db.Column(db.Numeric(10, 2), default=0)
    disability_insurance_employee_cost = db.Column(db.Numeric(10, 2), default=0)
    
    # Garnishments
    child_support_amount = db.Column(db.Numeric(10, 2), default=0)
    child_support_percentage = db.Column(db.Numeric(5, 2), default=0)
    wage_garnishment_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_levy_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Union
    union_member = db.Column(db.Boolean, default=False)
    union_dues_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    termination_date = db.Column(db.Date)
    termination_reason = db.Column(db.Text)
    
    # YTD Tracking (cached for quick dashboard access)
    ytd_gross = db.Column(db.Numeric(12, 2), default=0)
    ytd_net = db.Column(db.Numeric(12, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="employees")
    company = relationship("Company", back_populates="employees")
    paystubs = relationship("Paystub", back_populates="employee", cascade="all, delete-orphan")
    
    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class Paystub(db.Model):
    __tablename__ = 'paystubs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(__import__('uuid').uuid4()))
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Pay Period Info
    period_start_date = db.Column(db.Date, nullable=False)
    period_end_date = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date, nullable=False, index=True)
    check_number = db.Column(db.String(50))
    paystub_number = db.Column(db.Integer, nullable=False)
    pay_frequency = db.Column(db.String(20), nullable=False)
    
    # Hours
    regular_hours = db.Column(db.Numeric(8, 2), default=0)
    overtime_hours = db.Column(db.Numeric(8, 2), default=0)
    double_time_hours = db.Column(db.Numeric(8, 2), default=0)
    sick_hours = db.Column(db.Numeric(8, 2), default=0)
    vacation_hours = db.Column(db.Numeric(8, 2), default=0)
    holiday_hours = db.Column(db.Numeric(8, 2), default=0)
    personal_hours = db.Column(db.Numeric(8, 2), default=0)
    unpaid_hours = db.Column(db.Numeric(8, 2), default=0)
    
    # Current Period Earnings
    regular_earnings = db.Column(db.Numeric(10, 2), default=0)
    overtime_earnings = db.Column(db.Numeric(10, 2), default=0)
    double_time_earnings = db.Column(db.Numeric(10, 2), default=0)
    bonus = db.Column(db.Numeric(10, 2), default=0)
    commission = db.Column(db.Numeric(10, 2), default=0)
    tips = db.Column(db.Numeric(10, 2), default=0)
    shift_differential = db.Column(db.Numeric(10, 2), default=0)
    holiday_pay = db.Column(db.Numeric(10, 2), default=0)
    sick_pay = db.Column(db.Numeric(10, 2), default=0)
    vacation_pay = db.Column(db.Numeric(10, 2), default=0)
    severance_pay = db.Column(db.Numeric(10, 2), default=0)
    reimbursements_taxable = db.Column(db.Numeric(10, 2), default=0)
    reimbursements_nontaxable = db.Column(db.Numeric(10, 2), default=0)
    other_earnings = db.Column(db.Numeric(10, 2), default=0)
    gross_pay = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Current Period Federal Tax Withholdings
    federal_income_tax = db.Column(db.Numeric(10, 2), default=0)
    social_security_tax = db.Column(db.Numeric(10, 2), default=0)
    medicare_tax = db.Column(db.Numeric(10, 2), default=0)
    additional_medicare_tax = db.Column(db.Numeric(10, 2), default=0)
    
    # Current Period State/Local Tax Withholdings
    state_income_tax = db.Column(db.Numeric(10, 2), default=0)
    state_disability_tax = db.Column(db.Numeric(10, 2), default=0)
    state_unemployment_employee = db.Column(db.Numeric(10, 2), default=0)
    local_income_tax = db.Column(db.Numeric(10, 2), default=0)
    local_jurisdiction = db.Column(db.String(100))
    
    # Current Period Pre-Tax Deductions
    retirement_401k = db.Column(db.Numeric(10, 2), default=0)
    retirement_403b = db.Column(db.Numeric(10, 2), default=0)
    retirement_ira = db.Column(db.Numeric(10, 2), default=0)
    health_insurance = db.Column(db.Numeric(10, 2), default=0)
    dental_insurance = db.Column(db.Numeric(10, 2), default=0)
    vision_insurance = db.Column(db.Numeric(10, 2), default=0)
    hsa_contribution = db.Column(db.Numeric(10, 2), default=0)
    fsa_contribution = db.Column(db.Numeric(10, 2), default=0)
    dependent_care_fsa = db.Column(db.Numeric(10, 2), default=0)
    commuter_benefits = db.Column(db.Numeric(10, 2), default=0)
    
    # Current Period Post-Tax Deductions
    life_insurance = db.Column(db.Numeric(10, 2), default=0)
    disability_insurance = db.Column(db.Numeric(10, 2), default=0)
    roth_401k = db.Column(db.Numeric(10, 2), default=0)
    union_dues = db.Column(db.Numeric(10, 2), default=0)
    charitable_contributions = db.Column(db.Numeric(10, 2), default=0)
    loan_repayments = db.Column(db.Numeric(10, 2), default=0)
    
    # Garnishments
    child_support = db.Column(db.Numeric(10, 2), default=0)
    spousal_support = db.Column(db.Numeric(10, 2), default=0)
    tax_levy = db.Column(db.Numeric(10, 2), default=0)
    wage_garnishment = db.Column(db.Numeric(10, 2), default=0)
    student_loan_garnishment = db.Column(db.Numeric(10, 2), default=0)
    other_garnishments = db.Column(db.Numeric(10, 2), default=0)
    
    # Net Pay
    net_pay = db.Column(db.Numeric(10, 2), nullable=False)
    
    # YTD Totals (CRITICAL FOR CONTINUITY)
    ytd_gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_federal_income_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_social_security_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_additional_medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_state_income_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_state_disability_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_local_income_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_retirement_401k = db.Column(db.Numeric(12, 2), default=0)
    ytd_health_insurance = db.Column(db.Numeric(12, 2), default=0)
    ytd_dental_insurance = db.Column(db.Numeric(12, 2), default=0)
    ytd_vision_insurance = db.Column(db.Numeric(12, 2), default=0)
    ytd_hsa_contribution = db.Column(db.Numeric(12, 2), default=0)
    ytd_net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Social Security Wage Base Tracking
    ytd_ss_wages = db.Column(db.Numeric(12, 2), default=0)
    ss_wage_base_reached = db.Column(db.Boolean, default=False)
    ss_wage_base_limit = db.Column(db.Numeric(12, 2), default=168600.00)
    
    # Medicare Tracking
    ytd_medicare_wages = db.Column(db.Numeric(12, 2), default=0)
    additional_medicare_threshold_reached = db.Column(db.Boolean, default=False)
    
    # PTO Balances
    vacation_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    vacation_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    vacation_balance = db.Column(db.Numeric(8, 2), default=0)
    
    sick_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    sick_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    sick_balance = db.Column(db.Numeric(8, 2), default=0)
    
    personal_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    personal_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    personal_balance = db.Column(db.Numeric(8, 2), default=0)
    
    # Verification & Security
    verification_id = db.Column(db.String(50), unique=True)
    document_hash = db.Column(db.String(64))
    document_serial = db.Column(db.String(100), unique=True)
    qr_code_data = db.Column(db.Text)
    
    # PDF Storage
    pdf_s3_bucket = db.Column(db.String(255))
    pdf_s3_key = db.Column(db.Text)
    pdf_url = db.Column(db.Text)
    pdf_generated_at = db.Column(db.DateTime)
    pdf_file_size_bytes = db.Column(db.Integer)
    
    # Tax Calculation Details
    tax_calculation_method = db.Column(db.String(50))
    federal_tax_bracket_used = db.Column(db.String(20))
    state_tax_bracket_used = db.Column(db.String(20))
    tax_engine_version = db.Column(db.String(20))
    tax_details = db.Column(db.Text)  # JSON string for backward compatibility
    
    # Metadata
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_void = db.Column(db.Boolean, default=False)
    void_reason = db.Column(db.Text)
    voided_at = db.Column(db.DateTime)
    voided_by_user_id = db.Column(db.Integer)
    
    notes = db.Column(db.Text)
    internal_memo = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="paystubs", foreign_keys=[user_id])
    employee = relationship("Employee", back_populates="paystubs")
    company = relationship("Company", back_populates="paystubs")
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'paystub_number', name='uq_employee_paystub_number'),
        CheckConstraint('period_end_date >= period_start_date', name='chk_period_dates'),
        CheckConstraint('pay_date >= period_end_date', name='chk_pay_date'),
        CheckConstraint('gross_pay >= 0', name='chk_gross_pay'),
        CheckConstraint('net_pay >= 0', name='chk_net_pay'),
        CheckConstraint('ytd_gross_pay >= gross_pay', name='chk_ytd_gross'),
    )


class RewardActivity(db.Model):
    __tablename__ = 'reward_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="rewards")


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    paystubs_per_month = db.Column(db.Integer, nullable=False)
    stripe_plan_id = db.Column(db.String(100), unique=True, nullable=False)
    features = db.Column(db.Text)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Initialize subscription plans
def create_initial_subscriptions():
    if not Subscription.query.first():
        db.session.add_all([
            Subscription(
                name="Starter", 
                price=25.00, 
                paystubs_per_month=5, 
                stripe_plan_id="plan_starter_monthly",
                features='["5 paystubs/month", "Basic templates", "Email support", "YTD tracking", "PDF downloads"]'
            ),
            Subscription(
                name="Professional", 
                price=50.00, 
                paystubs_per_month=15, 
                stripe_plan_id="plan_professional_monthly",
                features='["15 paystubs/month", "Premium templates", "Priority support", "Advanced YTD", "Bulk downloads", "Custom branding"]'
            ),
            Subscription(
                name="Business", 
                price=100.00, 
                paystubs_per_month=50, 
                stripe_plan_id="plan_business_monthly",
                features='["50 paystubs/month", "All templates", "Phone support", "API access", "Multi-user", "White-label"]'
            )
        ])
        db.session.commit()

