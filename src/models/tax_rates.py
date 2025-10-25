"""
Tax Rates 2025 Model - Store tax rates for all jurisdictions
"""
from src.models.user import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class TaxRates2025(db.Model):
    __tablename__ = 'tax_rates_2025'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Jurisdiction Information
    jurisdiction_type = db.Column(db.String(20), nullable=False)  # federal, state, local, territory
    jurisdiction_code = db.Column(db.String(20), nullable=False)  # US, CA, NYC, etc.
    jurisdiction_name = db.Column(db.String(200), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False, default=2025)
    
    # Federal Tax Data
    federal_standard_deduction_single = db.Column(db.Numeric(10, 2))
    federal_standard_deduction_married = db.Column(db.Numeric(10, 2))
    federal_standard_deduction_hoh = db.Column(db.Numeric(10, 2))
    federal_tax_brackets = db.Column(JSONB)  # Store brackets as JSON
    
    # State Tax Data
    state_tax_type = db.Column(db.String(20))  # progressive, flat, none
    state_flat_rate = db.Column(db.Numeric(6, 4))  # For flat tax states
    state_tax_brackets = db.Column(JSONB)  # For progressive states
    standard_deduction_single = db.Column(db.Numeric(10, 2))
    standard_deduction_married = db.Column(db.Numeric(10, 2))
    standard_deduction_hoh = db.Column(db.Numeric(10, 2))
    personal_exemption = db.Column(db.Numeric(10, 2))
    dependent_exemption = db.Column(db.Numeric(10, 2))
    
    # State Disability Insurance (SDI)
    sdi_rate = db.Column(db.Numeric(6, 4))  # CA, NY, NJ, RI, HI
    sdi_wage_base = db.Column(db.Numeric(12, 2))
    sdi_employee_rate = db.Column(db.Numeric(6, 4))
    sdi_employer_rate = db.Column(db.Numeric(6, 4))
    
    # Local Tax Data
    local_tax_rate = db.Column(db.Numeric(6, 4))
    local_tax_type = db.Column(db.String(20))  # flat, progressive, resident_only
    local_resident_rate = db.Column(db.Numeric(6, 4))
    local_nonresident_rate = db.Column(db.Numeric(6, 4))
    
    # Unemployment Tax
    sui_rate_min = db.Column(db.Numeric(6, 4))  # State Unemployment Insurance
    sui_rate_max = db.Column(db.Numeric(6, 4))
    sui_wage_base = db.Column(db.Numeric(12, 2))
    
    # Metadata
    effective_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date)
    source_url = db.Column(db.String(500))  # Link to official source
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on jurisdiction + year
    __table_args__ = (
        db.UniqueConstraint('jurisdiction_type', 'jurisdiction_code', 'tax_year', name='unique_jurisdiction_year'),
    )
    
    def __repr__(self):
        return f'<TaxRates2025 {self.jurisdiction_code} - {self.tax_year}>'


class FederalPayrollTaxConfig(db.Model):
    __tablename__ = 'federal_payroll_tax_config'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_year = db.Column(db.Integer, nullable=False, default=2025)
    
    # Social Security
    ss_rate = db.Column(db.Numeric(6, 4), nullable=False, default=0.062)  # 6.2%
    ss_wage_base = db.Column(db.Numeric(12, 2), nullable=False, default=176100.00)  # 2025 estimate
    
    # Medicare
    medicare_rate = db.Column(db.Numeric(6, 4), nullable=False, default=0.0145)  # 1.45%
    additional_medicare_rate = db.Column(db.Numeric(6, 4), nullable=False, default=0.009)  # 0.9%
    additional_medicare_threshold_single = db.Column(db.Numeric(12, 2), nullable=False, default=200000.00)
    additional_medicare_threshold_married = db.Column(db.Numeric(12, 2), nullable=False, default=250000.00)
    additional_medicare_threshold_hoh = db.Column(db.Numeric(12, 2), nullable=False, default=200000.00)
    
    # Federal Unemployment (FUTA)
    futa_rate = db.Column(db.Numeric(6, 4), nullable=False, default=0.006)  # 0.6% after credit
    futa_wage_base = db.Column(db.Numeric(12, 2), nullable=False, default=7000.00)
    
    # Standard Deductions (for informational purposes)
    standard_deduction_single = db.Column(db.Numeric(10, 2), nullable=False, default=14600.00)
    standard_deduction_married = db.Column(db.Numeric(10, 2), nullable=False, default=29200.00)
    standard_deduction_hoh = db.Column(db.Numeric(10, 2), nullable=False, default=21900.00)
    
    # Tax Brackets (stored as JSON)
    tax_brackets_single = db.Column(JSONB)
    tax_brackets_married = db.Column(JSONB)
    tax_brackets_hoh = db.Column(JSONB)
    
    # Metadata
    effective_date = db.Column(db.Date, nullable=False)
    source_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FederalPayrollTaxConfig {self.tax_year}>'

