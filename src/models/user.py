from src.models.database import db
from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20), nullable=True)
    
    # Subscription Tracking
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    subscription_tier = db.Column(db.String(50), default='starter')
    is_active_subscriber = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Rewards and Gamification Tracking
    reward_points = db.Column(db.Integer, default=0)
    total_lifetime_points = db.Column(db.Integer, default=0)
    reward_tier = db.Column(db.String(50), default='bronze')
    lifetime_paystubs_generated = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employees = relationship("Employee", back_populates="user")
    paystubs = relationship("Paystub", back_populates="user")
    rewards = relationship("RewardActivity", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'subscription_tier': self.subscription_tier,
            'is_active_subscriber': self.is_active_subscriber,
            'reward_points': self.reward_points,
            'reward_tier': self.reward_tier,
            'total_lifetime_points': self.total_lifetime_points,
            'lifetime_paystubs_generated': self.lifetime_paystubs_generated,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    paystubs_per_month = db.Column(db.Integer, nullable=False)
    stripe_plan_id = db.Column(db.String(100), unique=True, nullable=False)
    
    users = relationship("User", backref="subscription")

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    ytd_gross = db.Column(db.Float, default=0.0)
    ytd_net = db.Column(db.Float, default=0.0)
    
    user = relationship("User", back_populates="employees")
    paystubs = relationship("Paystub", back_populates="employee")

class Paystub(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    gross_pay = db.Column(db.Float, nullable=False)
    net_pay = db.Column(db.Float, nullable=False)
    tax_details = db.Column(db.Text, nullable=False) # JSON string of tax and deduction details
    
    user = relationship("User", back_populates="paystubs")
    employee = relationship("Employee", back_populates="paystubs")

class RewardActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., 'paystub_generated', 'login_streak', 'referral'
    points_awarded = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="rewards")
    
# Add initial subscription plans to the database
def create_initial_subscriptions():
    if not Subscription.query.first():
        db.session.add_all([
            Subscription(name="Starter", price=25.00, paystubs_per_month=5, stripe_plan_id="plan_starter_monthly"),
            Subscription(name="Professional", price=50.00, paystubs_per_month=15, stripe_plan_id="plan_professional_monthly"),
            Subscription(name="Business", price=100.00, paystubs_per_month=50, stripe_plan_id="plan_business_monthly")
        ])
        db.session.commit()

