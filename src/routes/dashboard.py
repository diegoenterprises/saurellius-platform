"""
Dashboard Routes with YTD Tracking and Intelligent Continuation
Provides comprehensive user dashboard with summary statistics and quick actions
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.models.database import User, Employee, Paystub, RewardActivity, db
from src.routes.auth import token_required
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
@token_required
def get_dashboard_summary(current_user):
    """Get comprehensive dashboard summary for current user"""
    try:
        # Get all employees for this user
        employees = Employee.query.filter_by(user_id=current_user.id).all()
        
        if not employees:
            return jsonify({
                'summary': {
                    'total_paystubs': 0,
                    'ytd_gross': 0,
                    'ytd_net': 0,
                    'average_net': 0,
                    'ytd_federal_tax': 0,
                    'ytd_social_security': 0,
                    'ytd_medicare': 0,
                    'ytd_state_tax': 0,
                    'current_tier': current_user.reward_tier,
                    'reward_points': current_user.reward_points,
                    'next_tier_progress': 0,
                    'employees': []
                }
            }), 200
        
        # Aggregate YTD data from all employees
        total_paystubs = Paystub.query.filter_by(user_id=current_user.id).count()
        
        ytd_data = db.session.query(
            func.sum(Employee.ytd_gross).label('ytd_gross'),
            func.sum(Employee.ytd_net).label('ytd_net'),
            func.sum(Employee.ytd_federal_tax).label('ytd_federal_tax'),
            func.sum(Employee.ytd_social_security).label('ytd_social_security'),
            func.sum(Employee.ytd_medicare).label('ytd_medicare'),
            func.sum(Employee.ytd_state_tax).label('ytd_state_tax')
        ).filter(Employee.user_id == current_user.id).first()
        
        ytd_gross = float(ytd_data.ytd_gross) if ytd_data.ytd_gross else 0
        ytd_net = float(ytd_data.ytd_net) if ytd_data.ytd_net else 0
        average_net = ytd_net / total_paystubs if total_paystubs > 0 else 0
        
        # Calculate reward tier progress
        tier_thresholds = {
            'bronze': 0,
            'silver': 500,
            'gold': 1000,
            'platinum': 1500
        }
        
        current_points = current_user.reward_points
        current_tier = current_user.reward_tier
        
        # Find next tier
        next_tier = None
        next_threshold = None
        for tier, threshold in sorted(tier_thresholds.items(), key=lambda x: x[1]):
            if threshold > tier_thresholds.get(current_tier, 0):
                next_tier = tier
                next_threshold = threshold
                break
        
        if next_tier and next_threshold:
            progress = ((current_points - tier_thresholds.get(current_tier, 0)) / 
                       (next_threshold - tier_thresholds.get(current_tier, 0))) * 100
            progress = min(100, max(0, progress))
        else:
            progress = 100
        
        # Build employee cards
        employee_cards = []
        for emp in employees:
            last_paystub = Paystub.query.filter_by(
                employee_id=emp.id
            ).order_by(Paystub.pay_date.desc()).first()
            
            # Calculate next suggested pay date
            if emp.pay_frequency == 'weekly':
                days_offset = 7
            elif emp.pay_frequency == 'biweekly':
                days_offset = 14
            elif emp.pay_frequency == 'semimonthly':
                days_offset = 15
            else:  # monthly
                days_offset = 30
            
            next_pay_date = None
            if last_paystub:
                next_pay_date = (last_paystub.pay_date + 
                               __import__('datetime').timedelta(days=days_offset))
            
            employee_cards.append({
                'id': emp.id,
                'name': emp.name,
                'employer_name': emp.employer_name,
                'pay_frequency': emp.pay_frequency,
                'last_paystub': {
                    'number': emp.last_paystub_number,
                    'pay_date': emp.last_paystub_date.isoformat() if emp.last_paystub_date else None,
                    'gross': float(last_paystub.gross_pay) if last_paystub else None,
                    'net': float(last_paystub.net_pay) if last_paystub else None
                } if last_paystub else None,
                'ytd_summary': {
                    'gross': float(emp.ytd_gross),
                    'net': float(emp.ytd_net),
                    'federal_tax': float(emp.ytd_federal_tax),
                    'state_tax': float(emp.ytd_state_tax),
                    'social_security': float(emp.ytd_social_security),
                    'medicare': float(emp.ytd_medicare)
                },
                'next_suggested_pay_date': next_pay_date.isoformat() if next_pay_date else None,
                'quick_actions': [
                    'generate_next',
                    'view_history',
                    'download_last_4',
                    'edit_info'
                ]
            })
        
        return jsonify({
            'summary': {
                'total_paystubs': total_paystubs,
                'ytd_gross': ytd_gross,
                'ytd_net': ytd_net,
                'average_net': average_net,
                'ytd_federal_tax': float(ytd_data.ytd_federal_tax) if ytd_data.ytd_federal_tax else 0,
                'ytd_social_security': float(ytd_data.ytd_social_security) if ytd_data.ytd_social_security else 0,
                'ytd_medicare': float(ytd_data.ytd_medicare) if ytd_data.ytd_medicare else 0,
                'ytd_state_tax': float(ytd_data.ytd_state_tax) if ytd_data.ytd_state_tax else 0,
                'current_tier': current_user.reward_tier,
                'reward_points': current_user.reward_points,
                'next_tier': next_tier,
                'next_tier_progress': progress,
                'employees': employee_cards
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/rewards', methods=['GET'])
@token_required
def get_rewards_widget(current_user):
    """Get rewards and gamification widget"""
    try:
        # Get recent activities
        recent_activities = RewardActivity.query.filter_by(
            user_id=current_user.id
        ).order_by(RewardActivity.created_at.desc()).limit(10).all()
        
        # Define achievements
        total_paystubs = Paystub.query.filter_by(user_id=current_user.id).count()
        
        achievements = [
            {
                'name': 'First Paystub',
                'description': 'Generate your first paystub',
                'unlocked': total_paystubs >= 1,
                'icon': '🎯'
            },
            {
                'name': '5 Paystubs',
                'description': 'Generate 5 paystubs',
                'unlocked': total_paystubs >= 5,
                'icon': '⭐'
            },
            {
                'name': '10 Paystubs',
                'description': 'Generate 10 paystubs',
                'unlocked': total_paystubs >= 10,
                'icon': '🏆'
            },
            {
                'name': '25 Paystubs',
                'description': 'Generate 25 paystubs',
                'unlocked': total_paystubs >= 25,
                'icon': '👑'
            },
            {
                'name': 'Gold Tier',
                'description': 'Reach Gold reward tier',
                'unlocked': current_user.reward_tier in ['gold', 'platinum'],
                'icon': '🥇'
            },
            {
                'name': 'Platinum Tier',
                'description': 'Reach Platinum reward tier',
                'unlocked': current_user.reward_tier == 'platinum',
                'icon': '💎'
            }
        ]
        
        # Calculate tier progress
        tier_thresholds = {
            'bronze': 0,
            'silver': 500,
            'gold': 1000,
            'platinum': 1500
        }
        
        current_tier = current_user.reward_tier
        current_points = current_user.reward_points
        
        next_tier = None
        next_threshold = None
        for tier, threshold in sorted(tier_thresholds.items(), key=lambda x: x[1]):
            if threshold > tier_thresholds.get(current_tier, 0):
                next_tier = tier
                next_threshold = threshold
                break
        
        points_needed = (next_threshold - current_points) if next_tier and next_threshold else 0
        
        return jsonify({
            'rewards': {
                'current_tier': current_user.reward_tier,
                'points': current_user.reward_points,
                'total_lifetime_points': current_user.total_lifetime_points,
                'next_tier': next_tier,
                'points_needed': max(0, points_needed),
                'progress_percentage': min(100, ((current_points - tier_thresholds.get(current_tier, 0)) / 
                                                (next_threshold - tier_thresholds.get(current_tier, 0)) * 100)) if next_tier else 100,
                'recent_activities': [
                    {
                        'action': activity.description,
                        'points': activity.points_earned,
                        'date': activity.created_at.isoformat()
                    } for activity in recent_activities
                ],
                'achievements': achievements
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/ytd-summary/<int:employee_id>', methods=['GET'])
@token_required
def get_ytd_summary(current_user, employee_id):
    """Get detailed YTD summary for an employee"""
    try:
        employee = Employee.query.filter_by(
            id=employee_id,
            user_id=current_user.id
        ).first()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get all paystubs for the year
        paystubs = Paystub.query.filter_by(
            employee_id=employee_id
        ).order_by(Paystub.pay_date).all()
        
        return jsonify({
            'ytd_summary': {
                'employee_name': employee.name,
                'year': date.today().year,
                'total_paystubs': len(paystubs),
                'ytd_gross': float(employee.ytd_gross),
                'ytd_net': float(employee.ytd_net),
                'ytd_federal_tax': float(employee.ytd_federal_tax),
                'ytd_state_tax': float(employee.ytd_state_tax),
                'ytd_social_security': float(employee.ytd_social_security),
                'ytd_medicare': float(employee.ytd_medicare),
                'paystub_details': [
                    {
                        'number': p.paystub_number,
                        'pay_date': p.pay_date.isoformat(),
                        'gross': float(p.gross_pay),
                        'net': float(p.net_pay),
                        'federal_tax': float(p.federal_income_tax),
                        'state_tax': float(p.state_income_tax)
                    } for p in paystubs
                ]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/recent-activity', methods=['GET'])
@token_required
def get_recent_activity(current_user):
    """Get recent user activity"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        activities = []
        
        # Get recent paystubs
        recent_paystubs = Paystub.query.filter_by(
            user_id=current_user.id
        ).order_by(Paystub.created_at.desc()).limit(limit).all()
        
        for paystub in recent_paystubs:
            activities.append({
                'type': 'paystub_generated',
                'description': f'Generated paystub #{paystub.paystub_number}',
                'timestamp': paystub.created_at.isoformat(),
                'metadata': {
                    'paystub_id': paystub.id,
                    'gross_pay': float(paystub.gross_pay)
                }
            })
        
        # Get recent reward activities
        reward_activities = RewardActivity.query.filter_by(
            user_id=current_user.id
        ).order_by(RewardActivity.created_at.desc()).limit(limit).all()
        
        for activity in reward_activities:
            activities.append({
                'type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.created_at.isoformat(),
                'points': activity.points_earned
            })
        
        # Sort by timestamp
        activities = sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        return jsonify({
            'recent_activity': activities
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

