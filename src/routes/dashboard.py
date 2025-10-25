from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User, Employee, Paystub, RewardActivity, Company
from src.routes.auth import token_required
from sqlalchemy import func, extract, desc
from datetime import datetime, date
from decimal import Decimal

dashboard_bp = Blueprint('dashboard', __name__)

def calculate_reward_tier_progress(points):
    """Calculate reward tier and progress to next tier"""
    tiers = {
        'bronze': {'min': 0, 'max': 500, 'next': 'silver'},
        'silver': {'min': 500, 'max': 1000, 'next': 'gold'},
        'gold': {'min': 1000, 'max': 1500, 'next': 'platinum'},
        'platinum': {'min': 1500, 'max': float('inf'), 'next': None}
    }
    
    for tier_name, tier_info in tiers.items():
        if tier_info['min'] <= points < tier_info['max']:
            if tier_info['next']:
                points_to_next = tier_info['max'] - points
                progress_percentage = int(((points - tier_info['min']) / (tier_info['max'] - tier_info['min'])) * 100)
            else:
                points_to_next = 0
                progress_percentage = 100
            
            return {
                'current_tier': tier_name.title(),
                'next_tier': tier_info['next'].title() if tier_info['next'] else None,
                'points_to_next': points_to_next,
                'progress_percentage': progress_percentage
            }
    
    return {
        'current_tier': 'Bronze',
        'next_tier': 'Silver',
        'points_to_next': 500,
        'progress_percentage': 0
    }


