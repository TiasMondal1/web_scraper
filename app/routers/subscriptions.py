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

