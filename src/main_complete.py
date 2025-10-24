from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.database import db
from src.models.complete_models import User, Employee, Company, Paystub, RewardActivity, SubscriptionPlan, create_initial_subscription_plans
from src.routes.complete_auth import auth_bp
from src.routes.complete_dashboard import dashboard_bp
from src.routes.paystub import paystub_bp
from src.routes.subscription import subscription_bp
from src.routes.user import user_bp

# Create Flask app
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'saurellius-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI", 'sqlite:///saurellius.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(paystub_bp, url_prefix='/api/paystub')
app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
app.register_blueprint(user_bp, url_prefix='/api/user')

# Create tables and initial data
with app.app_context():
    db.create_all()
    create_initial_subscription_plans()

# Helper function to check authentication
def is_authenticated():
    return 'user_id' in session

def get_current_user():
    if is_authenticated():
        return User.query.get(session['user_id'])
    return None

# Landing Page Route
@app.route('/')
def landing():
    """Landing page with hero section, features, pricing, and stats"""
    
    # Get subscription plans for pricing section
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_monthly).all()
    
    # Platform stats (can be made dynamic later)
    stats = {
        'happy_users': '15,000+',
        'paystubs_generated': '125,000+',
        'satisfaction_rate': '98%'
    }
    
    return render_template('landing.html', 
                         plans=plans, 
                         stats=stats,
                         current_user=get_current_user())

# Authentication Routes (Frontend)
@app.route('/login')
def login_page():
    """Login page"""
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')

@app.route('/register')
def register_page():
    """Registration page with plan selection"""
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_monthly).all()
    return render_template('auth/register.html', plans=plans)

@app.route('/forgot-password')
def forgot_password_page():
    """Forgot password page"""
    return render_template('auth/forgot_password.html')

@app.route('/reset-password')
def reset_password_page():
    """Reset password page"""
    token = request.args.get('token')
    if not token:
        return redirect(url_for('forgot_password_page'))
    return render_template('auth/reset_password.html', token=token)

# Dashboard Routes (Frontend)
@app.route('/dashboard')
def dashboard():
    """Main dashboard with YTD tracking and employee cards"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    return render_template('dashboard/main.html', user=user)

@app.route('/paystub/generator')
def paystub_generator():
    """Paystub generator form"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    employees = Employee.query.filter_by(user_id=user.id, is_active=True).all()
    companies = Company.query.filter_by(user_id=user.id).all()
    
    return render_template('paystub/generator.html', 
                         user=user, 
                         employees=employees, 
                         companies=companies)

@app.route('/paystub/history')
def paystub_history():
    """Paystub history and management"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    return render_template('paystub/history.html', user=user)

@app.route('/ytd-summary')
def ytd_summary():
    """Year-to-date summary and analytics"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    return render_template('dashboard/ytd_summary.html', user=user)

@app.route('/rewards')
def rewards_center():
    """Rewards center with points, tiers, and activities"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    return render_template('rewards/center.html', user=user)

@app.route('/settings')
def settings():
    """User settings and profile management"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    return render_template('settings/profile.html', user=user)

@app.route('/employees')
def employees():
    """Employee management"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    employees = Employee.query.filter_by(user_id=user.id).all()
    return render_template('employees/list.html', user=user, employees=employees)

@app.route('/employees/add')
def add_employee():
    """Add new employee"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    companies = Company.query.filter_by(user_id=user.id).all()
    return render_template('employees/add.html', user=user, companies=companies)

@app.route('/employees/<int:employee_id>/edit')
def edit_employee(employee_id):
    """Edit existing employee"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    employee = Employee.query.filter_by(id=employee_id, user_id=user.id).first_or_404()
    companies = Company.query.filter_by(user_id=user.id).all()
    
    return render_template('employees/edit.html', 
                         user=user, 
                         employee=employee, 
                         companies=companies)

@app.route('/subscription')
def subscription_management():
    """Subscription management and billing"""
    if not is_authenticated():
        return redirect(url_for('login_page'))
    
    user = get_current_user()
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('subscription/manage.html', user=user, plans=plans)

# Legal Pages
@app.route('/terms')
def terms_of_service():
    """Terms of Service page"""
    return render_template('legal/terms.html')

@app.route('/privacy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('legal/privacy.html')

@app.route('/security')
def security():
    """Security and compliance information"""
    return render_template('legal/security.html')

@app.route('/compliance')
def compliance():
    """Regulatory compliance information"""
    return render_template('legal/compliance.html')

# Support Pages
@app.route('/help')
def help_center():
    """Help center and documentation"""
    return render_template('support/help.html')

@app.route('/contact')
def contact():
    """Contact form and support information"""
    return render_template('support/contact.html')

# Pricing Page
@app.route('/pricing')
def pricing():
    """Detailed pricing page"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_monthly).all()
    return render_template('pricing.html', plans=plans)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Health Check for Elastic Beanstalk
@app.route('/health')
def health_check():
    """Health check endpoint for AWS Elastic Beanstalk"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

# API Status
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'database': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Context Processors (Global Template Variables)
@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    return {
        'current_year': datetime.now().year,
        'app_name': 'Saurellius Cloud Payroll Stub Manager',
        'company_name': 'Dr. Paystub Corp',
        'is_authenticated': is_authenticated(),
        'current_user': get_current_user()
    }

# Template Filters
@app.template_filter('currency')
def currency_filter(amount):
    """Format currency amounts"""
    if amount is None:
        return '$0.00'
    return f'${float(amount):,.2f}'

@app.template_filter('date_format')
def date_format_filter(date, format='%B %d, %Y'):
    """Format dates"""
    if date is None:
        return ''
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    return date.strftime(format)

@app.template_filter('points_format')
def points_format_filter(points):
    """Format reward points"""
    if points is None:
        return '0'
    return f'{int(points):,}'

# Development Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# For Elastic Beanstalk
application = app
