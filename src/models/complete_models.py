from src.models.database import db
from datetime import datetime, date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    profile_picture_url = db.Column(db.Text)
    
    # Subscription
    subscription_tier = db.Column(db.String(50), default='starter')  # starter, professional, business
    subscription_status = db.Column(db.String(50), default='active')  # active, cancelled, past_due
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(255))
    stripe_subscription_id = db.Column(db.String(255))
    
    # Rewards
    reward_points = db.Column(db.Integer, default=0)
    reward_tier = db.Column(db.String(50), default='bronze')  # bronze, silver, gold, platinum
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
    login_streak = db.Column(db.Integer, default=0)
    last_login_streak_date = db.Column(db.Date)
    
    # Relationships
    companies = relationship("Company", back_populates="user", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="user", cascade="all, delete-orphan")
    paystubs = relationship("Paystub", back_populates="user", cascade="all, delete-orphan")
    reward_activities = relationship("RewardActivity", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'reward_points': self.reward_points,
            'reward_tier': self.reward_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Company Info
    legal_name = db.Column(db.String(255), nullable=False)
    dba_name = db.Column(db.String(255))
    ein = db.Column(db.String(10), nullable=False)  # Format: XX-XXXXXXX
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
    business_structure = db.Column(db.String(50))  # LLC, Corp, Sole Proprietor, etc.
    
    # Branding
    company_logo_url = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="companies")
    employees = relationship("Employee", back_populates="company", cascade="all, delete-orphan")

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Personal Info
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    ssn_encrypted = db.Column(db.Text, nullable=False)  # AES-256 encrypted
    ssn_last_four = db.Column(db.String(4), nullable=False)
    date_of_birth = db.Column(db.Date)
    employee_id = db.Column(db.String(50))
    hire_date = db.Column(db.Date)
    
    # Contact
    address_street = db.Column(db.String(255))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2), nullable=False)  # Critical for tax calculations
    address_zip = db.Column(db.String(10))
    address_county = db.Column(db.String(100))  # For local taxes
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # Employment Details
    employment_type = db.Column(db.String(50), nullable=False)  # Full-Time, Part-Time, Contract, Self-Employed
    pay_frequency = db.Column(db.String(20), nullable=False)  # Weekly, BiWeekly, SemiMonthly, Monthly
    pay_method = db.Column(db.String(20), default='Direct Deposit')  # Direct Deposit, Check
    
    # Compensation
    hourly_rate = db.Column(db.Numeric(10, 2))
    salary_annual = db.Column(db.Numeric(12, 2))
    overtime_rate = db.Column(db.Numeric(10, 2))
    
    # Tax Settings
    federal_filing_status = db.Column(db.String(20), nullable=False)  # Single, Married Filing Jointly, etc.
    federal_allowances = db.Column(db.Integer, default=0)
    state_filing_status = db.Column(db.String(20))
    state_allowances = db.Column(db.Integer, default=0)
    additional_federal_withholding = db.Column(db.Numeric(10, 2), default=0)
    additional_state_withholding = db.Column(db.Numeric(10, 2), default=0)
    
    # Benefits & Deductions
    health_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    dental_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    vision_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    retirement_401k_pretax = db.Column(db.Numeric(10, 2), default=0)
    retirement_401k_roth = db.Column(db.Numeric(10, 2), default=0)
    hsa_contribution = db.Column(db.Numeric(10, 2), default=0)
    
    # YTD Tracking
    ytd_gross_pay = db.Column(db.Numeric(12, 2), default=0)
    ytd_net_pay = db.Column(db.Numeric(12, 2), default=0)
    ytd_federal_income_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_social_security_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_state_income_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_sdi_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_health_insurance = db.Column(db.Numeric(12, 2), default=0)
    ytd_retirement_401k = db.Column(db.Numeric(12, 2), default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    termination_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="employees")
    user = relationship("User", back_populates="employees")
    paystubs = relationship("Paystub", back_populates="employee", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

class Paystub(db.Model):
    __tablename__ = 'paystubs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Pay Period Info
    paystub_number = db.Column(db.Integer, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    
    # Earnings
    regular_hours = db.Column(db.Numeric(8, 2), default=0)
    overtime_hours = db.Column(db.Numeric(8, 2), default=0)
    regular_pay = db.Column(db.Numeric(10, 2), default=0)
    overtime_pay = db.Column(db.Numeric(10, 2), default=0)
    bonus_pay = db.Column(db.Numeric(10, 2), default=0)
    commission_pay = db.Column(db.Numeric(10, 2), default=0)
    gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Pre-Tax Deductions
    health_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    dental_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    vision_insurance_pretax = db.Column(db.Numeric(10, 2), default=0)
    retirement_401k_pretax = db.Column(db.Numeric(10, 2), default=0)
    hsa_contribution = db.Column(db.Numeric(10, 2), default=0)
    
    # Taxable Income (after pre-tax deductions)
    taxable_income = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Tax Withholdings
    federal_income_tax = db.Column(db.Numeric(10, 2), default=0)
    social_security_tax = db.Column(db.Numeric(10, 2), default=0)
    medicare_tax = db.Column(db.Numeric(10, 2), default=0)
    state_income_tax = db.Column(db.Numeric(10, 2), default=0)
    sdi_tax = db.Column(db.Numeric(10, 2), default=0)  # State Disability Insurance
    local_tax = db.Column(db.Numeric(10, 2), default=0)
    
    # Post-Tax Deductions
    retirement_401k_roth = db.Column(db.Numeric(10, 2), default=0)
    union_dues = db.Column(db.Numeric(10, 2), default=0)
    parking_fee = db.Column(db.Numeric(10, 2), default=0)
    
    # Net Pay
    net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # YTD Totals (at time of paystub generation)
    ytd_gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_taxable_income = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_federal_income_tax = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_social_security_tax = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_medicare_tax = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_state_income_tax = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # PDF & Security
    pdf_file_path = db.Column(db.Text)
    pdf_s3_key = db.Column(db.Text)
    verification_qr_code = db.Column(db.Text)
    verification_id = db.Column(db.String(20))
    security_hash = db.Column(db.String(64))
    
    # Status
    is_draft = db.Column(db.Boolean, default=False)
    is_voided = db.Column(db.Boolean, default=False)
    void_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="paystubs")
    employee = relationship("Employee", back_populates="paystubs")

class RewardActivity(db.Model):
    __tablename__ = 'reward_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    activity_type = db.Column(db.String(50), nullable=False)  # paystub_generated, login_streak, referral, etc.
    description = db.Column(db.String(255), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False)
    
    # Metadata
    paystub_id = db.Column(db.Integer, db.ForeignKey('paystubs.id'))  # If related to paystub
    referral_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # If referral activity
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reward_activities")

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    price_monthly = db.Column(db.Numeric(8, 2), nullable=False)
    paystubs_per_month = db.Column(db.Integer, nullable=False)
    max_employees = db.Column(db.Integer, nullable=False)
    
    # Features
    priority_support = db.Column(db.Boolean, default=False)
    api_access = db.Column(db.Boolean, default=False)
    custom_templates = db.Column(db.Boolean, default=False)
    bulk_generation = db.Column(db.Boolean, default=False)
    
    # Stripe Integration
    stripe_price_id = db.Column(db.String(255), unique=True, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize subscription plans
def create_initial_subscription_plans():
    """Create the initial subscription plans if they don't exist"""
    if not SubscriptionPlan.query.first():
        plans = [
            SubscriptionPlan(
                name='starter',
                display_name='Starter',
                price_monthly=25.00,
                paystubs_per_month=5,
                max_employees=1,
                priority_support=False,
                api_access=False,
                custom_templates=False,
                bulk_generation=False,
                stripe_price_id='price_starter_monthly'
            ),
            SubscriptionPlan(
                name='professional',
                display_name='Professional',
                price_monthly=50.00,
                paystubs_per_month=20,
                max_employees=5,
                priority_support=True,
                api_access=False,
                custom_templates=True,
                bulk_generation=False,
                stripe_price_id='price_professional_monthly'
            ),
            SubscriptionPlan(
                name='business',
                display_name='Business',
                price_monthly=100.00,
                paystubs_per_month=9999,  # Unlimited
                max_employees=50,
                priority_support=True,
                api_access=True,
                custom_templates=True,
                bulk_generation=True,
                stripe_price_id='price_business_monthly'
            )
        ]
        
        db.session.add_all(plans)
        db.session.commit()
        print("✅ Subscription plans created successfully")
