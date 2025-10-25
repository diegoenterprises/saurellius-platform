"""
Complete Rewards Calculation System
Implements gamification from deployment guide lines 3200-3400
"""
from decimal import Decimal
from datetime import datetime, timedelta
from src.models.user import db, User
from src.models.paystub import Paystub
from sqlalchemy import func, extract

class RewardsCalculator:
    """
    Calculate points, tiers, achievements, and milestones
    """
    
    # Tier Thresholds
    TIERS = {
        'Bronze': {'min': 0, 'max': 999, 'multiplier': Decimal('1.0')},
        'Silver': {'min': 1000, 'max': 4999, 'multiplier': Decimal('1.25')},
        'Gold': {'min': 5000, 'max': 14999, 'multiplier': Decimal('1.5')},
        'Platinum': {'min': 15000, 'max': None, 'multiplier': Decimal('2.0')}
    }
    
    # Points for Actions
    POINTS_FOR_ACTIONS = {
        'generate_paystub': 50,
        'first_paystub': 500,  # Bonus for first paystub
        'login': 5,
        'login_streak_7': 100,  # 7 day streak bonus
        'login_streak_30': 500,  # 30 day streak bonus
        'referral': 1000,
        'complete_profile': 200,
        'verify_email': 100,
        'add_employee': 25,
        'milestone_10_paystubs': 250,
        'milestone_50_paystubs': 1000,
        'milestone_100_paystubs': 2500,
        'milestone_500_paystubs': 10000
    }
    
    # Achievements
    ACHIEVEMENTS = [
        {
            'id': 'first_steps',
            'name': 'First Steps',
            'description': 'Generate your first paystub',
            'points': 500,
            'icon': 'fa-flag-checkered',
            'requirement': lambda user: user.total_paystubs >= 1
        },
        {
            'id': 'getting_started',
            'name': 'Getting Started',
            'description': 'Generate 10 paystubs',
            'points': 250,
            'icon': 'fa-rocket',
            'requirement': lambda user: user.total_paystubs >= 10
        },
        {
            'id': 'power_user',
            'name': 'Power User',
            'description': 'Generate 50 paystubs',
            'points': 1000,
            'icon': 'fa-fire',
            'requirement': lambda user: user.total_paystubs >= 50
        },
        {
            'id': 'master',
            'name': 'Paystub Master',
            'description': 'Generate 100 paystubs',
            'points': 2500,
            'icon': 'fa-crown',
            'requirement': lambda user: user.total_paystubs >= 100
        },
        {
            'id': 'legend',
            'name': 'Legend',
            'description': 'Generate 500 paystubs',
            'points': 10000,
            'icon': 'fa-trophy',
            'requirement': lambda user: user.total_paystubs >= 500
        },
        {
            'id': 'team_builder',
            'name': 'Team Builder',
            'description': 'Add 5 employees',
            'points': 200,
            'icon': 'fa-users',
            'requirement': lambda user: user.total_employees >= 5
        },
        {
            'id': 'early_adopter',
            'name': 'Early Adopter',
            'description': 'Join in the first month',
            'points': 1000,
            'icon': 'fa-star',
            'requirement': lambda user: (datetime.utcnow() - user.created_at).days <= 30
        },
        {
            'id': 'consistent',
            'name': 'Consistent',
            'description': '7 day login streak',
            'points': 100,
            'icon': 'fa-calendar-check',
            'requirement': lambda user: user.login_streak >= 7
        },
        {
            'id': 'dedicated',
            'name': 'Dedicated',
            'description': '30 day login streak',
            'points': 500,
            'icon': 'fa-medal',
            'requirement': lambda user: user.login_streak >= 30
        }
    ]
    
    @staticmethod
    def get_tier(total_points):
        """
        Determine user tier based on total points
        """
        for tier_name, tier_data in RewardsCalculator.TIERS.items():
            if tier_data['max'] is None:
                if total_points >= tier_data['min']:
                    return tier_name
            elif tier_data['min'] <= total_points <= tier_data['max']:
                return tier_name
        return 'Bronze'
    
    @staticmethod
    def get_tier_progress(total_points):
        """
        Calculate progress to next tier
        """
        current_tier = RewardsCalculator.get_tier(total_points)
        
        # Find next tier
        tier_order = ['Bronze', 'Silver', 'Gold', 'Platinum']
        current_index = tier_order.index(current_tier)
        
        if current_index >= len(tier_order) - 1:
            # Already at max tier
            return {
                'current_tier': current_tier,
                'next_tier': None,
                'progress_percent': 100,
                'points_to_next': 0,
                'current_points': total_points
            }
        
        next_tier = tier_order[current_index + 1]
        next_tier_min = RewardsCalculator.TIERS[next_tier]['min']
        current_tier_min = RewardsCalculator.TIERS[current_tier]['min']
        
        points_in_tier = total_points - current_tier_min
        points_needed = next_tier_min - current_tier_min
        progress_percent = int((points_in_tier / points_needed) * 100)
        points_to_next = next_tier_min - total_points
        
        return {
            'current_tier': current_tier,
            'next_tier': next_tier,
            'progress_percent': progress_percent,
            'points_to_next': points_to_next,
            'current_points': total_points
        }
    
    @staticmethod
    def award_points(user_id, action, amount=None, description=None):
        """
        Award points to user for an action
        """
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get points for action
        if amount is None:
            amount = RewardsCalculator.POINTS_FOR_ACTIONS.get(action, 0)
        
        # Apply tier multiplier
        current_tier = RewardsCalculator.get_tier(user.total_lifetime_points)
        multiplier = RewardsCalculator.TIERS[current_tier]['multiplier']
        final_points = int(amount * multiplier)
        
        # Update user points
        user.reward_points = (user.reward_points or 0) + final_points
        user.total_lifetime_points = (user.total_lifetime_points or 0) + final_points
        
        # Update tier
        user.reward_tier = RewardsCalculator.get_tier(user.total_lifetime_points)
        
        # Create reward activity record (would be in RewardActivity model)
        # For now, just update user
        
        db.session.commit()
        
        return {
            'points_awarded': final_points,
            'base_points': amount,
            'multiplier': float(multiplier),
            'new_total': user.reward_points,
            'new_tier': user.reward_tier
        }
    
    @staticmethod
    def check_achievements(user_id):
        """
        Check and award achievements for user
        """
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Get user stats
        user.total_paystubs = Paystub.query.filter_by(
            user_id=user_id,
            is_void=False
        ).count()
        
        # Check each achievement
        earned_achievements = []
        for achievement in RewardsCalculator.ACHIEVEMENTS:
            # Check if already earned (would check RewardActivity table)
            # For now, check if requirement is met
            if achievement['requirement'](user):
                earned_achievements.append({
                    'id': achievement['id'],
                    'name': achievement['name'],
                    'description': achievement['description'],
                    'points': achievement['points'],
                    'icon': achievement['icon']
                })
        
        return earned_achievements
    
    @staticmethod
    def check_milestones(user_id):
        """
        Check if user has reached any milestones
        """
        user = User.query.get(user_id)
        if not user:
            return []
        
        paystub_count = Paystub.query.filter_by(
            user_id=user_id,
            is_void=False
        ).count()
        
        milestones = []
        milestone_thresholds = [10, 50, 100, 500, 1000]
        
        for threshold in milestone_thresholds:
            if paystub_count >= threshold:
                action_key = f'milestone_{threshold}_paystubs'
                milestones.append({
                    'threshold': threshold,
                    'points': RewardsCalculator.POINTS_FOR_ACTIONS.get(action_key, 0),
                    'description': f'Generated {threshold} paystubs'
                })
        
        return milestones
    
    @staticmethod
    def calculate_login_streak(user_id):
        """
        Calculate consecutive login streak
        """
        user = User.query.get(user_id)
        if not user:
            return 0
        
        # This would check login history table
        # For now, return stored streak
        return user.login_streak or 0
    
    @staticmethod
    def update_login_streak(user_id):
        """
        Update login streak and award points if applicable
        """
        user = User.query.get(user_id)
        if not user:
            return None
        
        today = datetime.utcnow().date()
        
        # Check last login
        if user.last_login_date:
            days_since_login = (today - user.last_login_date).days
            
            if days_since_login == 1:
                # Consecutive day - increment streak
                user.login_streak = (user.login_streak or 0) + 1
            elif days_since_login > 1:
                # Streak broken - reset
                user.login_streak = 1
            # else: same day, no change
        else:
            # First login
            user.login_streak = 1
        
        user.last_login_date = today
        
        # Award streak bonuses
        if user.login_streak == 7:
            RewardsCalculator.award_points(user_id, 'login_streak_7')
        elif user.login_streak == 30:
            RewardsCalculator.award_points(user_id, 'login_streak_30')
        
        # Award daily login points
        RewardsCalculator.award_points(user_id, 'login')
        
        db.session.commit()
        
        return {
            'login_streak': user.login_streak,
            'points_awarded': True
        }
    
    @staticmethod
    def get_rewards_summary(user_id):
        """
        Get complete rewards summary for dashboard
        """
        user = User.query.get(user_id)
        if not user:
            return None
        
        tier_progress = RewardsCalculator.get_tier_progress(user.total_lifetime_points or 0)
        achievements = RewardsCalculator.check_achievements(user_id)
        milestones = RewardsCalculator.check_milestones(user_id)
        
        return {
            'current_points': user.reward_points or 0,
            'lifetime_points': user.total_lifetime_points or 0,
            'tier': tier_progress['current_tier'],
            'tier_progress': tier_progress,
            'achievements': achievements,
            'achievements_count': len(achievements),
            'milestones': milestones,
            'login_streak': user.login_streak or 0
        }

