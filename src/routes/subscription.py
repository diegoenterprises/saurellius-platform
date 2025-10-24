from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User, Subscription
from src.routes.auth import token_required
import stripe
import os

subscription_bp = Blueprint('subscription', __name__)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
DOMAIN = os.environ.get("DOMAIN", "http://localhost:5000")

@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    plans = Subscription.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "paystubs_per_month": p.paystubs_per_month,
            "stripe_plan_id": p.stripe_plan_id
        } for p in plans
    ]), 200

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@token_required
def create_checkout_session(current_user):
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    plan = Subscription.query.get(plan_id)
    if not plan:
        return jsonify({'message': 'Invalid plan ID'}), 404

    try:
        # Create a Stripe Customer if one doesn't exist
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.username,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create a Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(plan.price * 100),
                        'product_data': {
                            'name': plan.name,
                        },
                        'recurring': {'interval': 'month'},
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=DOMAIN + '/cancel',
            metadata={'plan_id': plan.id, 'user_id': current_user.id}
        )
        
        return jsonify({'sessionId': checkout_session.id}), 200
    except Exception as e:
        print(f"Stripe Error: {e}")
        return jsonify(error=str(e)), 403

@subscription_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    
    # Replace with your actual webhook secret
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        
        user = User.query.get(user_id)
        plan = Subscription.query.get(plan_id)
        
        if user and plan:
            user.subscription_id = plan.id
            user.is_active_subscriber = True
            db.session.commit()
            # Optionally, create a subscription record in your DB if needed
            
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.is_active_subscriber = False
            user.subscription_id = None
            db.session.commit()

    return jsonify({'status': 'success'}), 200

@subscription_bp.route('/billing-portal', methods=['POST'])
@token_required
def create_billing_portal_session(current_user):
    if not current_user.stripe_customer_id:
        return jsonify({'message': 'User has no Stripe customer ID'}), 400

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=DOMAIN + '/dashboard',
        )
        return jsonify({'url': session.url}), 200
    except Exception as e:
        return jsonify(error=str(e)), 403
