"""
Comprehensive Database Models for Saurellius Platform
Includes users, paystubs, subscriptions, rewards, and tax configuration
"""

from datetime import datetime
from src.models.user import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    """User model with subscription and rewards tracking"""
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
    two_factor_secret = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paystubs = db.relationship('Paystub', backref='user', lazy=True, cascade='all, delete-orphan')
    employees = db.relationship('Employee', backref='user', lazy=True, cascade='all, delete-orphan')
    reward_activities = db.relationship('RewardActivity', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'email': self.email,
            'full_name': self.full_name,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'reward_points': self.reward_points,
            'reward_tier': self.reward_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Employee(db.Model):
    """Employee/Payee information for multi-employee support"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    ssn_last_four = db.Column(db.String(4))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)
    
    # Default employer info
    employer_name = db.Column(db.String(255))
    employer_address = db.Column(db.Text)
    employer_ein = db.Column(db.String(20))
    
    # Pay frequency
    pay_frequency = db.Column(db.String(50), default='biweekly')  # weekly, biweekly, semimonthly, monthly
    
    # Tax info
    filing_status = db.Column(db.String(50))  # single, married_filing_jointly, etc
    state = db.Column(db.String(50))
    dependents = db.Column(db.Integer, default=0)
    
    # YTD tracking
    ytd_gross = db.Column(db.Numeric(12, 2), default=0)
    ytd_federal_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_state_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_social_security = db.Column(db.Numeric(12, 2), default=0)
    ytd_medicare = db.Column(db.Numeric(12, 2), default=0)
    ytd_net = db.Column(db.Numeric(12, 2), default=0)
    
    last_paystub_number = db.Column(db.Integer, default=0)
    last_paystub_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paystubs = db.relationship('Paystub', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'employer_name': self.employer_name,
            'pay_frequency': self.pay_frequency,
            'ytd_gross': float(self.ytd_gross) if self.ytd_gross else 0,
            'ytd_net': float(self.ytd_net) if self.ytd_net else 0,
            'last_paystub_number': self.last_paystub_number,
            'last_paystub_date': self.last_paystub_date.isoformat() if self.last_paystub_date else None
        }


class Paystub(db.Model):
    """Paystub records with complete tax and deduction information"""
    __tablename__ = 'paystubs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Paystub identification
    paystub_number = db.Column(db.Integer, nullable=False)
    check_number = db.Column(db.String(50))
    
    # Pay period
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    
    # Earnings
    gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    regular_hours = db.Column(db.Numeric(8, 2))
    regular_rate = db.Column(db.Numeric(10, 2))
    overtime_hours = db.Column(db.Numeric(8, 2))
    overtime_rate = db.Column(db.Numeric(10, 2))
    
    # Deductions
    federal_income_tax = db.Column(db.Numeric(12, 2), default=0)
    social_security_tax = db.Column(db.Numeric(12, 2), default=0)
    medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    additional_medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    state_income_tax = db.Column(db.Numeric(12, 2), default=0)
    local_income_tax = db.Column(db.Numeric(12, 2), default=0)
    
    # Other deductions
    health_insurance = db.Column(db.Numeric(12, 2), default=0)
    retirement_401k = db.Column(db.Numeric(12, 2), default=0)
    other_deductions = db.Column(db.Numeric(12, 2), default=0)
    
    # Totals
    total_deductions = db.Column(db.Numeric(12, 2), default=0)
    net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # YTD values
    ytd_gross = db.Column(db.Numeric(12, 2), nullable=False)
    ytd_federal_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_state_tax = db.Column(db.Numeric(12, 2), default=0)
    ytd_social_security = db.Column(db.Numeric(12, 2), default=0)
    ytd_medicare = db.Column(db.Numeric(12, 2), default=0)
    ytd_net = db.Column(db.Numeric(12, 2), default=0)
    
    # PDF storage
    pdf_url = db.Column(db.Text)
    pdf_hash = db.Column(db.String(64))  # SHA256 hash for integrity
    
    # Verification
    verification_id = db.Column(db.String(50), unique=True)
    qr_code_data = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'paystub_number': self.paystub_number,
            'pay_date': self.pay_date.isoformat() if self.pay_date else None,
            'gross_pay': float(self.gross_pay) if self.gross_pay else 0,
            'net_pay': float(self.net_pay) if self.net_pay else 0,
            'ytd_gross': float(self.ytd_gross) if self.ytd_gross else 0,
            'ytd_net': float(self.ytd_net) if self.ytd_net else 0,
            'pdf_url': self.pdf_url,
            'verification_id': self.verification_id
        }


class Subscription(db.Model):
    """Subscription plans and pricing"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # starter, professional, business
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    price_annual = db.Column(db.Numeric(10, 2))
    
    # Features
    max_employees = db.Column(db.Integer, default=1)
    max_paystubs_per_month = db.Column(db.Integer, default=10)
    api_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    custom_branding = db.Column(db.Boolean, default=False)
    
    stripe_product_id = db.Column(db.String(255))
    stripe_price_id_monthly = db.Column(db.String(255))
    stripe_price_id_annual = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price_monthly': float(self.price_monthly) if self.price_monthly else 0,
            'max_employees': self.max_employees,
            'max_paystubs_per_month': self.max_paystubs_per_month
        }


class RewardActivity(db.Model):
    """Track reward points and activities"""
    __tablename__ = 'reward_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)  # paystub_generated, login_streak, etc
    points_earned = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    metadata = db.Column(db.JSON)  # Store additional data like paystub_id, streak_count, etc
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'points_earned': self.points_earned,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TaxRate(db.Model):
    """Tax rates for 2025/2026 - federal, state, and local"""
    __tablename__ = 'tax_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    tax_type = db.Column(db.String(100), nullable=False)  # federal_income, state_income, local_income, fica, etc
    jurisdiction = db.Column(db.String(100), nullable=False)  # US, CA, NY, etc
    filing_status = db.Column(db.String(50))  # single, married_filing_jointly, etc
    
    # Tax bracket information
    income_min = db.Column(db.Numeric(15, 2))
    income_max = db.Column(db.Numeric(15, 2))
    rate = db.Column(db.Numeric(6, 4))  # 0.1234 for 12.34%
    
    # Additional parameters
    standard_deduction = db.Column(db.Numeric(12, 2))
    exemption_amount = db.Column(db.Numeric(12, 2))
    
    metadata = db.Column(db.JSON)  # Store additional tax rules
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_tax_rates_year_type_jurisdiction', 'year', 'tax_type', 'jurisdiction'),
    )


class FederalPayrollConfig(db.Model):
    """Federal payroll tax configuration"""
    __tablename__ = 'federal_payroll_config'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)
    
    # Social Security
    social_security_wage_base = db.Column(db.Numeric(12, 2), nullable=False)
    social_security_rate = db.Column(db.Numeric(6, 4), nullable=False)
    
    # Medicare
    medicare_rate = db.Column(db.Numeric(6, 4), nullable=False)
    additional_medicare_threshold_single = db.Column(db.Numeric(12, 2), nullable=False)
    additional_medicare_threshold_married = db.Column(db.Numeric(12, 2), nullable=False)
    additional_medicare_rate = db.Column(db.Numeric(6, 4), nullable=False)
    
    # FUTA
    futa_rate = db.Column(db.Numeric(6, 4), nullable=False)
    futa_wage_base = db.Column(db.Numeric(12, 2), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

