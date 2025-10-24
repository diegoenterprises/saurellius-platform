from flask import Blueprint, jsonify
from src.models.database import db
from src.models.user import User, Employee, Paystub, RewardActivity
from src.routes.auth import token_required
from sqlalchemy import func, extract
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@token_required
def get_dashboard_summary(current_user):
    # 1. Comprehensive YTD Summary
    current_year = datetime.now().year
    
    ytd_data = db.session.query(
        func.sum(Paystub.gross_pay).label('ytd_gross'),
        func.sum(Paystub.net_pay).label('ytd_net')
    ).filter(
        Paystub.user_id == current_user.id,
        extract('year', Paystub.pay_date) == current_year
    ).first()
    
    ytd_gross = ytd_data.ytd_gross if ytd_data.ytd_gross else 0.0
    ytd_net = ytd_data.ytd_net if ytd_data.ytd_net else 0.0
    
    # 2. Employee Cards with quick actions (just data for now)
    employees = Employee.query.filter_by(user_id=current_user.id).all()
    employee_cards = []
    for emp in employees:
        employee_cards.append({
            'id': emp.id,
            'name': emp.name,
            'paystub_count': Paystub.query.filter_by(employee_id=emp.id).count()
        })
        
    # 3. Rewards and achievements tracking
    total_rewards = current_user.reward_points
    
    # 4. Recent activity feed
    recent_activity = RewardActivity.query.filter_by(user_id=current_user.id)\
        .order_by(RewardActivity.timestamp.desc()).limit(5).all()
        
    activity_feed = [{
        'type': ra.type,
        'points': ra.points_awarded,
        'timestamp': ra.timestamp.isoformat()
    } for ra in recent_activity]
    
    # 5. Tier progress visualization (based on paystub count)
    paystub_count = current_user.lifetime_paystubs_generated
    tier = "Bronze"
    if paystub_count >= 10:
        tier = "Silver"
    if paystub_count >= 50:
        tier = "Gold"
    if paystub_count >= 100:
        tier = "Platinum"
        
    return jsonify({
        'user_info': current_user.to_dict(),
        'ytd_summary': {
            'year': current_year,
            'gross_pay': f"{ytd_gross:.2f}",
            'net_pay': f"{ytd_net:.2f}",
            'total_paystubs': Paystub.query.filter_by(user_id=current_user.id).count()
        },
        'employees': employee_cards,
        'rewards': {
            'total_points': total_rewards,
            'current_tier': tier,
            'paystubs_to_next_tier': 100 - paystub_count if paystub_count < 100 else 0
        },
        'activity_feed': activity_feed
    }), 200
