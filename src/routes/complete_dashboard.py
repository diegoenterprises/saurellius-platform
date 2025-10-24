from flask import Blueprint, jsonify, request, session
from src.models.complete_models import User, Employee, Paystub, RewardActivity, Company
from src.models.database import db
from datetime import datetime, date
from sqlalchemy import func, desc
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """Get comprehensive dashboard summary with YTD tracking"""
    
    # Get user from session (in production, use proper authentication)
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get current year
    current_year = datetime.now().year
    
    # Calculate YTD totals across all employees
    ytd_totals = db.session.query(
        func.count(Paystub.id).label('total_paystubs'),
        func.sum(Paystub.gross_pay).label('ytd_gross'),
        func.sum(Paystub.net_pay).label('ytd_net'),
        func.sum(Paystub.federal_income_tax).label('ytd_federal_tax'),
        func.sum(Paystub.social_security_tax).label('ytd_social_security'),
        func.sum(Paystub.medicare_tax).label('ytd_medicare'),
        func.sum(Paystub.state_income_tax).label('ytd_state_tax')
    ).filter(
        Paystub.user_id == user_id,
        func.extract('year', Paystub.pay_date) == current_year,
        Paystub.is_voided == False
    ).first()
    
    # Calculate average net pay
    average_net = 0
    if ytd_totals.total_paystubs and ytd_totals.total_paystubs > 0:
        average_net = float(ytd_totals.ytd_net or 0) / ytd_totals.total_paystubs
    
    # Get reward tier information
    reward_tier_info = get_reward_tier_info(user.reward_points)
    
    # Get recent activity
    recent_activities = get_recent_activities(user_id)
    
    summary = {
        'user': {
            'full_name': user.full_name,
            'email': user.email,
            'subscription_tier': user.subscription_tier,
            'subscription_status': user.subscription_status
        },
        'ytd_overview': {
            'total_paystubs': ytd_totals.total_paystubs or 0,
            'ytd_gross': float(ytd_totals.ytd_gross or 0),
            'ytd_net': float(ytd_totals.ytd_net or 0),
            'average_net': round(average_net, 2),
            'ytd_federal_tax': float(ytd_totals.ytd_federal_tax or 0),
            'ytd_social_security': float(ytd_totals.ytd_social_security or 0),
            'ytd_medicare': float(ytd_totals.ytd_medicare or 0),
            'ytd_state_tax': float(ytd_totals.ytd_state_tax or 0)
        },
        'rewards': {
            'current_tier': reward_tier_info['current_tier'],
            'points': user.reward_points,
            'next_tier': reward_tier_info['next_tier'],
            'points_needed': reward_tier_info['points_needed'],
            'progress_percentage': reward_tier_info['progress_percentage']
        },
        'recent_activities': recent_activities
    }
    
    return jsonify(summary)