@dashboard_bp.route('/summary', methods=['GET'])
@token_required
def get_dashboard_summary(current_user):
    """Get comprehensive dashboard summary with YTD stats, employees, and rewards"""
    
    current_year = datetime.now().year
    
    # 1. Comprehensive YTD Summary
    ytd_data = db.session.query(
        func.count(Paystub.id).label('total_paystubs'),
        func.sum(Paystub.gross_pay).label('ytd_gross'),
        func.sum(Paystub.net_pay).label('ytd_net'),
        func.sum(Paystub.federal_income_tax).label('ytd_federal_tax'),
        func.sum(Paystub.social_security_tax).label('ytd_social_security'),
        func.sum(Paystub.medicare_tax).label('ytd_medicare'),
        func.sum(Paystub.state_income_tax).label('ytd_state_tax')
    ).filter(
        Paystub.user_id == current_user.id,
        extract('year', Paystub.pay_date) == current_year,
        Paystub.is_void == False
    ).first()
    
    total_paystubs = ytd_data.total_paystubs if ytd_data.total_paystubs else 0
    ytd_gross = float(ytd_data.ytd_gross) if ytd_data.ytd_gross else 0.0
    ytd_net = float(ytd_data.ytd_net) if ytd_data.ytd_net else 0.0
    ytd_federal_tax = float(ytd_data.ytd_federal_tax) if ytd_data.ytd_federal_tax else 0.0
    ytd_social_security = float(ytd_data.ytd_social_security) if ytd_data.ytd_social_security else 0.0
    ytd_medicare = float(ytd_data.ytd_medicare) if ytd_data.ytd_medicare else 0.0
    ytd_state_tax = float(ytd_data.ytd_state_tax) if ytd_data.ytd_state_tax else 0.0
    
    average_net = ytd_net / total_paystubs if total_paystubs > 0 else 0.0
    
    # 2. Employee Cards with quick actions
    employees = Employee.query.filter_by(user_id=current_user.id, is_active=True).all()
    employee_cards = []
    
    for emp in employees:
        # Get last paystub for this employee
        last_paystub = Paystub.query.filter_by(
            employee_id=emp.id,
            is_void=False
        ).order_by(desc(Paystub.pay_date)).first()
        
        # Get employee YTD for current year
        emp_ytd = db.session.query(
            func.sum(Paystub.gross_pay).label('ytd_gross'),
            func.sum(Paystub.net_pay).label('ytd_net'),
            func.sum(Paystub.federal_income_tax).label('ytd_federal'),
            func.sum(Paystub.state_income_tax).label('ytd_state')
        ).filter(
            Paystub.employee_id == emp.id,
            extract('year', Paystub.pay_date) == current_year,
            Paystub.is_void == False
        ).first()
        
        # Calculate next suggested pay date based on pay frequency
        next_pay_date = None
        if last_paystub:
            from datetime import timedelta
            pay_date = last_paystub.pay_date
            
            if emp.pay_frequency == 'Weekly':
                next_pay_date = pay_date + timedelta(days=7)
            elif emp.pay_frequency == 'BiWeekly':
                next_pay_date = pay_date + timedelta(days=14)
            elif emp.pay_frequency == 'SemiMonthly':
                # Logic from deployment guide
                if pay_date.day == 15:
                    # Go to last day of current month
                    next_month = pay_date.replace(day=28) + timedelta(days=4)
                    next_pay_date = next_month.replace(day=1) - timedelta(days=1)
                else:
                    # Go to 15th of next month
                    if pay_date.month == 12:
                        next_pay_date = pay_date.replace(year=pay_date.year + 1, month=1, day=15)
                    else:
                        next_pay_date = pay_date.replace(month=pay_date.month + 1, day=15)
            elif emp.pay_frequency == 'Monthly':
                # Logic from deployment guide
                if pay_date.month == 12:
                    next_pay_date = pay_date.replace(year=pay_date.year + 1, month=1, day=pay_date.day)
                else:
                    # Handle day in month overflow (e.g. 31st to Feb)
                    try:
                        next_pay_date = pay_date.replace(month=pay_date.month + 1)
                    except ValueError:
                        # Go to last day of next month
                        next_month = pay_date.replace(day=28) + timedelta(days=4)
                        next_pay_date = next_month.replace(day=1) - timedelta(days=1)
        
        employee_cards.append({
            'employee_id': emp.id,
            'name': emp.get_full_name(),
            'last_paystub': {
                'number': last_paystub.paystub_number if last_paystub else 0,
                'pay_date': last_paystub.pay_date.isoformat() if last_paystub else None,
                'gross': float(last_paystub.gross_pay) if last_paystub else 0.0,
                'net': float(last_paystub.net_pay) if last_paystub else 0.0
            } if last_paystub else None,
            'ytd_summary': {
                'gross': float(emp_ytd.ytd_gross) if emp_ytd.ytd_gross else 0.0,
                'net': float(emp_ytd.ytd_net) if emp_ytd.ytd_net else 0.0,
                'federal_tax': float(emp_ytd.ytd_federal) if emp_ytd.ytd_federal else 0.0,
                'state_tax': float(emp_ytd.ytd_state) if emp_ytd.ytd_state else 0.0
            },
            'next_suggested_pay_date': next_pay_date.isoformat() if next_pay_date else None,
            'pay_frequency': emp.pay_frequency,
            'state': emp.address_state
        })
    
    # 3. Rewards Widget
    reward_tier_info = calculate_reward_tier_progress(current_user.reward_points)
    
    # Get recent reward activities
    recent_activities = RewardActivity.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(RewardActivity.timestamp)).limit(5).all()
    
    recent_activities_list = [{
        'action': activity.description or activity.type,
        'points': activity.points_awarded,
        'date': activity.timestamp.isoformat()
    } for activity in recent_activities]
    
    # Calculate achievements
    achievements = [
        {
            'name': 'First Paystub',
            'unlocked': total_paystubs >= 1,
            'description': 'Generate your first paystub'
        },
        {
            'name': '10 Paystubs',
            'unlocked': total_paystubs >= 10,
            'description': 'Generate 10 paystubs'
        },
        {
            'name': '25 Paystubs',
            'unlocked': total_paystubs >= 25,
            'description': 'Generate 25 paystubs'
        },
        {
            'name': '50 Paystubs',
            'unlocked': total_paystubs >= 50,
            'description': 'Generate 50 paystubs'
        },
        {
            'name': 'Silver Tier',
            'unlocked': current_user.reward_points >= 500,
            'description': 'Reach Silver reward tier'
        },
        {
            'name': 'Gold Tier',
            'unlocked': current_user.reward_points >= 1000,
            'description': 'Reach Gold reward tier'
        },
        {
            'name': 'Platinum Tier',
            'unlocked': current_user.reward_points >= 1500,
            'description': 'Reach Platinum reward tier'
        }
    ]
    
    rewards_widget = {
        'current_tier': reward_tier_info['current_tier'],
        'points': current_user.reward_points,
        'next_tier': reward_tier_info['next_tier'],
        'points_needed': reward_tier_info['points_to_next'],
        'progress_percentage': reward_tier_info['progress_percentage'],
        'recent_activities': recent_activities_list,
        'achievements': achievements
    }
    
    # 4. Recent Activity Feed
    recent_paystubs = Paystub.query.filter_by(
        user_id=current_user.id,
        is_void=False
    ).order_by(desc(Paystub.created_at)).limit(5).all()
    
    activity_feed = []
    for ps in recent_paystubs:
        employee = Employee.query.get(ps.employee_id)
        activity_feed.append({
            'type': 'paystub_generated',
            'description': f'Paystub #{ps.paystub_number} generated for {employee.get_full_name() if employee else "employee"}',
            'timestamp': ps.created_at.isoformat(),
            'paystub_id': ps.id
        })
    
    # 5. Quick Stats
    quick_stats = {
        'total_employees': len(employees),
        'active_subscription': current_user.subscription_tier,
        'subscription_status': current_user.subscription_status,
        'paystubs_this_month': Paystub.query.filter(
            Paystub.user_id == current_user.id,
            extract('year', Paystub.pay_date) == current_year,
            extract('month', Paystub.pay_date) == datetime.now().month,
            Paystub.is_void == False
        ).count()
    }
    
    return jsonify({
        'dashboard_summary': {
            'total_paystubs': total_paystubs,
            'ytd_gross': ytd_gross,
            'ytd_net': ytd_net,
            'average_net': average_net,
            'ytd_federal_tax': ytd_federal_tax,
            'ytd_social_security': ytd_social_security,
            'ytd_medicare': ytd_medicare,
            'ytd_state_tax': ytd_state_tax
        },
        'employee_cards': employee_cards,
        'rewards_widget': rewards_widget,
        'activity_feed': activity_feed,
        'quick_stats': quick_stats,
        'user': current_user.to_dict()
    }), 200


