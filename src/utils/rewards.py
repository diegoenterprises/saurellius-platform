"""
Rewards and Gamification System
Handles point awards, tier progression, and achievements
"""

from src.models.user import User, RewardActivity
from src.models.database import db
from datetime import datetime, date, timedelta


# Reward Points Configuration
POINTS_CONFIG = {
    'paystub_generated': 50,
    'first_paystub': 100,
    'login_streak_3': 15,
    'login_streak_7': 25,
    'login_streak_30': 50,
    'profile_completed': 25,
    'referral': 100,
    'milestone_10_paystubs': 100,
    'milestone_25_paystubs': 250,
    'milestone_50_paystubs': 500,
    'milestone_100_paystubs': 1000
}

# Tier Thresholds
TIER_THRESHOLDS = {
    'bronze': 0,
    'silver': 500,
    'gold': 1000,
    'platinum': 1500
}


def award_points(user_id, activity_type, description=None, custom_points=None):
    """Award points to a user for an activity"""
    user = User.query.get(user_id)
    if not user:
        return False
    
    # Determine points to award
    points = custom_points if custom_points else POINTS_CONFIG.get(activity_type, 0)
    
    # Create reward activity record
    reward_activity = RewardActivity(
        user_id=user_id,
        type=activity_type,
        points_awarded=points,
        description=description or activity_type.replace('_', ' ').title(),
        timestamp=datetime.utcnow()
    )
    
    # Update user points
    user.reward_points += points
    user.total_lifetime_points += points
    
    # Check for tier upgrade
    new_tier = calculate_tier(user.reward_points)
    if new_tier != user.reward_tier:
        old_tier = user.reward_tier
        user.reward_tier = new_tier
        
        # Award bonus points for tier upgrade
        tier_bonus = RewardActivity(
            user_id=user_id,
            type='tier_upgrade',
            points_awarded=50,
            description=f'Upgraded from {old_tier.title()} to {new_tier.title()}!',
            timestamp=datetime.utcnow()
        )
        user.reward_points += 50
        user.total_lifetime_points += 50
        db.session.add(tier_bonus)
    
    db.session.add(reward_activity)
    db.session.commit()
    
    return True


def calculate_tier(points):
    """Calculate reward tier based on points"""
    if points >= TIER_THRESHOLDS['platinum']:
        return 'platinum'
    elif points >= TIER_THRESHOLDS['gold']:
        return 'gold'
    elif points >= TIER_THRESHOLDS['silver']:
        return 'silver'
    else:
        return 'bronze'


def check_and_award_milestones(user_id, paystub_count):
    """Check if user has reached any milestones and award points"""
    milestones = [
        (1, 'first_paystub', 'Generated your first paystub!'),
        (10, 'milestone_10_paystubs', 'Generated 10 paystubs!'),
        (25, 'milestone_25_paystubs', 'Generated 25 paystubs!'),
        (50, 'milestone_50_paystubs', 'Generated 50 paystubs!'),
        (100, 'milestone_100_paystubs', 'Generated 100 paystubs!')
    ]
    
    for count, activity_type, description in milestones:
        if paystub_count == count:
            award_points(user_id, activity_type, description)


def check_login_streak(user_id):
    """Check and update login streak, award points if applicable"""
    user = User.query.get(user_id)
    if not user:
        return
    
    today = date.today()
    last_login_date = user.last_login_streak_date
    
    if last_login_date:
        days_since_last = (today - last_login_date).days
        
        if days_since_last == 1:
            # Consecutive day - increment streak
            user.login_streak += 1
        elif days_since_last > 1:
            # Streak broken - reset
            user.login_streak = 1
        # else: same day, no change
    else:
        # First login tracking
        user.login_streak = 1
    
    user.last_login_streak_date = today
    user.last_login = datetime.utcnow()
    
    # Award points for streaks
    if user.login_streak == 3:
        award_points(user_id, 'login_streak_3', '3-day login streak!')
    elif user.login_streak == 7:
        award_points(user_id, 'login_streak_7', '7-day login streak!')
    elif user.login_streak == 30:
        award_points(user_id, 'login_streak_30', '30-day login streak!')
    
    db.session.commit()