@dashboard_bp.route('/employees', methods=['GET'])
def get_employee_cards():
    """Get employee cards with individual YTD tracking and next suggested pay dates"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    employees = Employee.query.filter_by(user_id=user_id, is_active=True).all()
    employee_cards = []
    
    current_year = datetime.now().year
    
    for employee in employees:
        # Get last paystub
        last_paystub = Paystub.query.filter_by(
            employee_id=employee.id,
            is_voided=False
        ).order_by(desc(Paystub.pay_date)).first()
        
        # Calculate YTD totals for this employee
        ytd_query = db.session.query(
            func.count(Paystub.id).label('paystub_count'),
            func.sum(Paystub.gross_pay).label('ytd_gross'),
            func.sum(Paystub.net_pay).label('ytd_net'),
            func.sum(Paystub.federal_income_tax).label('ytd_federal_tax'),
            func.sum(Paystub.state_income_tax).label('ytd_state_tax')
        ).filter(
            Paystub.employee_id == employee.id,
            func.extract('year', Paystub.pay_date) == current_year,
            Paystub.is_voided == False
        ).first()
        
        # Calculate next suggested pay date
        next_pay_date = calculate_next_pay_date(employee.pay_frequency, last_paystub.pay_date if last_paystub else None)
        
        employee_card = {
            'employee_id': employee.id,
            'name': employee.full_name,
            'employment_type': employee.employment_type,
            'pay_frequency': employee.pay_frequency,
            'last_paystub': {
                'number': last_paystub.paystub_number if last_paystub else 0,
                'pay_date': last_paystub.pay_date.isoformat() if last_paystub else None,
                'gross': float(last_paystub.gross_pay) if last_paystub else 0,
                'net': float(last_paystub.net_pay) if last_paystub else 0
            },
            'ytd_summary': {
                'paystub_count': ytd_query.paystub_count or 0,
                'gross': float(ytd_query.ytd_gross or 0),
                'net': float(ytd_query.ytd_net or 0),
                'federal_tax': float(ytd_query.ytd_federal_tax or 0),
                'state_tax': float(ytd_query.ytd_state_tax or 0)
            },
            'next_suggested_pay_date': next_pay_date.isoformat() if next_pay_date else None,
            'quick_actions': [
                'generate_next',
                'view_history',
                'download_last_4',
                'edit_info'
            ]
        }
        
        employee_cards.append(employee_card)
    
    return jsonify({'employees': employee_cards})

@dashboard_bp.route('/rewards/activities', methods=['GET'])
def get_reward_activities():
    """Get recent reward activities for the rewards widget"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Get recent reward activities
    activities = RewardActivity.query.filter_by(user_id=user_id)\
        .order_by(desc(RewardActivity.created_at))\
        .limit(10).all()
    
    activity_list = []
    for activity in activities:
        activity_list.append({
            'description': activity.description,
            'points': activity.points_awarded,
            'date': activity.created_at.isoformat(),
            'type': activity.activity_type
        })
    
    return jsonify({'activities': activity_list})

