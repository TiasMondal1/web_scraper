"""
Admin panel endpoints
Requires admin role/privileges
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from app.database import get_db
from app.models import (
    User, Subscription, SubscriptionPlan, Product, UserProduct, 
    Alert, PaymentTransaction, UsageStats
)
from app.auth import get_current_user
from app.schemas import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify user has admin privileges
    In production, check user.role == 'admin' or similar
    """
    # TODO: Add proper admin role checking
    # For now, checking if user is verified and has been around
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access denied"
        )
    
    # You should add a 'role' field to User model and check it here
    # if current_user.role != 'admin':
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    return current_user


# ============================================
# Dashboard Analytics
# ============================================

@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Get overall platform statistics for admin dashboard
    """
    # Total users
    total_users = db.query(User).count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    
    # Active subscriptions
    active_subscriptions = db.query(Subscription).filter(
        Subscription.status == "active"
    ).count()
    
    # Revenue (this month)
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.query(func.sum(PaymentTransaction.amount)).filter(
        PaymentTransaction.status == "completed",
        PaymentTransaction.created_at >= first_day_of_month
    ).scalar() or Decimal(0)
    
    # Total revenue (all time)
    total_revenue = db.query(func.sum(PaymentTransaction.amount)).filter(
        PaymentTransaction.status == "completed"
    ).scalar() or Decimal(0)
    
    # Products tracked
    total_products = db.query(Product).count()
    active_tracking = db.query(UserProduct).filter(
        UserProduct.is_active == True
    ).count()
    
    # Alerts sent (today)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = db.query(Alert).filter(
        Alert.created_at >= today
    ).count()
    
    # New users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = db.query(User).filter(
        User.created_at >= week_ago
    ).count()
    
    # MRR (Monthly Recurring Revenue)
    monthly_subscriptions = db.query(Subscription).filter(
        Subscription.status == "active",
        Subscription.billing_cycle == "monthly"
    ).all()
    
    yearly_subscriptions = db.query(Subscription).filter(
        Subscription.status == "active",
        Subscription.billing_cycle == "yearly"
    ).all()
    
    mrr = sum(float(sub.amount) for sub in monthly_subscriptions)
    mrr += sum(float(sub.amount) / 12 for sub in yearly_subscriptions)  # Normalize yearly to monthly
    
    return {
        "users": {
            "total": total_users,
            "verified": verified_users,
            "new_this_week": new_users_week
        },
        "subscriptions": {
            "active": active_subscriptions,
            "mrr": round(mrr, 2)
        },
        "revenue": {
            "this_month": float(monthly_revenue),
            "total": float(total_revenue)
        },
        "products": {
            "total": total_products,
            "active_tracking": active_tracking
        },
        "alerts": {
            "today": alerts_today
        }
    }


@router.get("/dashboard/revenue-chart")
async def get_revenue_chart(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Get monthly revenue data for charts
    """
    revenue_data = []
    
    for i in range(months):
        if i == 0:
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_date = start_date - timedelta(days=1)
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_revenue = db.query(func.sum(PaymentTransaction.amount)).filter(
            PaymentTransaction.status == "completed",
            PaymentTransaction.created_at >= start_date,
            PaymentTransaction.created_at <= end_date
        ).scalar() or Decimal(0)
        
        revenue_data.insert(0, {
            "month": start_date.strftime("%B %Y"),
            "revenue": float(month_revenue)
        })
    
    return {"revenue_data": revenue_data}


# ============================================
# User Management
# ============================================

