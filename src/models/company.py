from src.models.database import db
from datetime import datetime
from sqlalchemy.orm import relationship

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

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'legal_name': self.legal_name,
            'ein': self.ein,
            'address_state': self.address_state
        }