@dashboard_bp.route('/monthly-stats', methods=['GET'])
def get_monthly_stats():
    """Get monthly breakdown for charts and analytics"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_year = datetime.now().year
    
    # Get monthly totals
    monthly_stats = []
    for month in range(1, 13):
        month_data = db.session.query(
            func.count(Paystub.id).label('paystub_count'),
            func.sum(Paystub.gross_pay).label('gross_total'),
            func.sum(Paystub.net_pay).label('net_total')
        ).filter(
            Paystub.user_id == user_id,
            func.extract('year', Paystub.pay_date) == current_year,
            func.extract('month', Paystub.pay_date) == month,
            Paystub.is_voided == False
        ).first()
        
        monthly_stats.append({
            'month': calendar.month_name[month],
            'month_number': month,
            'paystub_count': month_data.paystub_count or 0,
            'gross_total': float(month_data.gross_total or 0),
            'net_total': float(month_data.net_total or 0)
        })
    
    return jsonify({'monthly_stats': monthly_stats})

def get_reward_tier_info(points):
    """Calculate reward tier information based on points"""
    
    tiers = [
        {'name': 'Bronze', 'min_points': 0, 'max_points': 499},
        {'name': 'Silver', 'min_points': 500, 'max_points': 999},
        {'name': 'Gold', 'min_points': 1000, 'max_points': 1499},
        {'name': 'Platinum', 'min_points': 1500, 'max_points': float('inf')}
    ]
    
    current_tier = None
    next_tier = None
    
    for i, tier in enumerate(tiers):
        if tier['min_points'] <= points <= tier['max_points']:
            current_tier = tier['name']
            if i < len(tiers) - 1:
                next_tier = tiers[i + 1]['name']
                points_needed = tiers[i + 1]['min_points'] - points
                progress_percentage = int((points - tier['min_points']) / (tiers[i + 1]['min_points'] - tier['min_points']) * 100)
            else:
                next_tier = None
                points_needed = 0
                progress_percentage = 100
            break
    
    return {
        'current_tier': current_tier or 'Bronze',
        'next_tier': next_tier,
        'points_needed': points_needed if next_tier else 0,
        'progress_percentage': progress_percentage if next_tier else 100
    }

def get_recent_activities(user_id, limit=5):
    """Get recent user activities for the dashboard"""
    
    activities = []
    
    # Recent paystubs
    recent_paystubs = Paystub.query.filter_by(user_id=user_id, is_voided=False)\
        .order_by(desc(Paystub.created_at))\
        .limit(3).all()
    
    for paystub in recent_paystubs:
        employee = Employee.query.get(paystub.employee_id)
        activities.append({
            'type': 'paystub_generated',
            'description': f'Paystub #{paystub.paystub_number} generated for {employee.full_name}',
            'date': paystub.created_at.isoformat(),
            'icon': '📄'
        })
    
    # Recent reward activities
    recent_rewards = RewardActivity.query.filter_by(user_id=user_id)\
        .order_by(desc(RewardActivity.created_at))\
        .limit(2).all()
    
    for reward in recent_rewards:
        activities.append({
            'type': 'reward_earned',
            'description': f'{reward.description} (+{reward.points_awarded} pts)',
            'date': reward.created_at.isoformat(),
            'icon': '🏆'
        })
    
    # Sort by date and limit
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:limit]

def calculate_next_pay_date(pay_frequency, last_pay_date):
    """Calculate the next suggested pay date based on frequency"""
    
    if not last_pay_date:
        return datetime.now().date()
    
    from datetime import timedelta
    
    if pay_frequency == 'Weekly':
        return last_pay_date + timedelta(days=7)
    elif pay_frequency == 'BiWeekly':
        return last_pay_date + timedelta(days=14)
    elif pay_frequency == 'SemiMonthly':
        # 15th and last day of month logic
        if last_pay_date.day <= 15:
            # Next pay is last day of month
            next_month = last_pay_date.replace(day=28)
            return next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1])
        else:
            # Next pay is 15th of next month
            if last_pay_date.month == 12:
                return date(last_pay_date.year + 1, 1, 15)
            else:
                return date(last_pay_date.year, last_pay_date.month + 1, 15)
    elif pay_frequency == 'Monthly':
        # Same day next month
        if last_pay_date.month == 12:
            return date(last_pay_date.year + 1, 1, last_pay_date.day)
        else:
            try:
                return date(last_pay_date.year, last_pay_date.month + 1, last_pay_date.day)
            except ValueError:
                # Handle month-end dates (e.g., Jan 31 -> Feb 28)
                return date(last_pay_date.year, last_pay_date.month + 1, 
                          calendar.monthrange(last_pay_date.year, last_pay_date.month + 1)[1])
    
    return last_pay_date + timedelta(days=14)  # Default to bi-weekly

@dashboard_bp.route('/pro-tips', methods=['GET'])
def get_pro_tips():
    """Get contextual pro tips for the dashboard"""
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    paystub_count = Paystub.query.filter_by(user_id=user_id, is_voided=False).count()
    
    tips = []
    
    if paystub_count == 0:
        tips.append("🚀 Generate your first paystub to start building your employment history!")
    elif paystub_count < 3:
        tips.append("📄 Keep generating paystubs to build a complete 3-month history for apartment applications.")
    else:
        tips.append("✅ You have enough paystubs for most apartment applications. Keep them updated!")
    
    if not user.two_factor_enabled:
        tips.append("🔒 Enable 2FA in settings for enhanced security of your financial documents.")
    
    if user.subscription_tier == 'starter':
        tips.append("⭐ Upgrade to Professional for premium templates and priority support.")
    
    tips.append("💡 Use 'Continue from Last' to maintain perfect YTD accuracy across paystubs.")
    tips.append("📊 Download your last 4 paystubs as a ZIP file for quick apartment applications.")
    
    return jsonify({'tips': tips[:3]})  # Return max 3 tips
