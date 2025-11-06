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




class RewardActivity(db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = 'reward_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="rewards")


class Subscription(db.Model):
    __table_args__ = {"extend_existing": True}
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
    if not db.session.execute(db.select(Subscription)).first():
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

