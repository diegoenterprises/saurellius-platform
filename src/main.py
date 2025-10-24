import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.paystub import paystub_bp

app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(paystub_bp, url_prefix='/api')

# Create database tables
with app.app_context():
    db.create_all()

# ============ FRONTEND ROUTES ============

@app.route('/')
def index():
    """Landing page"""
    stats = {
        'total_paystubs': '50K+',
        'active_users': '15K+'
    }
    return render_template('index.html', stats=stats)

@app.route('/login', methods=['GET'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    plan = request.args.get('plan', 'professional')
    return render_template('register.html', selected_plan=plan)

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get user statistics
    user_stats = {
        'total_paystubs': current_user.paystubs.count() if hasattr(current_user, 'paystubs') else 0,
        'ytd_gross': 0,
        'ytd_net': 0,
        'average_net': 0
    }
    
    # Get employees
    employees = current_user.employees if hasattr(current_user, 'employees') else []
    
    # Get rewards data
    rewards = {
        'current_tier': '🥉 Bronze',
        'current_points': current_user.reward_points if hasattr(current_user, 'reward_points') else 0,
        'points_to_next_tier': 250,
        'progress_percentage': 0,
        'recent_activities': []
    }
    
    # Get recent activity
    recent_activity = []
    
    return render_template('dashboard.html',
        user_stats=user_stats,
        employees=employees,
        rewards=rewards,
        recent_activity=recent_activity
    )

@app.route('/paystub-generator')
def paystub_generator():
    """Paystub generator page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    employees = current_user.employees if hasattr(current_user, 'employees') else []
    return render_template('paystub-generator.html', employees=employees)

@app.route('/paystub-history')
def paystub_history():
    """Paystub history page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    paystubs = current_user.paystubs if hasattr(current_user, 'paystubs') else []
    return render_template('paystub-history.html', paystubs=paystubs)

@app.route('/ytd-summary')
def ytd_summary():
    """YTD summary page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('ytd-summary.html')

@app.route('/rewards')
def rewards():
    """Rewards center page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('rewards.html')

@app.route('/settings')
def settings():
    """User settings page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('settings.html')

@app.route('/add-employee')
def add_employee():
    """Add employee page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('add-employee.html')

@app.route('/edit-employee')
def edit_employee():
    """Edit employee page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    employee_id = request.args.get('id')
    return render_template('edit-employee.html', employee_id=employee_id)

@app.route('/forgot-password')
def forgot_password():
    """Forgot password page"""
    return render_template('forgot-password.html')

# ============ LEGAL & INFO PAGES ============

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.route('/security')
def security():
    """Security page"""
    return render_template('security.html')

@app.route('/compliance')
def compliance():
    """Compliance page"""
    return render_template('compliance.html')

@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        # Handle contact form submission
        data = request.get_json()
        # TODO: Send email or save to database
        return jsonify({'message': 'Message received'}), 200
    
    return render_template('contact.html')

@app.route('/blog')
def blog():
    """Blog page"""
    return render_template('blog.html')

@app.route('/careers')
def careers():
    """Careers page"""
    return render_template('careers.html')

# ============ API HEALTH CHECK ============

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

