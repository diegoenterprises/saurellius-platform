from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# JWT decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing username, email, or password'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(
        username=data['username'], 
        email=data['email'], 
        password_hash=hashed_password,
        last_activity=datetime.datetime.utcnow()
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401

    user = User.query.filter_by(email=auth['email']).first()

    if not user or not check_password_hash(user.password_hash, auth['password']):
        return jsonify({'message': 'Could not verify'}), 401

    # Update last activity
    user.last_activity = datetime.datetime.utcnow()
    db.session.commit()

    token = jwt.encode({
        'id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({'token': token, 'user': user.to_dict()}), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'message': 'Missing old and new passwords'}), 400

    if not check_password_hash(current_user.password_hash, data['old_password']):
        return jsonify({'message': 'Incorrect old password'}), 401

    current_user.password_hash = generate_password_hash(data['new_password'], method='pbkdf2:sha256')
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # For JWT, logout is handled client-side by deleting the token.
    # We can implement a server-side token blacklist if necessary, but for now,
    # we'll just return a success message.
    return jsonify({'message': 'Logged out successfully'}), 200
