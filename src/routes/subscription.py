"""
Subscription Management Routes with Stripe Integration
Handles subscription plans, upgrades, downgrades, and billing
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.database import User, Subscription, db
from src.routes.auth import token_required
import stripe
import os

subscription_bp = Blueprint('subscription', __name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')


@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = Subscription.query.all()
        return jsonify({
            'plans': [plan.to_dict() for plan in plans]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/current', methods=['GET'])
@token_required
def get_current_subscription(current_user):
    """Get current user's subscription details"""
    try:
        return jsonify({
            'subscription': {
                'tier': current_user.subscription_tier,
                'status': current_user.subscription_status,
                'start_date': current_user.subscription_start_date.isoformat() if current_user.subscription_start_date else None,
                'end_date': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
                'stripe_customer_id': current_user.stripe_customer_id,
                'stripe_subscription_id': current_user.stripe_subscription_id
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/upgrade', methods=['POST'])
@token_required
def upgrade_subscription(current_user):
    """
    Upgrade to a new subscription tier
    
    Expected JSON:
    {
        "plan_name": "professional",
        "billing_cycle": "monthly"  # monthly or annual
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'plan_name' not in data:
            return jsonify({'error': 'Missing plan_name'}), 400
        
        plan_name = data['plan_name']
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # Get the plan
        plan = Subscription.query.filter_by(name=plan_name).first()
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Create or update Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create subscription
        if billing_cycle == 'annual' and plan.stripe_price_id_annual:
            price_id = plan.stripe_price_id_annual
        else:
            price_id = plan.stripe_price_id_monthly
        
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{'price': price_id}],
            metadata={'user_id': current_user.id, 'plan': plan_name}
        )
        
        # Update user subscription
        current_user.subscription_tier = plan_name
        current_user.subscription_status = 'active'
        current_user.subscription_start_date = datetime.utcnow()
        current_user.stripe_subscription_id = subscription.id
        
        # Set end date based on billing cycle
        if billing_cycle == 'annual':
            current_user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
        else:
            current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully upgraded to {plan_name}',
            'subscription': {
                'tier': current_user.subscription_tier,
                'status': current_user.subscription_status,
                'stripe_subscription_id': subscription.id
            }
        }), 200
        
    except stripe.error.CardError as e:
        return jsonify({'error': f'Card error: {e.user_message}'}), 400
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_subscription(current_user):
    """Cancel current subscription"""
    try:
        if not current_user.stripe_subscription_id:
            return jsonify({'error': 'No active subscription'}), 400
        
        # Cancel Stripe subscription
        stripe.Subscription.delete(current_user.stripe_subscription_id)
        
        # Update user subscription
        current_user.subscription_status = 'cancelled'
        current_user.subscription_tier = 'starter'
        current_user.subscription_end_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled successfully'
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/billing-portal', methods=['POST'])
@token_required
def create_billing_portal(current_user):
    """Create Stripe billing portal session"""
    try:
        if not current_user.stripe_customer_id:
            return jsonify({'error': 'No Stripe customer found'}), 400
        
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url='https://saurellius.drpaystub.com/dashboard'
        )
        
        return jsonify({
            'url': session.url
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/webhook', methods=['POST'])
def handle_stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        # Handle subscription events
        if event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            user = User.query.filter_by(
                stripe_subscription_id=subscription['id']
            ).first()
            
            if user:
                user.subscription_status = 'active' if subscription['status'] == 'active' else subscription['status']
                db.session.commit()
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            user = User.query.filter_by(
                stripe_subscription_id=subscription['id']
            ).first()
            
            if user:
                user.subscription_status = 'cancelled'
                user.subscription_tier = 'starter'
                db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

