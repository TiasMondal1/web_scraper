"""
Dashboard and analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
from app.database import get_db
from app.models import User, UserProduct, Alert, Product, PriceHistory, Subscription, SubscriptionPlan
from app.schemas import DashboardStatsResponse, AlertResponse
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for current user
    """
    # Total products
    total_products = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).count()
    
    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.viewed == False
    ).count()
    
    # Price drops today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    price_drops_today = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.alert_type == "price_drop",
        Alert.created_at >= today
    ).count()
    
    # Calculate savings this month
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    alerts_this_month = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.alert_type == "price_drop",
        Alert.created_at >= first_day_of_month
    ).all()
    
    total_savings = Decimal(0)
    for alert in alerts_this_month:
        if alert.price_difference:
            total_savings += alert.price_difference
    
    # Current subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if subscription:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subscription.plan_id
        ).first()
        plan_name = plan.display_name if plan else "Free"
        expires = subscription.current_period_end
    else:
        # Default to free plan if no subscription
        plan_name = "Free"
        expires = datetime.utcnow() + timedelta(days=365)
    
    return DashboardStatsResponse(
        total_products=total_products,
        active_alerts=active_alerts,
        price_drops_today=price_drops_today,
        savings_this_month=total_savings,
        subscription_plan=plan_name,
        subscription_expires=expires
    )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_recent_alerts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent alerts for current user
    """
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).limit(limit).all()
    
    return alerts


@router.post("/alerts/{alert_id}/mark-viewed")
async def mark_alert_viewed(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an alert as viewed
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.viewed = True
    alert.viewed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Alert marked as viewed"}


@router.get("/savings/monthly")
async def get_monthly_savings(
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get savings breakdown by month
    """
    savings_data = []
    
    for i in range(months):
        # Calculate start and end of month
        if i == 0:
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_date = start_date - timedelta(days=1)
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get alerts for this month
        alerts = db.query(Alert).filter(
            Alert.user_id == current_user.id,
            Alert.alert_type == "price_drop",
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        ).all()
        
        month_savings = sum(
            float(alert.price_difference) for alert in alerts 
            if alert.price_difference
        )
        
        savings_data.append({
            "month": start_date.strftime("%B %Y"),
            "savings": month_savings,
            "alerts_count": len(alerts)
        })
    
    return {"monthly_savings": savings_data}


@router.get("/top-deals")
async def get_top_deals(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top price drop deals
    """
    # Get recent alerts with biggest price drops
    top_alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.alert_type == "price_drop"
    ).order_by(Alert.price_difference_percent.desc()).limit(limit).all()
    
    deals = []
    for alert in top_alerts:
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        deals.append({
            "product_name": product.name,
            "old_price": float(alert.old_price),
            "new_price": float(alert.new_price),
            "savings": float(alert.price_difference),
            "discount_percent": float(alert.price_difference_percent),
            "date": alert.created_at,
            "product_url": product.url
        })
    
    return {"top_deals": deals}

