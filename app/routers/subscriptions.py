"""
Subscription management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import User, Subscription, SubscriptionPlan
from app.schemas import SubscriptionPlanResponse, SubscriptionResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(get_db)):
    """
    Get all available subscription plans
    Public endpoint - no authentication required
    """
    plans = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.is_active == True
    ).order_by(SubscriptionPlan.price_monthly.asc()).all()
    
    return plans


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's active subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return subscription


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel current subscription
    - Subscription remains active until end of billing period
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Don't immediately deactivate, let it run until period end
    subscription.cancelled_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Subscription cancelled",
        "active_until": subscription.current_period_end
    }


@router.get("/usage", response_model=dict)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current usage statistics
    """
    from app.utils.limits import get_usage_stats
    
    stats = get_usage_stats(db, current_user.id)
    return stats


@router.post("/upgrade")
async def upgrade_subscription(
    plan_id: int,
    billing_cycle: str = "monthly",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upgrade or change subscription plan
    Note: This endpoint prepares for payment. Actual upgrade happens after payment verification.
    """
    # Get target plan
    target_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()
    
    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Get current subscription
    current_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if current_subscription:
        current_plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == current_subscription.plan_id
        ).first()
        
        # Check if it's actually an upgrade
        if target_plan.price_monthly <= current_plan.price_monthly:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This is not an upgrade. Use /downgrade for lower plans."
            )
    
    # Return payment information (frontend will call /api/payments/create-order)
    return {
        "message": "Please complete payment to upgrade",
        "plan_id": plan_id,
        "plan_name": target_plan.display_name,
        "billing_cycle": billing_cycle,
        "next_step": "Call /api/payments/create-order with this plan_id"
    }


@router.post("/downgrade")
async def downgrade_subscription(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downgrade subscription plan
    - Downgrade takes effect at end of current billing period
    """
    # Get target plan
    target_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()
    
    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Get current subscription
    current_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not current_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    current_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == current_subscription.plan_id
    ).first()
    
    # Check if it's actually a downgrade
    if target_plan.price_monthly >= current_plan.price_monthly:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not a downgrade. Use /upgrade for higher plans."
        )
    
    # For downgrade, we'll cancel current and let user subscribe to new plan
    # In production, you might want to schedule this for end of period
    # For now, we'll just cancel and user can subscribe to new plan
    current_subscription.cancelled_at = datetime.utcnow()
    current_subscription.cancellation_reason = f"Downgrading to {target_plan.display_name}"
    db.commit()
    
    return {
        "message": "Current subscription cancelled. You can now subscribe to the new plan.",
        "current_plan": current_plan.display_name,
        "new_plan": target_plan.display_name,
        "note": "Subscribe to new plan via /api/payments/create-order"
    }