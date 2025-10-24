from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.complete_models import User, RewardActivity, create_initial_subscription_plans
from src.models.database import db
from datetime import datetime, timedelta
import re
import secrets
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Complete user registration with validation and welcome bonus"""
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'subscription_tier']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        email = data['email'].lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate password strength
        password = data['password']
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Validate subscription tier
        valid_tiers = ['starter', 'professional', 'business']
        subscription_tier = data['subscription_tier']
        if subscription_tier not in valid_tiers:
            return jsonify({'error': 'Invalid subscription tier'}), 400
        
        # Create new user
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=data['full_name'].strip(),
            phone=data.get('phone', '').strip() or None,
            subscription_tier=subscription_tier,
            subscription_status='active',
            subscription_start_date=datetime.utcnow(),
            reward_points=500,  # Welcome bonus
            total_lifetime_points=500,
            email_verification_token=secrets.token_urlsafe(32),
            created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Add welcome bonus reward activity
        welcome_activity = RewardActivity(
            user_id=user.id,
            activity_type='registration_bonus',
            description='Welcome bonus for completing registration',
            points_awarded=500
        )
        db.session.add(welcome_activity)
        
        db.session.commit()
        
        # Log the user in immediately
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'welcome_bonus': 500
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login with session management and login streak tracking"""
    
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update login tracking
        today = datetime.now().date()
        user.last_login = datetime.utcnow()
        
        # Calculate login streak
        if user.last_login_streak_date:
            days_diff = (today - user.last_login_streak_date).days
            if days_diff == 1:
                # Consecutive day
                user.login_streak += 1
            elif days_diff > 1:
                # Streak broken
                user.login_streak = 1
            # Same day login doesn't change streak
        else:
            # First login
            user.login_streak = 1
        
        user.last_login_streak_date = today
        
        # Award login streak bonus (every 5 days)
        if user.login_streak % 5 == 0 and user.login_streak > 0:
            streak_bonus = min(user.login_streak * 5, 100)  # Max 100 points
            user.reward_points += streak_bonus
            user.total_lifetime_points += streak_bonus
            
            # Record reward activity
            streak_activity = RewardActivity(
                user_id=user.id,
                activity_type='login_streak',
                description=f'{user.login_streak}-day login streak bonus',
                points_awarded=streak_bonus
            )
            db.session.add(streak_activity)
        
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'login_streak': user.login_streak
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout - clear session"""
    
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset process"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            
            db.session.commit()
            
            # In production, send email here
            # For now, return the token (remove in production)
            return jsonify({
                'message': 'Password reset instructions sent to your email',
                'reset_token': reset_token  # Remove this in production
            }), 200
        else:
            # Don't reveal if email exists or not
            return jsonify({
                'message': 'If an account with that email exists, password reset instructions have been sent'
            }), 200
            
    except Exception as e:
        return jsonify({'error': 'Password reset request failed'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Complete password reset with token"""
    
    try:
        data = request.get_json()
        
        token = data.get('token', '')
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Find user with valid token
        user = User.query.filter(
            User.password_reset_token == token,
            User.password_reset_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Password reset failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'].strip()
        
        if 'phone' in data:
            user.phone = data['phone'].strip() or None
        
        if 'profile_picture_url' in data:
            user.profile_picture_url = data['profile_picture_url']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password (requires current password)"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        data = request.get_json()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address with token"""
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        user = User.query.filter_by(email_verification_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid verification token'}), 400
        
        user.email_verified = True
        user.email_verification_token = None
        
        # Award email verification bonus
        user.reward_points += 25
        user.total_lifetime_points += 25
        
        verification_activity = RewardActivity(
            user_id=user.id,
            activity_type='email_verification',
            description='Email address verified',
            points_awarded=25
        )
        db.session.add(verification_activity)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Email verified successfully',
            'bonus_points': 25
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Email verification failed'}), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 200
    
    return jsonify({
        'authenticated': True,
        'user': user.to_dict()
    }), 200

# Initialize subscription plans on first import
try:
    create_initial_subscription_plans()
except:
    pass  # Database might not be initialized yet
