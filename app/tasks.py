"""
Celery background tasks for price tracking and alerts
"""
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from app.database import get_db
from app.models import UserProduct, Product, PriceHistory, Alert, User, Subscription, SubscriptionPlan
from app.utils.scraper import scrape_product_price, get_platform_from_url
from app.utils.limits import get_user_plan_limits
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "price_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
)


@celery_app.task(name="scrape_all_products")
def scrape_all_products_task():
    """
    Scrape prices for all active user products
    Runs daily or on schedule
    """
    db = next(get_db())
    try:
        # Get all active user products
        user_products = db.query(UserProduct).filter(
            UserProduct.is_active == True
        ).all()
        
        total_products = len(user_products)
        successful = 0
        failed = 0
        
        logger.info(f"Starting price scrape for {total_products} products")
        
        for user_product in user_products:
            try:
                # Get product details
                product = db.query(Product).filter(
                    Product.id == user_product.product_id
                ).first()
                
                if not product:
                    continue
                
                # Check user's plan limits
                user = db.query(User).filter(User.id == user_product.user_id).first()
                subscription = db.query(Subscription).filter(
                    Subscription.user_id == user.id,
                    Subscription.status == "active"
                ).first()
                
                if subscription:
                    plan = db.query(SubscriptionPlan).filter(
                        SubscriptionPlan.id == subscription.plan_id
                    ).first()
                    limits = get_user_plan_limits(db, user.id)
                    
                    # Check if user has exceeded daily price checks
                    if limits['price_checks_today'] >= limits['price_checks_limit_per_day']:
                        logger.warning(f"User {user.id} exceeded daily price check limit")
                        continue
                
                # Scrape price
                price_data = scrape_product_price(product.url)
                
                if price_data and price_data.get('price'):
                    # Get previous price
                    previous_price_record = db.query(PriceHistory).filter(
                        PriceHistory.product_id == product.id
                    ).order_by(PriceHistory.scraped_at.desc()).first()
                    
                    previous_price = previous_price_record.price if previous_price_record else None
                    current_price = Decimal(str(price_data['price']))
                    
                    # Create price history record
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=current_price,
                        currency=price_data.get('currency', 'INR'),
                        in_stock=price_data.get('in_stock', True),
                        discount_percent=price_data.get('discount_percent'),
                        original_price=price_data.get('original_price'),
                        scraped_at=datetime.utcnow()
                    )
                    db.add(price_history)
                    
                    # Update product current price
                    product.current_price = current_price
                    product.in_stock = price_data.get('in_stock', True)
                    product.last_scraped_at = datetime.utcnow()
                    
                    # Check for price drops and create alerts
                    if previous_price and current_price < previous_price:
                        price_difference = previous_price - current_price
                        price_difference_percent = (price_difference / previous_price) * 100
                        
                        # Check if alert should be sent
                        should_alert = False
                        if user_product.alert_enabled:
                            # Check if price dropped below target
                            if user_product.target_price and current_price <= user_product.target_price:
                                should_alert = True
                            # Or if price dropped significantly (5% or more)
                            elif price_difference_percent >= 5:
                                should_alert = True
                        
                        if should_alert:
                            # Create alert
                            alert = Alert(
                                user_id=user_product.user_id,
                                user_product_id=user_product.id,
                                product_id=product.id,
                                alert_type="price_drop",
                                old_price=previous_price,
                                new_price=current_price,
                                price_difference=price_difference,
                                price_difference_percent=price_difference_percent,
                                status="pending"
                            )
                            db.add(alert)
                            
                            # Trigger alert sending task
                            send_price_alert_task.delay(alert.id)
                    
                    db.commit()
                    successful += 1
                else:
                    failed += 1
                    logger.warning(f"Failed to scrape price for product {product.id}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error scraping product {user_product.product_id}: {str(e)}")
                db.rollback()
                continue
        
        logger.info(f"Price scrape completed: {successful} successful, {failed} failed")
        return {
            "total": total_products,
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Error in scrape_all_products_task: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(name="send_price_alert")
def send_price_alert_task(alert_id: int):
    """
    Send price alert notification to user
    """
    db = next(get_db())
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert or alert.status != "pending":
            return
        
        user = db.query(User).filter(User.id == alert.user_id).first()
        user_product = db.query(UserProduct).filter(
            UserProduct.id == alert.user_product_id
        ).first()
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        
        if not user or not product:
            return
        
        # Send email alert if enabled
        if user_product.email_notification:
            try:
                from app.utils.email import send_price_alert_email
                send_price_alert_email(
                    user.email,
                    product.name,
                    alert.old_price,
                    alert.new_price,
                    alert.price_difference,
                    alert.price_difference_percent,
                    product.url
                )
                alert.email_sent = True
            except Exception as e:
                logger.error(f"Failed to send email alert: {str(e)}")
        
        # Update alert status
        alert.status = "sent"
        alert.sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Price alert sent for alert {alert_id}")
        
    except Exception as e:
        logger.error(f"Error sending price alert {alert_id}: {str(e)}")
        if alert:
            alert.status = "failed"
            db.commit()
    finally:
        db.close()


@celery_app.task(name="send_all_pending_alerts")
def send_all_pending_alerts_task():
    """
    Send all pending alerts
    Runs periodically to process queued alerts
    """
    db = next(get_db())
    try:
        pending_alerts = db.query(Alert).filter(
            Alert.status == "pending"
        ).limit(100).all()  # Process 100 at a time
        
        for alert in pending_alerts:
            send_price_alert_task.delay(alert.id)
        
        return {"processed": len(pending_alerts)}
        
    except Exception as e:
        logger.error(f"Error in send_all_pending_alerts_task: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(name="cleanup_old_data")
def cleanup_old_data_task(days_to_keep: int = 365):
    """
    Clean up old price history data beyond retention period
    """
    db = next(get_db())
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Get all users and their plan retention periods
        subscriptions = db.query(Subscription).filter(
            Subscription.status == "active"
        ).all()
        
        deleted_count = 0
        
        for subscription in subscriptions:
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            
            if plan:
                # Use plan's retention period
                plan_cutoff = datetime.utcnow() - timedelta(days=plan.historical_data_days)
                
                # Get user's products
                user_products = db.query(UserProduct).filter(
                    UserProduct.user_id == subscription.user_id,
                    UserProduct.is_active == True
                ).all()
                
                for user_product in user_products:
                    # Delete old price history
                    deleted = db.query(PriceHistory).filter(
                        PriceHistory.product_id == user_product.product_id,
                        PriceHistory.scraped_at < plan_cutoff
                    ).delete()
                    deleted_count += deleted
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old price history records")
        
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_data_task: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="update_usage_stats")
def update_usage_stats_task():
    """
    Reset daily usage statistics for all users
    Runs daily at midnight
    """
    db = next(get_db())
    try:
        from app.models import UsageStats
        
        # Get all active users
        users = db.query(User).filter(User.status == "active").all()
        
        reset_count = 0
        
        for user in users:
            # Get or create usage stats for today
            today = datetime.utcnow().date()
            usage_stats = db.query(UsageStats).filter(
                UsageStats.user_id == user.id,
                UsageStats.date == today
            ).first()
            
            if not usage_stats:
                usage_stats = UsageStats(
                    user_id=user.id,
                    date=today
                )
                db.add(usage_stats)
            
            # Reset counters if it's a new day
            if usage_stats.last_reset.date() < today:
                usage_stats.tracked_products_count = db.query(UserProduct).filter(
                    UserProduct.user_id == user.id,
                    UserProduct.is_active == True
                ).count()
                usage_stats.alerts_sent_count = 0
                usage_stats.price_checks_count = 0
                usage_stats.api_calls_count = 0
                usage_stats.last_reset = datetime.utcnow()
                reset_count += 1
        
        db.commit()
        logger.info(f"Updated usage stats for {reset_count} users")
        
        return {"reset_count": reset_count}
        
    except Exception as e:
        logger.error(f"Error in update_usage_stats_task: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
