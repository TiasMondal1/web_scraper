"""
Usage limits and quotas checking
"""
from sqlalchemy.orm import Session
from app.models import User, Subscription, SubscriptionPlan, UsageStats, UserProduct
from datetime import date
from fastapi import HTTPException, status


def get_user_plan(db: Session, user_id: int) -> SubscriptionPlan:
    """Get user's current subscription plan"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active subscription found"
        )
    
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()
    
    return plan


def check_product_limit(db: Session, user_id: int) -> bool:
    """Check if user has reached product tracking limit"""
    plan = get_user_plan(db, user_id)
    
    current_count = db.query(UserProduct).filter(
        UserProduct.user_id == user_id,
        UserProduct.is_active == True
    ).count()
    
    return current_count < plan.max_products


def check_daily_limit(db: Session, user_id: int, limit_type: str) -> bool:
    """
    Check daily usage limits
    limit_type: 'alerts', 'price_checks', 'api_calls'
    """
    plan = get_user_plan(db, user_id)
    
    # Get or create today's usage stats
    today = date.today()
    usage = db.query(UsageStats).filter(
        UsageStats.user_id == user_id,
        UsageStats.date == today
    ).first()
    
    if not usage:
        usage = UsageStats(user_id=user_id, date=today)
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    # Check limits based on type
    if limit_type == 'alerts':
        return usage.alerts_sent_count < plan.max_alerts_per_day
    elif limit_type == 'price_checks':
        return usage.price_checks_count < plan.max_price_checks_per_day
    elif limit_type == 'api_calls':
        return usage.api_calls_count < plan.max_api_calls_per_day
    
    return False


def increment_usage(db: Session, user_id: int, usage_type: str):
    """Increment usage counter"""
    today = date.today()
    usage = db.query(UsageStats).filter(
        UsageStats.user_id == user_id,
        UsageStats.date == today
    ).first()
    
    if not usage:
        usage = UsageStats(user_id=user_id, date=today)
        db.add(usage)
    
    if usage_type == 'alerts':
        usage.alerts_sent_count += 1
    elif usage_type == 'price_checks':
        usage.price_checks_count += 1
    elif usage_type == 'api_calls':
        usage.api_calls_count += 1
    
    db.commit()


def get_usage_stats(db: Session, user_id: int) -> dict:
    """Get current usage statistics"""
    plan = get_user_plan(db, user_id)
    
    today = date.today()
    usage = db.query(UsageStats).filter(
        UsageStats.user_id == user_id,
        UsageStats.date == today
    ).first()
    
    if not usage:
        usage = UsageStats(user_id=user_id, date=today)
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    tracked_products = db.query(UserProduct).filter(
        UserProduct.user_id == user_id,
        UserProduct.is_active == True
    ).count()
    
    return {
        'tracked_products': tracked_products,
        'tracked_products_limit': plan.max_products,
        'alerts_sent_today': usage.alerts_sent_count,
        'alerts_limit_per_day': plan.max_alerts_per_day,
        'price_checks_today': usage.price_checks_count,
        'price_checks_limit_per_day': plan.max_price_checks_per_day,
        'api_calls_today': usage.api_calls_count,
        'api_calls_limit_per_day': plan.max_api_calls_per_day
    }