@router.get("/users")
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    List all users with pagination and filtering
    """
    query = db.query(User)
    
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) | 
            (User.full_name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    user_list = []
    for user in users:
        # Get subscription info
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        plan_name = "Free"
        if subscription:
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            plan_name = plan.display_name if plan else "Unknown"
        
        # Get usage stats
        products_tracked = db.query(UserProduct).filter(
            UserProduct.user_id == user.id,
            UserProduct.is_active == True
        ).count()
        
        user_list.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "email_verified": user.email_verified,
            "status": user.status,
            "plan": plan_name,
            "products_tracked": products_tracked,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at
        })
    
    return {
        "total": total,
        "users": user_list,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Get detailed user information
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    subscription_info = None
    if subscription:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subscription.plan_id
        ).first()
        subscription_info = {
            "plan": plan.display_name if plan else "Unknown",
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "amount": float(subscription.amount),
            "current_period_end": subscription.current_period_end
        }
    
    # Get tracked products
    products = db.query(UserProduct).filter(
        UserProduct.user_id == user.id,
        UserProduct.is_active == True
    ).count()
    
    # Get alerts
    alerts = db.query(Alert).filter(
        Alert.user_id == user.id
    ).order_by(desc(Alert.created_at)).limit(10).all()
    
    # Get payment history
    payments = db.query(PaymentTransaction).filter(
        PaymentTransaction.user_id == user.id
    ).order_by(desc(PaymentTransaction.created_at)).limit(10).all()
    
    payment_history = [{
        "id": p.id,
        "amount": float(p.amount),
        "status": p.status,
        "created_at": p.created_at
    } for p in payments]
    
    alert_history = [{
        "id": a.id,
        "type": a.alert_type,
        "price_difference": float(a.price_difference) if a.price_difference else None,
        "status": a.status,
        "created_at": a.created_at
    } for a in alerts]
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "email_verified": user.email_verified,
            "status": user.status,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "login_count": user.login_count
        },
        "subscription": subscription_info,
        "stats": {
            "products_tracked": products,
            "total_alerts": len(alerts),
            "total_payments": len(payments)
        },
        "recent_alerts": alert_history,
        "payment_history": payment_history
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Update user status (active, suspended, deleted)
    """
    if new_status not in ["active", "suspended", "deleted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be: active, suspended, or deleted"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.status = new_status
    db.commit()
    
    return {
        "message": f"User status updated to {new_status}",
        "user_id": user_id,
        "new_status": new_status
    }


# ============================================
# Subscription Management
# ============================================

@router.get("/subscriptions")
async def list_subscriptions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: Optional[str] = None,
    plan_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    List all subscriptions with filtering
    """
    query = db.query(Subscription)
    
    if status_filter:
        query = query.filter(Subscription.status == status_filter)
    
    if plan_filter:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == plan_filter
        ).first()
        if plan:
            query = query.filter(Subscription.plan_id == plan.id)
    
    total = query.count()
    subscriptions = query.order_by(desc(Subscription.created_at)).offset(skip).limit(limit).all()
    
    subscription_list = []
    for sub in subscriptions:
        user = db.query(User).filter(User.id == sub.user_id).first()
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
        
        subscription_list.append({
            "id": sub.id,
            "user_email": user.email if user else "Unknown",
            "user_id": sub.user_id,
            "plan": plan.display_name if plan else "Unknown",
            "status": sub.status,
            "billing_cycle": sub.billing_cycle,
            "amount": float(sub.amount),
            "current_period_end": sub.current_period_end,
            "created_at": sub.created_at
        })
    
    return {
        "total": total,
        "subscriptions": subscription_list,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }


@router.post("/subscriptions/{subscription_id}/cancel")
async def admin_cancel_subscription(
    subscription_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Admin cancel a user's subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    subscription.cancellation_reason = reason or "Cancelled by admin"
    db.commit()
    
    return {
        "message": "Subscription cancelled",
        "subscription_id": subscription_id
    }


# ============================================
# Product Management
# ============================================

@router.get("/products")
async def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    List all products in the system
    """
    query = db.query(Product)
    
    if platform:
        query = query.filter(Product.platform == platform)
    
    total = query.count()
    products = query.order_by(desc(Product.last_scraped_at)).offset(skip).limit(limit).all()
    
    product_list = []
    for product in products:
        tracking_count = db.query(UserProduct).filter(
            UserProduct.product_id == product.id,
            UserProduct.is_active == True
        ).count()
        
        product_list.append({
            "id": product.id,
            "name": product.name,
            "platform": product.platform,
            "current_price": float(product.current_price) if product.current_price else None,
            "in_stock": product.in_stock,
            "tracking_count": tracking_count,
            "last_scraped_at": product.last_scraped_at,
            "created_at": product.created_at
        })
    
    return {
        "total": total,
        "products": product_list,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }


# ============================================
# System Health
# ============================================

@router.get("/system/health")
async def system_health(
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    """
    Check system health and status
    """
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Celery (Redis)
    celery_status = "unknown"
    try:
        from app.tasks import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            celery_status = "healthy"
        else:
            celery_status = "no workers"
    except Exception as e:
        celery_status = f"unhealthy: {str(e)}"
    
    # Get recent errors/alerts
    recent_failed_alerts = db.query(Alert).filter(
        Alert.status == "failed"
    ).order_by(desc(Alert.created_at)).limit(10).count()
    
    return {
        "database": db_status,
        "celery": celery_status,
        "recent_failed_alerts": recent_failed_alerts,
        "timestamp": datetime.utcnow()
    }
