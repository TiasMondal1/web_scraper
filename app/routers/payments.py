"""
Razorpay payment integration
Handles subscription payments, verification, and webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import razorpay
import hmac
import hashlib
from typing import Optional
from app.database import get_db
from app.models import User, Subscription, SubscriptionPlan, PaymentTransaction
from app.schemas import CreatePaymentRequest, PaymentVerificationRequest
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@router.post("/create-order")
async def create_payment_order(
    payment_data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Razorpay order for subscription payment
    
    Flow:
    1. Get plan details
    2. Create Razorpay order
    3. Return order details to frontend
    4. Frontend shows Razorpay checkout
    5. User completes payment
    6. Frontend calls /verify-payment with response
    """
    # Get plan details
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == payment_data.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Calculate amount based on billing cycle
    if payment_data.billing_cycle == "yearly":
        amount = float(plan.price_yearly)
    else:
        amount = float(plan.price_monthly)
    
    if amount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create payment for free plan"
        )
    
    # Create Razorpay order
    try:
        order = razorpay_client.order.create({
            "amount": int(amount * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": current_user.id,
                "plan_id": plan.id,
                "billing_cycle": payment_data.billing_cycle
            }
        })
        
        return {
            "order_id": order['id'],
            "amount": amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
            "plan_name": plan.display_name,
            "user_email": current_user.email,
            "user_name": current_user.full_name or current_user.email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.post("/verify-payment")
async def verify_payment(
    verification_data: PaymentVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify Razorpay payment and activate subscription
    
    Called by frontend after successful payment with:
    - razorpay_order_id
    - razorpay_payment_id  
    - razorpay_signature
    """
    # Verify signature
    generated_signature = hmac.new(
        bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
        bytes(f"{verification_data.razorpay_order_id}|{verification_data.razorpay_payment_id}", 'utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if generated_signature != verification_data.razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Get plan
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == verification_data.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Fetch payment details from Razorpay
    try:
        payment = razorpay_client.payment.fetch(verification_data.razorpay_payment_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment details: {str(e)}"
        )
    
    # Determine billing cycle and amount from payment notes
    billing_cycle = payment.get('notes', {}).get('billing_cycle', 'monthly')
    amount = payment['amount'] / 100  # Convert from paise to rupees
    
    # Deactivate old subscriptions
    db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).update({"status": "cancelled", "cancelled_at": datetime.utcnow()})
    
    # Calculate subscription period
    start_date = datetime.utcnow()
    if billing_cycle == "yearly":
        end_date = start_date + timedelta(days=365)
    else:
        end_date = start_date + timedelta(days=30)
    
    # Create new subscription
    new_subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        billing_cycle=billing_cycle,
        amount=amount,
        payment_gateway="razorpay",
        gateway_subscription_id=verification_data.razorpay_payment_id,
        gateway_customer_id=payment.get('customer_id'),
        status="active",
        current_period_start=start_date,
        current_period_end=end_date
    )
    
    db.add(new_subscription)
    db.flush()
    
    # Record transaction
    transaction = PaymentTransaction(
        user_id=current_user.id,
        subscription_id=new_subscription.id,
        amount=amount,
        currency="INR",
        total_amount=amount,
        payment_gateway="razorpay",
        gateway_transaction_id=verification_data.razorpay_order_id,
        gateway_payment_id=verification_data.razorpay_payment_id,
        status="completed",
        payment_method=payment.get('method', 'unknown')
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(new_subscription)
    
    return {
        "message": "Payment verified and subscription activated",
        "subscription_id": new_subscription.id,
        "plan": plan.display_name,
        "valid_until": new_subscription.current_period_end
    }


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle Razorpay webhooks for automated events
    
    Events:
    - payment.authorized
    - payment.captured
    - payment.failed
    - subscription.charged
    - subscription.cancelled
    
    Configure webhook URL in Razorpay Dashboard:
    https://your-domain.com/api/payments/webhook
    """
    # Get request body
    body = await request.body()
    
    # Verify webhook signature
    expected_signature = hmac.new(
        bytes(settings.RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if x_razorpay_signature != expected_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse payload
    import json
    payload = json.loads(body)
    
    event = payload.get('event')
    payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
    
    # Handle different events
    if event == "payment.captured":
        # Payment successful - handled in verify-payment
        pass
    
    elif event == "payment.failed":
        # Payment failed
        payment_id = payment_entity.get('id')
        # TODO: Notify user about failed payment
        pass
    
    elif event == "subscription.charged":
        # Recurring payment successful
        subscription_entity = payload.get('payload', {}).get('subscription', {}).get('entity', {})
        # TODO: Extend subscription period
        pass
    
    elif event == "subscription.cancelled":
        # Subscription cancelled
        subscription_id = payload.get('payload', {}).get('subscription', {}).get('entity', {}).get('id')
        # TODO: Mark subscription as cancelled in DB
        pass
    
    return {"status": "ok"}


@router.get("/invoices")
async def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's payment history / invoices
    """
    transactions = db.query(PaymentTransaction).filter(
        PaymentTransaction.user_id == current_user.id
    ).order_by(PaymentTransaction.created_at.desc()).all()
    
    invoices = []
    for transaction in transactions:
        invoices.append({
            "id": transaction.id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status,
            "payment_method": transaction.payment_method,
            "date": transaction.created_at,
            "invoice_url": transaction.invoice_url
        })
    
    return {"invoices": invoices}

