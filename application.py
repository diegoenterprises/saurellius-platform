import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from datetime import datetime
from src.models.database import db
from src.routes.user import user_bp
from src.routes.paystub import paystub_bp
from src.routes.auth import auth_bp
from src.routes.subscription import subscription_bp
from src.routes.paystub_advanced import paystub_advanced_bp
from src.routes.paystub_complete import paystub_complete_bp
from src.routes.dashboard import dashboard_bp
from src.routes.employee import employee_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'src', 'static'))
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'asdf#FGSgvasgf$5$WGT')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(paystub_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
app.register_blueprint(paystub_advanced_bp, url_prefix='/api/paystubs')
app.register_blueprint(paystub_complete_bp, url_prefix='/api/paystubs')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(employee_bp, url_prefix='/api/employees')

# Database configuration and initialization
db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
if db_uri:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    
    db.init_app(app)
    with app.app_context():
        # Import models to ensure they're registered
        from src.models.user import User, Employee, Company, Paystub, RewardActivity, Subscription, create_initial_subscriptions
        
        # Create tables on first run (idempotent)
        db.create_all()
        
        # Initialize subscription plans
        try:
            create_initial_subscriptions()
        except Exception as e:
            print(f"Subscription initialization: {e}")


# Health check endpoint for Elastic Beanstalk
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Elastic Beanstalk"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db_uri else 'not configured'
    }), 200


@app.route('/api/test', methods=['GET'])
def api_test():
    """Test endpoint to verify API is working"""
    return jsonify({
        'message': 'Saurellius API is running',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Elastic Beanstalk expects 'application'
application = app