def get_user_achievements(user_id):
    """Get all achievements and their unlock status for a user"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get paystub count
    from src.models.user import Paystub
    paystub_count = Paystub.query.filter_by(user_id=user_id, is_void=False).count()
    
    achievements = [
        {
            'id': 'first_paystub',
            'name': 'First Paystub',
            'description': 'Generate your first paystub',
            'icon': '🎉',
            'unlocked': paystub_count >= 1,
            'progress': min(paystub_count, 1),
            'target': 1
        },
        {
            'id': 'paystub_10',
            'name': '10 Paystubs',
            'description': 'Generate 10 paystubs',
            'icon': '📄',
            'unlocked': paystub_count >= 10,
            'progress': min(paystub_count, 10),
            'target': 10
        },
        {
            'id': 'paystub_25',
            'name': '25 Paystubs',
            'description': 'Generate 25 paystubs',
            'icon': '📚',
            'unlocked': paystub_count >= 25,
            'progress': min(paystub_count, 25),
            'target': 25
        },
        {
            'id': 'paystub_50',
            'name': '50 Paystubs',
            'description': 'Generate 50 paystubs',
            'icon': '🏆',
            'unlocked': paystub_count >= 50,
            'progress': min(paystub_count, 50),
            'target': 50
        },
        {
            'id': 'paystub_100',
            'name': '100 Paystubs',
            'description': 'Generate 100 paystubs',
            'icon': '💎',
            'unlocked': paystub_count >= 100,
            'progress': min(paystub_count, 100),
            'target': 100
        },
        {
            'id': 'silver_tier',
            'name': 'Silver Tier',
            'description': 'Reach Silver reward tier (500 points)',
            'icon': '🥈',
            'unlocked': user.reward_points >= 500,
            'progress': min(user.reward_points, 500),
            'target': 500
        },
        {
            'id': 'gold_tier',
            'name': 'Gold Tier',
            'description': 'Reach Gold reward tier (1000 points)',
            'icon': '🥇',
            'unlocked': user.reward_points >= 1000,
            'progress': min(user.reward_points, 1000),
            'target': 1000
        },
        {
            'id': 'platinum_tier',
            'name': 'Platinum Tier',
            'description': 'Reach Platinum reward tier (1500 points)',
            'icon': '💠',
            'unlocked': user.reward_points >= 1500,
            'progress': min(user.reward_points, 1500),
            'target': 1500
        },
        {
            'id': 'login_streak_7',
            'name': 'Week Warrior',
            'description': 'Login for 7 consecutive days',
            'icon': '🔥',
            'unlocked': user.login_streak >= 7,
            'progress': min(user.login_streak, 7),
            'target': 7
        },
        {
            'id': 'login_streak_30',
            'name': 'Monthly Master',
            'description': 'Login for 30 consecutive days',
            'icon': '⚡',
            'unlocked': user.login_streak >= 30,
            'progress': min(user.login_streak, 30),
            'target': 30
        }
    ]
    
    return achievements


def get_tier_benefits(tier):
    """Get the benefits for a specific reward tier"""
    benefits = {
        'bronze': [
            'Basic paystub generation',
            'Standard support',
            'Email notifications'
        ],
        'silver': [
            'All Bronze benefits',
            'Priority support',
            '5% discount on upgrades',
            'Early access to new features'
        ],
        'gold': [
            'All Silver benefits',
            'Dedicated account manager',
            '10% discount on upgrades',
            'Custom branding options',
            'API access'
        ],
        'platinum': [
            'All Gold benefits',
            'VIP support (24/7)',
            '15% discount on upgrades',
            'White-label options',
            'Custom integrations',
            'Priority feature requests'
        ]
    }
    
    return benefits.get(tier, benefits['bronze'])

