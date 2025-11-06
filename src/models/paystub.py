"""
Complete Paystub Model - All 117 Fields from Deployment Guide
"""
from src.models.database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


class Paystub(db.Model):
    __tablename__ = 'paystubs'
    
    # Primary identification
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=False)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('companies.id'), nullable=True)
    
    # Pay Period Information
    pay_date = db.Column(db.Date, nullable=False)
    period_start_date = db.Column(db.Date, nullable=False)
    period_end_date = db.Column(db.Date, nullable=False)
    paystub_number = db.Column(db.Integer, nullable=False)
    check_number = db.Column(db.String(50))
    pay_frequency = db.Column(db.String(20))  # Weekly, BiWeekly, SemiMonthly, Monthly
    
    # Hours Worked
    regular_hours = db.Column(db.Numeric(8, 2), default=0)
    overtime_hours = db.Column(db.Numeric(8, 2), default=0)
    double_time_hours = db.Column(db.Numeric(8, 2), default=0)
    
    # Earnings - Current Period
    regular_pay = db.Column(db.Numeric(12, 2), default=0)
    overtime_pay = db.Column(db.Numeric(12, 2), default=0)
    double_time_pay = db.Column(db.Numeric(12, 2), default=0)
    bonus = db.Column(db.Numeric(12, 2), default=0)
    commission = db.Column(db.Numeric(12, 2), default=0)
    tips = db.Column(db.Numeric(12, 2), default=0)
    holiday_pay = db.Column(db.Numeric(12, 2), default=0)
    sick_pay = db.Column(db.Numeric(12, 2), default=0)
    vacation_pay = db.Column(db.Numeric(12, 2), default=0)
    severance_pay = db.Column(db.Numeric(12, 2), default=0)
    other_earnings = db.Column(db.Numeric(12, 2), default=0)
    gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Federal Taxes - Current Period
    federal_income_tax = db.Column(db.Numeric(12, 2), default=0)
    social_security_tax = db.Column(db.Numeric(12, 2), default=0)
    medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    additional_medicare_tax = db.Column(db.Numeric(12, 2), default=0)
    
    # State Taxes - Current Period
    state_income_tax = db.Column(db.Numeric(12, 2), default=0)
    state_disability_tax = db.Column(db.Numeric(12, 2), default=0)  # CA, NY, NJ, RI, HI
    state_unemployment_tax = db.Column(db.Numeric(12, 2), default=0)
    
    # Local Taxes - Current Period
    local_income_tax = db.Column(db.Numeric(12, 2), default=0)
    city_tax = db.Column(db.Numeric(12, 2), default=0)
    county_tax = db.Column(db.Numeric(12, 2), default=0)
    school_district_tax = db.Column(db.Numeric(12, 2), default=0)
    
    # Pre-Tax Deductions - Current Period
    deduction_401k = db.Column(db.Numeric(12, 2), default=0)
    deduction_403b = db.Column(db.Numeric(12, 2), default=0)
    deduction_health_insurance = db.Column(db.Numeric(12, 2), default=0)
    deduction_dental_insurance = db.Column(db.Numeric(12, 2), default=0)
    deduction_vision_insurance = db.Column(db.Numeric(12, 2), default=0)
    deduction_hsa = db.Column(db.Numeric(12, 2), default=0)
    deduction_fsa = db.Column(db.Numeric(12, 2), default=0)
    deduction_commuter_benefits = db.Column(db.Numeric(12, 2), default=0)
    deduction_dependent_care = db.Column(db.Numeric(12, 2), default=0)
    
    # Post-Tax Deductions - Current Period
    deduction_roth_401k = db.Column(db.Numeric(12, 2), default=0)
    deduction_life_insurance = db.Column(db.Numeric(12, 2), default=0)
    deduction_disability_insurance = db.Column(db.Numeric(12, 2), default=0)
    deduction_union_dues = db.Column(db.Numeric(12, 2), default=0)
    deduction_other = db.Column(db.Numeric(12, 2), default=0)
    
    # Garnishments - Current Period
    garnishment_child_support = db.Column(db.Numeric(12, 2), default=0)
    garnishment_wage_garnishment = db.Column(db.Numeric(12, 2), default=0)
    garnishment_tax_levy = db.Column(db.Numeric(12, 2), default=0)
    garnishment_student_loan = db.Column(db.Numeric(12, 2), default=0)
    garnishment_bankruptcy = db.Column(db.Numeric(12, 2), default=0)
    
    # Totals - Current Period
    total_taxes = db.Column(db.Numeric(12, 2), default=0)
    total_deductions = db.Column(db.Numeric(12, 2), default=0)
    total_garnishments = db.Column(db.Numeric(12, 2), default=0)
    net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # YTD Earnings
    ytd_gross = db.Column(db.Numeric(15, 2), default=0)
    ytd_regular_pay = db.Column(db.Numeric(15, 2), default=0)
    ytd_overtime_pay = db.Column(db.Numeric(15, 2), default=0)
    ytd_bonus = db.Column(db.Numeric(15, 2), default=0)
    ytd_commission = db.Column(db.Numeric(15, 2), default=0)
    ytd_tips = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD Federal Taxes
    ytd_federal_income_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_social_security_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_medicare_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_additional_medicare_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_ss_wages = db.Column(db.Numeric(15, 2), default=0)  # For wage base tracking
    ytd_medicare_wages = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD State Taxes
    ytd_state_income_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_state_disability_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_state_wages = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD Local Taxes
    ytd_local_income_tax = db.Column(db.Numeric(15, 2), default=0)
    ytd_local_wages = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD Deductions
    ytd_401k = db.Column(db.Numeric(15, 2), default=0)
    ytd_403b = db.Column(db.Numeric(15, 2), default=0)
    ytd_roth_401k = db.Column(db.Numeric(15, 2), default=0)
    ytd_health_insurance = db.Column(db.Numeric(15, 2), default=0)
    ytd_dental_insurance = db.Column(db.Numeric(15, 2), default=0)
    ytd_vision_insurance = db.Column(db.Numeric(15, 2), default=0)
    ytd_hsa = db.Column(db.Numeric(15, 2), default=0)
    ytd_fsa = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD Garnishments
    ytd_child_support = db.Column(db.Numeric(15, 2), default=0)
    ytd_wage_garnishment = db.Column(db.Numeric(15, 2), default=0)
    ytd_tax_levy = db.Column(db.Numeric(15, 2), default=0)
    
    # YTD Totals
    ytd_total_taxes = db.Column(db.Numeric(15, 2), default=0)
    ytd_total_deductions = db.Column(db.Numeric(15, 2), default=0)
    ytd_total_garnishments = db.Column(db.Numeric(15, 2), default=0)
    ytd_net_pay = db.Column(db.Numeric(15, 2), default=0)
    
    # PTO Balances (as of this paystub)
    pto_vacation_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_sick_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_personal_used_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_vacation_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_sick_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_personal_accrued_this_period = db.Column(db.Numeric(8, 2), default=0)
    pto_vacation_balance = db.Column(db.Numeric(8, 2), default=0)
    pto_sick_balance = db.Column(db.Numeric(8, 2), default=0)
    pto_personal_balance = db.Column(db.Numeric(8, 2), default=0)
    pto_vacation_ytd_used = db.Column(db.Numeric(8, 2), default=0)
    pto_sick_ytd_used = db.Column(db.Numeric(8, 2), default=0)
    pto_personal_ytd_used = db.Column(db.Numeric(8, 2), default=0)
    
    # Employer Contributions (informational)
    employer_401k_match = db.Column(db.Numeric(12, 2), default=0)
    employer_health_insurance = db.Column(db.Numeric(12, 2), default=0)
    employer_social_security = db.Column(db.Numeric(12, 2), default=0)
    employer_medicare = db.Column(db.Numeric(12, 2), default=0)
    employer_unemployment = db.Column(db.Numeric(12, 2), default=0)
    
    # Verification & Security
    verification_id = db.Column(db.String(100), unique=True)  # Unique verification code
    document_hash = db.Column(db.String(64))  # SHA-256 hash of PDF
    qr_code_data = db.Column(db.Text)  # QR code content for verification
    verification_url = db.Column(db.String(500))  # Public verification URL
    
    # PDF Storage
    pdf_s3_bucket = db.Column(db.String(100))
    pdf_s3_key = db.Column(db.String(500))
    pdf_url = db.Column(db.String(1000))  # Signed URL or public URL
    pdf_generated_at = db.Column(db.DateTime)
    
    # Tax Calculation Audit Trail
    tax_calculation_method = db.Column(db.String(50))  # 2020_W4, 2024_W4, etc.
    tax_calculation_timestamp = db.Column(db.DateTime)
    tax_calculation_version = db.Column(db.String(20))  # Version of tax engine
    tax_rates_used = db.Column(JSONB)  # Store actual rates used for audit
    
    # Status & Metadata
    status = db.Column(db.String(20), default='draft')  # draft, finalized, void
    is_void = db.Column(db.Boolean, default=False)
    void_reason = db.Column(db.Text)
    void_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalized_at = db.Column(db.DateTime)
    
    # Additional Data
    memo = db.Column(db.Text)
    notes = db.Column(db.Text)
    custom_fields = db.Column(JSONB)  # For additional custom data
    
    def __repr__(self):
        return f'<Paystub #{self.paystub_number} - ${self.net_pay}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'paystub_number': self.paystub_number,
            'pay_date': self.pay_date.isoformat() if self.pay_date else None,
            'period_start': self.period_start_date.isoformat() if self.period_start_date else None,
            'period_end': self.period_end_date.isoformat() if self.period_end_date else None,
            'gross_pay': float(self.gross_pay) if self.gross_pay else 0,
            'net_pay': float(self.net_pay) if self.net_pay else 0,
            'total_taxes': float(self.total_taxes) if self.total_taxes else 0,
            'total_deductions': float(self.total_deductions) if self.total_deductions else 0,
            'verification_id': self.verification_id,
            'pdf_url': self.pdf_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