@dashboard_bp.route('/employees', methods=['GET'])
@token_required
def get_employees(current_user):
    """Get all employees for the current user"""
    employees = Employee.query.filter_by(user_id=current_user.id).all()
    
    employee_list = []
    for emp in employees:
        employee_list.append({
            'id': emp.id,
            'uuid': emp.uuid,
            'name': emp.get_full_name(),
            'first_name': emp.first_name,
            'last_name': emp.last_name,
            'email': emp.email,
            'phone': emp.phone,
            'address_state': emp.address_state,
            'pay_frequency': emp.pay_frequency,
            'employment_type': emp.employment_type,
            'pay_structure': emp.pay_structure,
            'hourly_rate': float(emp.hourly_rate) if emp.hourly_rate else None,
            'annual_salary': float(emp.annual_salary) if emp.annual_salary else None,
            'is_active': emp.is_active,
            'hire_date': emp.hire_date.isoformat() if emp.hire_date else None,
            'ytd_gross': float(emp.ytd_gross) if emp.ytd_gross else 0.0,
            'ytd_net': float(emp.ytd_net) if emp.ytd_net else 0.0
        })
    
    return jsonify({'employees': employee_list}), 200


@dashboard_bp.route('/recent-activity', methods=['GET'])
@token_required
def get_recent_activity(current_user):
    """Get recent activity for the dashboard"""
    
    # Get recent paystubs
    recent_paystubs = Paystub.query.filter_by(
        user_id=current_user.id,
        is_void=False
    ).order_by(desc(Paystub.created_at)).limit(10).all()
    
    activities = []
    for ps in recent_paystubs:
        employee = Employee.query.get(ps.employee_id)
        activities.append({
            'id': ps.id,
            'type': 'paystub_generated',
            'description': f'Paystub #{ps.paystub_number} generated for {employee.get_full_name() if employee else "employee"}',
            'timestamp': ps.created_at.isoformat(),
            'details': {
                'paystub_id': ps.id,
                'employee_name': employee.get_full_name() if employee else None,
                'gross_pay': float(ps.gross_pay),
                'net_pay': float(ps.net_pay),
                'pay_date': ps.pay_date.isoformat()
            }
        })
    
    # Get recent reward activities
    recent_rewards = RewardActivity.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(RewardActivity.timestamp)).limit(10).all()
    
    for reward in recent_rewards:
        activities.append({
            'id': reward.id,
            'type': 'reward_earned',
            'description': reward.description or f'{reward.type} - {reward.points_awarded} points',
            'timestamp': reward.timestamp.isoformat(),
            'details': {
                'points': reward.points_awarded,
                'reward_type': reward.type
            }
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({'activities': activities[:20]}), 200


@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get detailed statistics for charts and graphs"""
    
    current_year = datetime.now().year
    
    # Monthly breakdown for current year
    monthly_stats = []
    for month in range(1, 13):
        month_data = db.session.query(
            func.count(Paystub.id).label('count'),
            func.sum(Paystub.gross_pay).label('gross'),
            func.sum(Paystub.net_pay).label('net')
        ).filter(
            Paystub.user_id == current_user.id,
            extract('year', Paystub.pay_date) == current_year,
            extract('month', Paystub.pay_date) == month,
            Paystub.is_void == False
        ).first()
        
        monthly_stats.append({
            'month': month,
            'month_name': date(current_year, month, 1).strftime('%B'),
            'paystub_count': month_data.count if month_data.count else 0,
            'gross_pay': float(month_data.gross) if month_data.gross else 0.0,
            'net_pay': float(month_data.net) if month_data.net else 0.0
        })
    
    return jsonify({
        'monthly_stats': monthly_stats,
        'current_year': current_year
    }), 200

